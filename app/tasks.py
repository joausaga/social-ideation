from __future__ import absolute_import

from app.models import ConsultationPlatform, Initiative, Idea, Comment, SocialNetworkApp
from app.sync import save_sn_post, save_sn_comment, save_sn_vote, cud_initiative_votes, cud_initiative_ideas, \
                     cud_initiative_comments, invalidate_initiative_content, do_push_content, do_delete_content
from app.utils import convert_to_utf8_str
from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.cache import cache
from django.db.models import Q
from hashlib import md5

import traceback

logger = get_task_logger(__name__)


def _pull_content_social_network(social_network):
    connector = social_network.connector
    sn_class = connector.connector_class.title()
    sn_module = connector.connector_module.lower()
    sn = getattr(__import__(sn_module, fromlist=[sn_class]), sn_class)
    sn.authenticate(social_network)
    if social_network.page_id:
        posts = sn.get_posts(social_network.page_id)
        for post in posts:
            ret_data = save_sn_post(social_network, post)
            if ret_data:
                if 'comments_array' in post.keys():
                    for comment in post['comments_array']:
                        save_sn_comment(social_network, comment)
                        # Process comment's replies
                        if 'comments_array' in comment.keys():
                            for reply in comment['comments_array']:
                                save_sn_comment(social_network, reply)
                        # Process comment's votes
                        if 'votes_array' in comment.keys():
                            for vote in comment['votes_array']:
                                save_sn_vote(social_network, vote)
                # Save/Update votes
                if 'votes_array' in post.keys():
                    for vote in post['votes_array']:
                        save_sn_vote(social_network, vote)
    else:
        logger.warning('Cannot pull content from the social network {}. Reason: Page id not found'.
                       format(social_network.name))


def _pull_content_consultation_platform(platform, initiative):
    cud_initiative_ideas(platform, initiative)
    cud_initiative_comments(platform, initiative)
    cud_initiative_votes(platform, initiative)


def pull_data():
    # Pull data from consultation platforms
    for cplatform in ConsultationPlatform.objects.all():
        initiatives = Initiative.objects.filter(platform=cplatform)
        for initiative in initiatives:
            if initiative.active:
                logger.info('Pulling content of the initiative {} from the platform {}'.format(initiative,
                                                                                               cplatform))
                invalidate_initiative_content(source_consultation=cplatform, initiative=initiative)
                try:
                    _pull_content_consultation_platform(cplatform, initiative)
                except Exception as e:
                    logger.warning('Problem when trying to pull content of the initiative {} from platform {}. '
                                   'Message: {}'.
                                   format(initiative, cplatform, e))
                    logger.warning(traceback.format_exc())
    # Pull data from social networks that are not subscribe to receive real time notifications
    for socialnetwork in SocialNetworkApp.objects.all():
        if not socialnetwork.subscribed_read_time_updates:
            initiatives = Initiative.objects.filter(social_network=socialnetwork)
            for initiative in initiatives:
                if initiative.active:
                    invalidate_initiative_content(source_social=socialnetwork, initiative=initiative)
            logger.info('Pulling content posted on {}'.format(socialnetwork))
            try:
                _pull_content_social_network(socialnetwork)
            except Exception as e:
                logger.warning('Problem when trying to pull content posted on {}. Message: {}'.
                               format(socialnetwork, e))
                logger.warning(traceback.format_exc())


def push_data():
    batch_req_ideas = {}
    batch_req_comments = {}
    # Push ideas to consultation platforms and social networks
    logger.info('Pushing ideas to social networks and consultation platforms')
    existing_ideas = Idea.objects.exclude(exist=False).filter(Q(has_changed=True) | Q(is_new=True)).\
                     order_by('datetime')
    tot_ideas_to_sn = Idea.objects.exclude(exist=False).filter(Q(has_changed=True) | Q(is_new=True)).\
                      filter(source='consultation_platform').filter(is_new=True).count()
    count_ideas_to_sn = 0
    for idea in existing_ideas:
        try:
            if idea.initiative.active:
                if idea.source == 'social_network':
                    if not idea.source_social.subscribed_read_time_updates:
                        do_push_content(idea, 'idea')
                else:
                    if idea.is_new:  count_ideas_to_sn += 1
                    if count_ideas_to_sn == tot_ideas_to_sn:
                        batch_req_ideas = do_push_content(idea, 'idea', True, batch_req_ideas)
                    else:
                        batch_req_ideas = do_push_content(idea, 'idea', False, batch_req_ideas)
        except Exception as e:
            if idea.source == 'consultation_platform':
                logger.warning('Error when trying to publish the idea with the id={} on the social networks. '
                               'Message: {}'.format(idea.id, convert_to_utf8_str(e)))
            else:
                logger.warning('Error when trying to publish the idea with the id={} on the consultation platforms. '
                               'Message: {}'.format(idea.id, idea.source_social, convert_to_utf8_str(e)))
            logger.warning(traceback.format_exc())
    # Push comments to consultation platforms and social networks
    logger.info('Pushing comments to social networks and consultation platforms')
    existing_comments = Comment.objects.exclude(exist=False).filter(Q(has_changed=True) | Q(is_new=True)).\
                        order_by('datetime')
    tot_comments_to_sn = Comment.objects.exclude(exist=False).filter(Q(has_changed=True) | Q(is_new=True)).\
                         filter(source='consultation_platform').filter(is_new=True).count()
    count_comments_to_sn = 0
    for comment in existing_comments:
        try:
            if comment.initiative.active:
                if comment.source == 'social_network':
                    if not comment.source_social.subscribed_read_time_updates:
                        do_push_content(comment, 'comment')
                else:
                    if comment.is_new: count_comments_to_sn += 1
                    if count_comments_to_sn == tot_comments_to_sn:
                        batch_req_comments = do_push_content(comment, 'comment', True, batch_req_comments)
                    else:
                        batch_req_comments = do_push_content(comment, 'comment', False, batch_req_comments)
        except Exception as e:
            if comment.source == 'consultation_platform':
                logger.warning('Error when trying to publish the comment with the id={} on the social networks. '
                               'Message: {}'.format(comment.id, comment.source_consultation, convert_to_utf8_str(e)))
            else:
                logger.warning('Error when trying to publish the comment with the id={} on the consultation platforms. '
                               'Message: {}'.format(comment.id, comment.source_social, convert_to_utf8_str(e)))
            logger.warning(traceback.format_exc())


def delete_data():
    # Delete ideas that don't exist anymore in their original social networks or consultation platforms
    logger.info('Checking whether exists ideas that do not exist anymore')
    unexisting_ideas = Idea.objects.exclude(exist=True).exclude(Q(cp_id=None) | Q(sn_id=None))
    for idea in unexisting_ideas:
        try:
            if idea.initiative.active:
                if idea.source == 'social_network':
                    if not idea.source_social.subscribed_read_time_updates:
                        do_delete_content(idea, 'idea')
                else:
                    do_delete_content(idea, 'idea')
        except Exception as e:
            if idea.source == 'consultation_platform':
                logger.warning('Error when trying to delete the idea with the id={} from {}. '
                               'Message: {}'.format(idea.id, idea.source_consultation, e))
            else:
                logger.warning('Error when trying to delete the idea with the id={} from {}. '
                               'Message: {}'.format(idea.id, idea.source_social, e))
            logger.warning(traceback.format_exc())
    # Delete comments that don't exist anymore in their original social networks or consultation platforms
    logger.info('Checking whether exists comments that do not exist anymore')
    unexisting_comments = Comment.objects.exclude(exist=True).exclude(Q(cp_id=None) | Q(sn_id=None))
    for comment in unexisting_comments:
        try:
            if comment.initiative.active:
                if comment.source == 'social_network':
                    if not comment.source_social.subscribed_read_time_updates:
                        do_delete_content(comment, 'comment')
                else:
                    do_delete_content(comment, 'comment')
        except Exception as e:
            if comment.source == 'consultation_platform':
                logger.warning('Error when trying to delete the comment with the id={} from {}. '
                               'Message: {}'.format(comment.id, comment.source_consultation, e))
            else:
                logger.warning('Error when trying to delete the comment with the id={} from {}. '
                               'Message: {}'.format(comment.id, comment.source_social, e))
            logger.warning(traceback.format_exc())

@shared_task
def synchronize_content():
    # The cache key consists of the task name and the MD5 digest
    # of the feed URL.
    hexdigest = md5('social_ideation').hexdigest()
    lock_id = '{0}-lock-{1}'.format('synchronize_content', hexdigest)

    # cache.add fails if the key already exists
    acquire_lock = lambda: cache.add(lock_id, 'true', 60 * 5)  # Lock expires in 5 minutes
    # memcache delete is very slow, but we have to use it to take
    # advantage of using add() for atomic locking
    release_lock = lambda: cache.delete(lock_id)

    if acquire_lock():
        try:
            # Lock is used to ensure that synchronization is only executed one at time
            logger.info('Starting the synchronization')
            logger.info('----------------------------')
            pull_data()
            push_data()
            delete_data()
            logger.info('----------------------------')
            logger.info('The synchronization has successfully finished!')
        except Exception as e:
            logger.critical('Error!, the synchronization could not finish. Message: {}'.format(e))
            logger.critical(traceback.format_exc())
        finally:
            release_lock()
    else:
        logger.info('The synchronization is already being executed by another worker')


def test_function():
    pass