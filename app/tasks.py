# -*- coding: UTF-8 -*-
from __future__ import absolute_import

from app.models import ConsultationPlatform, Initiative, Idea, Comment, SocialNetworkApp
from app.sync import save_sn_post, save_sn_comment, save_sn_vote, cud_initiative_votes, cud_initiative_ideas, \
                     cud_initiative_comments, invalidate_initiative_content, do_push_content, do_delete_content, \
                     revalidate_initiative_content, notify_new_campaigns, count_other_platform_votes, notify_new_users, \
                     notify_join_group, check_reactivated_accounts_activity
from app.utils import convert_to_utf8_str, call_social_network_api
from app.error import AppError
from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.cache import cache
from django.db.models import Q
from hashlib import md5

import traceback

logger = get_task_logger(__name__)


def _pull_content_social_network(social_network, initiative):
    if social_network.community:
        params = {'app': social_network}
        posts = call_social_network_api(social_network.connector, 'get_posts', params)
        for post in posts:
            ret_data = save_sn_post(social_network, post, initiative)
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
        logger.warning('Cannot pull content from the social network {}. Reason: Community not found'.
                       format(social_network.name))


def _pull_content_consultation_platform(platform, initiative):
    cud_initiative_ideas(platform, initiative)
    cud_initiative_comments(platform, initiative)
    cud_initiative_votes(platform, initiative)
    notify_new_campaigns(initiative)
    count_other_platform_votes()
    notify_new_users(initiative)
    notify_join_group(initiative)
    check_reactivated_accounts_activity()
    #update_IS_user_demographic_data(initiative)


def _handle_pull_exceptions(initiative, platform, invalidate_filters, update_attrs):
    revalidate_initiative_content(invalidate_filters, update_attrs)
    logger.warning('Problem when trying to pull content of the initiative {} from {}. '
                   'The content was re-validated.'.format(initiative, platform))


def pull_data():
    # Pull data of the active initiatives from the consultation platforms
    # and social networks where they are running on
    initiatives = Initiative.objects.filter(active=True)
    for initiative in initiatives:
        invalidate_filters = {'initiative': initiative, 'is_new': False}
        try:
            invalidate_initiative_content(invalidate_filters, {'exist_cp': False})
            logger.info(u'Pulling content of the initiative {} from the platform {}'.format(initiative,
                                                                                           initiative.platform))
            _pull_content_consultation_platform(initiative.platform, initiative)
            for socialnetwork in initiative.social_network.all():
                if not socialnetwork.subscribed_read_time_updates:
                    try:
                        invalidate_initiative_content(invalidate_filters, {'exist_sn': False})
                        logger.info(u'Pulling content of the initiative {} from the platform {}'.format(initiative,
                                                                                                       socialnetwork))
                        _pull_content_social_network(socialnetwork, initiative)
                    except Exception as e:
                        _handle_pull_exceptions(initiative, socialnetwork, invalidate_filters, {'exist_sn': True})
                        raise AppError(e)
                        
        except Exception as e:
            _handle_pull_exceptions(initiative, initiative.platform, invalidate_filters, {'exist_cp': True})
            raise AppError(e)

def push_data():
    batch_req_ideas = {}
    batch_req_comments = {}
    # Push ideas to consultation platforms and social networks
    logger.info('Pushing ideas to social networks and consultation platforms')
    existing_ideas = Idea.objects.filter(Q(exist_sn=True, sn_id__isnull=False) |
                                         Q(exist_cp=True, cp_id__isnull=False)).\
                                  filter(Q(has_changed=True) | Q(is_new=True)).\
                                  order_by('datetime')
    tot_ideas_to_sn = Idea.objects.filter(Q(exist_sn=True, sn_id__isnull=False) |
                                          Q(exist_cp=True, cp_id__isnull=False)).\
                                   filter(Q(has_changed=True) | Q(is_new=True)).\
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
                               .format(idea.id))
                logger.warning(traceback.format_exc())
            else:
                logger.warning('Error when trying to publish the idea with the id={} on the consultation platforms.'
                               .format(idea.id))
            raise AppError(e)

    # Push comments to consultation platforms and social networks
    logger.info('Pushing comments to social networks and consultation platforms')
    existing_comments = Comment.objects.filter(Q(exist_sn=True, sn_id__isnull=False) |
                                              Q(exist_cp=True, cp_id__isnull=False)).\
                                        filter(Q(has_changed=True) | Q(is_new=True)).\
                                        order_by('datetime')
    tot_comments_to_sn = Comment.objects.filter(Q(exist_sn=True, sn_id__isnull=False) |
                                                Q(exist_cp=True, cp_id__isnull=False)).\
                                         filter(Q(has_changed=True) | Q(is_new=True)).\
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
                logger.warning('Error when trying to publish the comment with the id={} on the social networks.'
                               .format(comment.id))
            else:
                logger.warning('Error when trying to publish the comment with the id={} on the consultation platforms.'
                               .format(comment.id))
            raise AppError(e)
            
def delete_data():
    # Delete comments that don't exist anymore in their original social networks or consultation platforms
    logger.info('Checking whether exists comments that do not exist anymore')
    unexisting_comments = Comment.objects.filter(Q(exist_sn=False, sn_id__isnull=False) |
                                                 Q(exist_cp=False, cp_id__isnull=False))
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
                               .format(comment.id, comment.source_consultation))
            else:
                logger.warning('Error when trying to delete the comment with the id={} from {}. '
                               .format(comment.id, comment.source_social))
            logger.warning(traceback.format_exc())
    # Delete ideas that don't exist anymore in their original social networks or consultation platforms
    logger.info('Checking whether exists ideas that do not exist anymore')
    unexisting_ideas = Idea.objects.filter(Q(exist_sn=False, sn_id__isnull=False) |
                                           Q(exist_cp=False, cp_id__isnull=False))
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
                               .format(idea.id, idea.source_consultation))
            else:
                logger.warning('Error when trying to delete the idea with the id={} from {}. '.
                               format(idea.id, idea.source_social))
            raise AppError(e)

@shared_task
def synchronize_content():
    # The cache key consists of the task name and the MD5 digest
    # of the feed URL.
    hexdigest = md5('social_ideation').hexdigest()
    lock_id = '{0}-lock-{1}'.format('synchronize_content', hexdigest)

    # cache.add fails if the key already exists
    acquire_lock = lambda: cache.add(lock_id, 'true', 60 * 20)  # Lock expires in 20 minutes
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
            logger.info('The synchronization has successfully finished!')
            logger.info('----------------------------')
        except Exception as e:
            if 'HTTPConnectionPool' in e and 'timed out' in e:
                # Only register in the log and don't notify via email when timed out errors occur
                logger.warning('The synchronization could not finish successfully. {}'.format(convert_to_utf8_str(e)))
            else:
                logger.error('The synchronization could not finish successfully.\n{}\n\n{}'.
                             format(convert_to_utf8_str(e), traceback.format_exc()))
        finally:
            release_lock()
    else:
        logger.info('The synchronization is already being executed by another worker')


def test_function():
    pass
