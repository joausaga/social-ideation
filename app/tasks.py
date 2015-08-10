from __future__ import absolute_import

from app.error import AppError
from app.models import ConsultationPlatform, Initiative, Author, Location, Idea, Comment, Vote, Campaign, SocialNetwork
from app.utils import convert_to_utf8_str
from celery import shared_task
from celery.utils.log import get_task_logger
from app.utils import do_request, get_json_or_error, get_url_cb, build_request_url, build_request_body, \
                      generate_idea_title_from_text, remove_hashtags
from django.core.cache import cache
from django.db.models import Q
from hashlib import md5

import traceback

logger = get_task_logger(__name__)


LOGO_IDEASCALE_VIA = 'https://dl.dropboxusercontent.com/u/55956367/via_is_white.png'


def _update_or_create_author(platform, author, source):
    try:
        if source == 'consultation_platform':
            author_obj = Author.objects.get(external_id=author['id'], consultation_platform=platform)
        else:
            author_obj = Author.objects.get(external_id=author['id'], social_network=platform)
    except Author.DoesNotExist:
        if 'email' not in author.keys() or 'name' not in author.keys():
            connector = platform.connector
            if source == 'consultation_platform':
                # Fetch author inform from consultation platform
                url_cb = get_url_cb(connector, 'get_user_cb')
                url = build_request_url(url_cb.url, url_cb.callback, {'user_id': author['id']})
                resp = do_request(connector, url, url_cb.callback.method)
                author = get_json_or_error(connector.name, url_cb.callback, resp)
            else:
                # Fetch author inform from social network
                sn_class = connector.connector_class.title()
                sn_module = connector.connector_module.lower()
                sn = getattr(__import__(sn_module, fromlist=[sn_class]), sn_class)
                sn.authenticate()
                author = sn.get_info_user(author['id'])
        attr_new_author = {'screen_name': author['name'], 'channel': source, 'external_id': author['id']}
        if 'email' in author.keys():
            attr_new_author.update({'email': author['email']})
        if 'url' in author.keys():
            attr_new_author.update({'url': author['url']})
        if source == 'consultation_platform':
            attr_new_author.update({'consultation_platform': platform})
        else:
            attr_new_author.update({'social_network': platform})
        author_obj = Author(**attr_new_author)
        author_obj.save()

    return author_obj


def _get_or_create_location(location):
    attr_new_location = {'latitude': location['latitude'], 'longitude': location['longitude'],
                         'city': location['city'], 'country': location['country']}
    location_obj, location_created = Location.objects.get_or_create(city=location['city'], country=location['country'],
                                                                    defaults=attr_new_location)
    return location_obj


def _update_or_create_content(platform, raw_obj, model, filters, obj_attrs, editable_fields, source):
    # Handle content author
    obj_attrs.update({'author': _update_or_create_author(platform, raw_obj['user_info'], source)})
    # Handle content location
    if 'location_info' in raw_obj.keys():
        obj_attrs.update({'location': _get_or_create_location(raw_obj['location_info'])})
    # Handle content creation or updating
    content_obj, content_created = model.objects.get_or_create(defaults=obj_attrs, **filters)
    if not content_created and content_obj.source == source:
        content_obj.exist = True
        for editable_field in editable_fields:
            obj_field = getattr(content_obj, editable_field)
            if obj_field != raw_obj[editable_field]:
                logger.info('The object with the id {} has changed its {}. '
                            'Before {}, now {}'.format(content_obj.id, editable_field,
                                                       obj_field, raw_obj[editable_field]))
                content_obj.has_changed = True
                setattr(content_obj, editable_field, raw_obj[editable_field])
    content_obj.save()

    return content_obj


def _get_parent(content_type, content_id, source):
    if source == 'consultation_platform':
        filter = {'cp_id': content_id}
    else:
        filter = {'sn_id':content_id}
    if content_type == 'idea':
        try:
            return {'parent': 'idea', 'parent_idea': Idea.objects.get(**filter)}
        except Idea.DoesNotExist:
            return None
    else:
        try:
            return {'parent': 'comment', 'parent_comment': Comment.objects.get(**filter)}
        except Comment.DoesNotExist:
            return None


def _do_create_update_comment(platform, initiative, comment, source):
    if source == 'consultation_platform':
        filters = {'cp_id': comment['id']}
    else:
        filters = {'sn_id': comment['id']}
    parent_dict = _get_parent(comment['parent_type'], comment['parent_id'], source)
    if parent_dict:
        if comment['parent_type'] == 'idea':
            campaign = parent_dict['parent_idea'].campaign
        else:
            campaign = parent_dict['parent_comment'].campaign
        comment_attrs = {'source': source, 'datetime': comment['datetime'], 'text': comment['text'],
                         'url': comment['url'], 'comments': comment['comments'], 'initiative': initiative,
                         'campaign': campaign, 'positive_votes': comment['positive_votes'],
                         'negative_votes': comment['negative_votes']}
        comment_attrs.update(parent_dict)
        if source == 'consultation_platform':
            comment_attrs.update({'source_consultation': platform, 'cp_id': comment['id']})
        else:
            comment_attrs.update({'source_social': platform, 'sn_id': comment['id'], })
        editable_fields = ('text','comments', 'positive_votes', 'negative_votes')
        return _update_or_create_content(platform, comment, Comment, filters, comment_attrs, editable_fields, source)
    else:
        return None


def _do_create_update_vote(platform, initiative, vote, source):
    author = _update_or_create_author(platform, {'id': vote['user_id']}, source)
    parent_dict = _get_parent(vote['parent_type'], vote['parent_id'], source)
    if parent_dict:
        if vote['parent_type'] == 'idea':
            campaign = parent_dict['parent_idea'].campaign
        else:
            campaign = parent_dict['parent_comment'].campaign
        vote_attrs = {'source': source, 'initiative': initiative, 'campaign': campaign, 'value': vote['value'],
                      'author': author}
        vote_attrs.update(parent_dict)
        if source == 'consultation_platform':
            vote_attrs.update({'cp_id': vote['id'], 'source_consultation': platform})
            filters = {'cp_id': vote['id'], 'defaults': vote_attrs}
        else:
            vote_attrs.update({'sn_id': vote['id'], 'source_social': platform})
            filters = {'sn_id': vote['id'], 'defaults': vote_attrs}
        if 'datetime' in vote.keys():
            vote_attrs.update({'datetime': vote['datetime']})
        vote_obj, vote_created = Vote.objects.get_or_create(**filters)
        if not vote_created:
            vote_obj.exist = True
            if vote_obj.value != vote['value']:
                vote_obj.value = vote['value']
                vote_obj.has_changed = True
            vote_obj.save()
    else:
        logger.error('Vote {} could\'nt be synchronized because its parent {} with id {} couldn\'t be found'.
                     format(vote['id'], vote['parent_type'], vote['parent_id']))

def _cud_initiative_votes(platform, initiative):
    # Fetch initiative's votes
    connector = platform.connector
    url_cb = get_url_cb(connector, 'get_votes_ideas_cb')
    url = build_request_url(url_cb.url, url_cb.callback, {'initiative_id': initiative.external_id})
    resp = do_request(connector, url, url_cb.callback.method)
    votes = get_json_or_error(connector.name, url_cb.callback, resp)
    url_cb = get_url_cb(connector, 'get_votes_comments_cb')
    url = build_request_url(url_cb.url, url_cb.callback, {'initiative_id': initiative.external_id})
    resp = do_request(connector, url, url_cb.callback.method)
    votes += get_json_or_error(connector.name, url_cb.callback, resp)
    for vote in votes:
        _do_create_update_vote(platform, initiative, vote, 'consultation_platform')


def _cud_initiative_comments(platform, initiative):
    # Fetch initiative's comments
    connector = platform.connector
    url_cb = get_url_cb(connector, 'get_comments_cb')
    url = build_request_url(url_cb.url, url_cb.callback, {'initiative_id': initiative.external_id})
    resp = do_request(connector, url, url_cb.callback.method)
    comments = get_json_or_error(connector.name, url_cb.callback, resp)
    delayed_comments = []
    # Iterate over initiative's comments
    for comment in comments:
        comment_obj = _do_create_update_comment(platform, initiative, comment, 'consultation_platform')
        if not comment_obj:
            delayed_comments.append(comment)
    for delayed_comment in delayed_comments:
        comment_obj = _do_create_update_comment(platform, initiative, delayed_comment, 'consultation_platform')
        if not comment_obj:
            logger.warning('Comment {} couldn\'t be synchronized because its parent {} with id {} couldn\'t be found. {}'.
                           format(delayed_comment['id'], delayed_comment['parent_type'], delayed_comment['parent_id'],
                                  delayed_comment['text']))


def _cud_initiative_ideas(platform, initiative):
    # Fetch ideas
    connector = platform.connector
    ideas_url_cb = get_url_cb(connector, 'get_ideas_cb')
    url = build_request_url(ideas_url_cb.url, ideas_url_cb.callback, {'initiative_id': initiative.external_id})
    resp = do_request(connector, url, ideas_url_cb.callback.method)
    ideas = get_json_or_error(connector.name, ideas_url_cb.callback, resp)
    # Iterate over initiative's ideas
    for idea in ideas:
        try:
            campaign = Campaign.objects.get(external_id=idea['campaign_info']['id'])
        except Campaign.DoesNotExist:
            logger.warning('Couldn\'t find the campaign with the id {} within the initiative {}. '
                           'Idea {} cannot be synchronized.'.format(idea['campaign_info']['id'], initiative.name,
                                                                    idea['id']))
            continue
        filters = {'cp_id': idea['id']}
        idea_attrs = {'cp_id': idea['id'], 'source': 'consultation_platform', 'datetime': idea['datetime'],
                      'title': idea['title'], 'text': idea['text'], 'url': idea['url'], 'comments': idea['comments'],
                      'initiative': initiative, 'campaign': campaign, 'positive_votes': idea['positive_votes'],
                      'negative_votes': idea['negative_votes'], 'source_consultation': platform}
        editable_fields = ('title', 'text', 'comments', 'positive_votes', 'negative_votes')
        _update_or_create_content(platform, idea, Idea, filters, idea_attrs, editable_fields, 'consultation_platform')


def _extract_hashtags(post):
    hashtags = []
    lines = post['text'].split('\n')
    for line in lines:
        words = line.split(' ')
        for word in words:
            if '#' in word:
                hashtags.append(word.replace('#','').replace('\n','').lower().strip())
    return hashtags


def _get_initiative(hashtags, social_network):
    try:
        initiatives = Initiative.objects.filter(social_network=social_network)
        for initiative in initiatives:
            if initiative.hashtag in hashtags:
                return initiative
        return None
    except ValueError:
        return None


def _get_campaign(hashtags, initiative):
    campaigns = initiative.campaign_set.all()
    for campaign in campaigns:
        if campaign.hashtag in hashtags:
            return campaign
    return None


def _pull_content_social_network(social_network):
    connector = social_network.connector
    sn_class = connector.connector_class.title()
    sn_module = connector.connector_module.lower()
    sn = getattr(__import__(sn_module, fromlist=[sn_class]), sn_class)
    sn.authenticate()
    posts = sn.get_posts()
    for post in posts:
        hashtags = _extract_hashtags(post)
        if len(hashtags) > 0:
            initiative = _get_initiative(hashtags, social_network)
            #initiative = Initiative.objects.get(pk=4)
            if initiative:
                campaign = _get_campaign(hashtags, initiative)
                #campaign = Campaign.objects.get(pk=7)
                if campaign:
                    # Save/Update ideas
                    filters = {'sn_id': post['id']}
                    idea_attrs = {'sn_id': post['id'], 'source': 'social_network', 'datetime': post['datetime'],
                                  'title': post['title'], 'text': post['text'], 'url': post['url'],
                                  'comments': post['comments'], 'initiative': initiative, 'campaign': campaign,
                                  'positive_votes': post['positive_votes'], 'negative_votes': post['negative_votes'],
                                  'source_social': social_network}
                    editable_fields = ('title', 'text', 'comments', 'positive_votes', 'negative_votes')
                    _update_or_create_content(social_network, post, Idea, filters, idea_attrs, editable_fields,
                                              'social_network')
                    # Save/Update comments
                    if 'comments_array' in post.keys():
                        for comment in post['comments_array']:
                            comment.update({'parent_type': 'idea'})
                            _do_create_update_comment(social_network, initiative, comment, 'social_network')
                            # Process comment's replies
                            if 'comments_array' in comment.keys():
                                for reply in comment['comments_array']:
                                    _do_create_update_comment(social_network, initiative, reply, 'social_network')
                            # Process comment's votes
                            if 'votes_array' in comment.keys():
                                for vote in comment['votes_array']:
                                    vote.update({'user_id': vote['user_info']['id']})
                                    _do_create_update_vote(social_network, initiative, vote, 'social_network')
                    # Save/Update votes
                    if 'votes_array' in post.keys():
                        for vote in post['votes_array']:
                            vote.update({'user_id': vote['user_info']['id'], 'parent_type': 'idea'})
                            _do_create_update_vote(social_network, initiative, vote, 'social_network')


def _pull_content_consultation_platform(platform, initiative):
    _cud_initiative_ideas(platform, initiative)
    _cud_initiative_comments(platform, initiative)
    _cud_initiative_votes(platform, initiative)


def _invalidate_initiative_content(**kwargs):
    # The invalidation process consist in assuming that all ideas, comments, and votes don't exist anymore
    # Then as they are obtained from the external platform they will be marked as still existing
    Idea.objects.filter(**kwargs).update(exist=False)
    Comment.objects.filter(**kwargs).update(exist=False)
    Vote.objects.filter(**kwargs).update(exist=False)


def _do_data_consolidation(type_obj, filters):
    objs_consolidated = 0

    if type_obj == 'idea':
        objs = Idea.objects.filter(**filters)
    else:
        objs = Comment.objects.filter(**filters)

    for obj in objs:
        if type_obj == 'idea':
            attrs = {'parent': type_obj, 'parent_idea': obj.id}
        else:
            attrs = {'parent': type_obj, 'parent_comment': obj.id}
        # Consolidate comments
        comments_saved = Comment.objects.filter(**attrs).count()
        # Add also replies to the comments
        for comment_saved in Comment.objects.filter(**attrs):
            comments_saved += Comment.objects.filter(parent_comment=comment_saved.id).count()
        if getattr(obj, 'comments') != comments_saved:
            logger.info('{} with id {} has inconsistent its property comments. Property: {} - Registered in DB: {}'.
                        format(type_obj, obj.id, getattr(obj, 'comments'), comments_saved))
            objs_consolidated += 1
            setattr(obj, 'comments', comments_saved)
        # Consolidate positive votes
        attrs.update({'value': 1})
        p_votes_saved = Vote.objects.filter(**attrs).count()
        if getattr(obj, 'positive_votes') != p_votes_saved:
            logger.info('{} with id {} has inconsistent its property positive_votes. '
                        'Property: {} - Registered in DB: {}'.format(type_obj, obj.id, getattr(obj, 'positive_votes'),
                                                                        p_votes_saved))
            objs_consolidated += 1
            setattr(obj, 'positive_votes', p_votes_saved)
        # Check negative votes
        attrs.update({'value': -1})
        n_votes_saved = Vote.objects.filter(**attrs).count()
        if getattr(obj, 'negative_votes') != n_votes_saved:
            logger.info('{} with id {} has inconsistent its property negative_votes. '
                        'Property: {} - Registered in DB: {}'.format(type_obj, obj.id, getattr(obj, 'negative_votes'),
                                                                        n_votes_saved))
            objs_consolidated += 1
            setattr(obj, 'inconsistent', n_votes_saved)
        obj.save()

    return objs_consolidated


def _consolidate_data(platform, source):
    """
    Consolidate the number of votes (positives and negatives) and comments declared in
    the ideas/comments' votes (positive and negative) and comments properties
    """
    objs_consolidated = 0
    if source == 'consultation_platform':
        filters = {'source_consultation': platform, 'exist': True}
    else:
        filters = {'source_social': platform, 'exist': True}
    objs_consolidated += _do_data_consolidation('idea', filters)
    objs_consolidated += _do_data_consolidation('comment', filters)

    return objs_consolidated


def _do_push_content(obj, type):
    initiative = obj.initiative
    campaign = obj.campaign
    #template_idea = '{}\n\nAuthor: {} ({})\n\nVotes ({}) Up: {}/Down: {}\n\nLink: {}'
    template_idea_cp = '{}\n\n' \
                       '----------------\n\n' \
                       'Author: {}'
    template_comment_cp = '{}\n' \
                          'Author: {}'
    template_idea_sn = '----------------\n' \
                       '{}\n' \
                       '----------------\n\n' \
                       '{}\n\n' \
                       '#{} #{}'
    template_comment_sn = '{}\n\n' \
                          'Votes Up: {}/Down: {}\n' \
                          'Author: {} ({})'
    desc_attachment = 'Idea contributed by {} in the initiative {}'
    desc_caption_attachment = 'Votes Up: {}/Down: {}'
    text_uf8 = convert_to_utf8_str(obj.text)
    author_name_utf8 = convert_to_utf8_str(obj.author.screen_name)
    if obj.source == 'consultation_platform':
        # Push object to the initiative's social networks
        ini_hashtag = initiative.hashtag
        cam_hashtag = campaign.hashtag
        for social_network in initiative.social_network.all():
            connector = social_network.connector
            sn_class = connector.connector_class.title()
            sn_module = connector.connector_module.lower()
            sn = getattr(__import__(sn_module, fromlist=[sn_class]), sn_class)
            sn.authenticate()
            # TODO: New text should be bounded by the social network's text length restriction
            if obj.is_new:
                obj.is_new = False
                if type == 'idea':
                    title_utf8 = convert_to_utf8_str(obj.title)
                    text_to_sn = template_idea_sn.format(title_utf8, text_uf8, ini_hashtag.lower(), cam_hashtag.lower())
                    attachment = {
                        'name': title_utf8,
                        'link':  obj.url,
                        'caption': desc_caption_attachment.format(obj.positive_votes, obj.negative_votes),
                        'description': desc_attachment.format(author_name_utf8, initiative.name),
                        'picture': LOGO_IDEASCALE_VIA
                    }
                    new_post = sn.publish_post(text_to_sn, attachment)
                    obj.sn_id = new_post['id']
                elif type == 'comment':
                    text_to_sn = template_comment_sn.format(text_uf8, obj.positive_votes, obj.negative_votes,
                                                            author_name_utf8, obj.source_consultation.name)
                    if obj.parent == 'idea':
                        parent = Idea.objects.get(id=obj.parent_idea.id)
                        new_comment = sn.comment_post(parent.sn_id, text_to_sn)
                        obj.sn_id = new_comment['id']
                    elif obj.parent == 'comment':
                        try:
                            parent = Comment.objects.get(id=obj.parent_comment.id)
                            new_comment = sn.comment_comment(parent.sn_id, text_to_sn)
                            obj.sn_id = new_comment['id']
                        except:
                            logger.info('Replies to comments cannot be posted through the API of {}'.
                                        format(social_network.name))
                    else:
                        raise AppError('Unknown the type of the object\'s parent')
                else:
                    logger.info('Objects of type {} are ignored and not synchronized'.format(type))
            elif obj.has_changed:
                obj.has_changed = False
                # Update content to social network
                if type == 'idea':
                    title_utf8 = convert_to_utf8_str(obj.title)
                    text_to_sn = template_idea_sn.format(title_utf8, text_uf8, ini_hashtag.lower(), cam_hashtag.lower())
                    attachment = {
                        'name': title_utf8,
                        'link':  obj.url,
                        'caption': desc_caption_attachment.format(obj.positive_votes, obj.negative_votes),
                        'description': desc_attachment.format(author_name_utf8, initiative.name),
                        'picture': LOGO_IDEASCALE_VIA
                    }
                    sn.edit_post(obj.sn_id, text_to_sn, attachment)
                elif type == 'comment':
                    text_to_sn = template_comment_sn.format(text_uf8, obj.positive_votes, obj.negative_votes,
                                                            author_name_utf8, obj.source_consultation.name)
                    sn.edit_comment(obj.sn_id, text_to_sn)
                else:
                    logger.info('Objects of type {} are ignored and not synchronized'.format(type))
    else:
        # Push object to the initiative's consultation_platform
        cplatform = initiative.platform
        connector = cplatform.connector
        text_cplatform = remove_hashtags(text_uf8)
        if obj.is_new:
            obj.is_new = False
            if type == 'idea':
                text_to_cp = template_idea_cp.format(text_cplatform, author_name_utf8)
                url_cb = get_url_cb(connector, 'create_idea_cb')
                url = build_request_url(url_cb.url, url_cb.callback, {'initiative_id': initiative.external_id})
                params = {'title': generate_idea_title_from_text(obj.text), 'text': text_to_cp,
                          'campaign_id': campaign.external_id}
                body_param = build_request_body(connector, url_cb.callback, params)
                resp = do_request(connector, url, url_cb.callback.method, body_param)
                new_content = get_json_or_error(connector.name, url_cb.callback, resp)
                obj.cp_id = new_content['id']
            elif type == 'comment':
                text_to_cp = template_comment_cp.format(text_cplatform, author_name_utf8)
                params = {'text': text_to_cp}
                if obj.parent == 'idea':
                    url_cb = get_url_cb(connector, 'create_comment_idea_cb')
                    url = build_request_url(url_cb.url, url_cb.callback, {'idea_id': obj.parent_idea.cp_id})
                elif obj.parent == 'comment':
                    url_cb = get_url_cb(connector, 'create_comment_comment_cb')
                    url = build_request_url(url_cb.url, url_cb.callback, {'comment_id': obj.parent_comment.cp_id})
                else:
                    raise AppError('Unknown the type of the object\'s parent')
                body_param = build_request_body(connector, url_cb.callback, params)
                resp = do_request(connector, url, url_cb.callback.method, body_param)
                new_content = get_json_or_error(connector.name, url_cb.callback, resp)
                obj.cp_id = new_content['id']
            else:
                logger.info('Objects of type {} are ignored and not synchronized'.format(type))
        elif obj.has_changed:
            obj.has_changed = False
            if type == 'idea':
                text_to_cp = template_idea_cp.format(text_cplatform, author_name_utf8)
                try:
                    url_cb = get_url_cb(connector, 'update_idea_cb')
                    url = build_request_url(url_cb.url, url_cb.callback, {'idea_id': obj.cp_id})
                    params = {'title': generate_idea_title_from_text(obj.text), 'text': text_to_cp,
                              'campaign_id': campaign.external_id}
                    body_param = build_request_body(connector, url_cb.callback, params)
                    do_request(connector, url, url_cb.callback.method, body_param)
                except:
                    logger.info('Cannon\'t find the url of the callback to update ideas through the API of {}'.
                                format(cplatform.name))
            elif type == 'comment':
                text_to_cp = template_comment_cp.format(text_cplatform, author_name_utf8)
                try:
                    url_cb = get_url_cb(connector, 'update_comment_cb')
                    url = build_request_url(url_cb.url, url_cb.callback, {'comment_id': obj.cp_id})
                    params = {'text': text_to_cp}
                    body_param = build_request_body(connector, url_cb.callback, params)
                    do_request(connector, url, url_cb.callback.method, body_param)
                except:
                    logger.info('Cannon\'t find the url of the callback to update comments through the API of {}'.
                                format(cplatform.name))
    obj.sync = True
    obj.save()


def _do_delete_content(obj, type):
    initiative = obj.initiative
    if obj.source == 'consultation_platform':
        # Delete object from the initiative's social networks
        for social_network in initiative.social_network.all():
            connector = social_network.connector
            sn_class = connector.connector_class.title()
            sn_module = connector.connector_module.lower()
            sn = getattr(__import__(sn_module, fromlist=[sn_class]), sn_class)
            sn.authenticate()
            if type == 'idea':
                sn.delete_post(obj.sn_id)
                logger.info('The idea {} does not exists anymore in {} and thus it was deleted from {}'.
                            format(obj.id, obj.source_consultation, social_network))
            else:
                sn.delete_comment(obj.sn_id)
                logger.info('The comment {} does not exists anymore in {} and thus it was deleted from {}'.
                            format(obj.id, obj.source_consultation, social_network))
    else:
        # Delete object from the initiative's consultation platform
        cplatform = initiative.platform
        connector = cplatform.connector
        if type == 'idea':
            url_cb = get_url_cb(connector, 'delete_idea_cb')
            url = build_request_url(url_cb.url, url_cb.callback, {'idea_id': obj.cp_id})
            do_request(connector, url, url_cb.callback.method)
            logger.info('The idea {} does not exists anymore in {} and thus it was deleted from {}'.
                         format(obj.id, obj.source_social, cplatform))
        else:
            url_cb = get_url_cb(connector, 'delete_comment_cb')
            url = build_request_url(url_cb.url, url_cb.callback, {'comment_id': obj.cp_id})
            do_request(connector, url, url_cb.callback.method)
            logger.info('The comment {} does not exists anymore in {} and thus it was deleted from {}'.
                         format(obj.id, obj.source_social, cplatform))
    obj.sn_id = None
    obj.cp_id = None
    obj.save()


def pull_data():
    # Pull data from consultation platforms
    for cplatform in ConsultationPlatform.objects.all():
        initiatives = Initiative.objects.filter(platform=cplatform)
        for initiative in initiatives:
            if initiative.active:
                logger.info('Pulling content of the initiative {} from the platform {}'.format(initiative,
                                                                                               cplatform))
                _invalidate_initiative_content(source_consultation=cplatform, initiative=initiative)
                try:
                    _pull_content_consultation_platform(cplatform, initiative)
                except Exception as e:
                    logger.warning('Problem when trying to pull content of the initiative {} from platform {}. '
                                   'Message: {}'.
                                   format(initiative, cplatform, e))
                    logger.warning(traceback.format_exc())
    # Pull data from social networks
    for socialnetwork in SocialNetwork.objects.all():
        initiatives = Initiative.objects.filter(social_network=socialnetwork)
        for initiative in initiatives:
            if initiative.active:
                _invalidate_initiative_content(source_social=socialnetwork, initiative=initiative)
        logger.info('Pulling content posted on {}'.format(socialnetwork))
        try:
            _pull_content_social_network(socialnetwork)
        except Exception as e:
            logger.warning('Problem when trying to pull content posted on {}. Message: {}'.
                           format(socialnetwork, e))
            logger.warning(traceback.format_exc())


def push_data():
    # Push ideas to consultation platforms and social networks
    logger.info('Pushing ideas to social networks and consultation platforms')
    existing_ideas = Idea.objects.exclude(exist=False).filter(Q(has_changed=True) | Q(is_new=True)).\
                     order_by('datetime')
    for idea in existing_ideas:
        try:
            if idea.initiative.active:
                _do_push_content(idea, 'idea')
        except Exception as e:
            if idea.source == 'consultation_platform':
                logger.warning('Error when trying to publish the idea with the id={} on {}. '
                               'Message: {}'.format(idea.id, idea.source_consultation, e))
            else:
                logger.warning('Error when trying to publish the idea with the id={} on {}. '
                               'Message: {}'.format(idea.id, idea.source_social, e))
            logger.warning(traceback.format_exc())
    # Push comments to consultation platforms and social networks
    logger.info('Pushing comments to social networks and consultation platforms')
    existing_comments = Comment.objects.exclude(exist=False).filter(Q(has_changed=True) | Q(is_new=True)).\
                        order_by('datetime')
    for comment in existing_comments:
        try:
            if comment.initiative.active:
                _do_push_content(comment, 'comment')
        except Exception as e:
                if comment.source == 'consultation_platform':
                    logger.warning('Error when trying to publish the comment with the id={} on {}. '
                                   'Message: {}'.format(comment.id, comment.source_consultation, e))
                else:
                    logger.warning('Error when trying to publish the comment with the id={} on {}. '
                                   'Message: {}'.format(comment.id, comment.source_social, e))
                logger.warning(traceback.format_exc())


def delete_data():
    # Delete ideas that don't exist anymore in their original social networks or consultation platforms
    logger.info('Checking whether exists ideas that do not exist anymore')
    unexisting_ideas = Idea.objects.exclude(exist=True).exclude(Q(cp_id=None) | Q(sn_id=None))
    for idea in unexisting_ideas:
        try:
            if idea.initiative.active:
                _do_delete_content(idea, 'idea')
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
                _do_delete_content(comment, 'comment')
        except Exception as e:
            if comment.source == 'consultation_platform':
                logger.warning('Error when trying to delete the comment with the id={} from {}. '
                               'Message: {}'.format(comment.id, comment.source_consultation, e))
            else:
                logger.warning('Error when trying to delete the comment with the id={} from {}. '
                               'Message: {}'.format(comment.id, comment.source_social, e))
            logger.warning(traceback.format_exc())


def consolidate_app_db():
    for cplatform in ConsultationPlatform.objects.all():
        objs_consolidated = _consolidate_data(cplatform, 'consultation_platform')
        logger.info('{} objects were consolidated in the platform {}'.format(objs_consolidated, cplatform))
    for socialnetwork in SocialNetwork.objects.all():
        objs_consolidated = _consolidate_data(socialnetwork, 'social_network')
        logger.info('{} objects were consolidated in the social_network {}'.format(objs_consolidated, socialnetwork))


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