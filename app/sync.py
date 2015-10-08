import logging
import json
import traceback

from app.error import AppError
from app.models import Idea, Author, Location, Initiative, Comment, Vote, Campaign, ConsultationPlatform, \
                       SocialNetworkApp, SocialNetworkAppUser, AutoComment
from app.utils import do_request, get_json_or_error, get_url_cb, build_request_url, convert_to_utf8_str, \
                      build_request_body, call_social_network_api
from datetime import datetime
from django.utils import timezone
from django.utils.translation import override, activate, deactivate, ugettext as _
from django.core.mail import EmailMessage
from django.template import Context
from django.template.loader import render_to_string, get_template

logger = logging.getLogger(__name__)


def generate_idea_title_from_text(text):
    title = ''
    TITLE_LENGTH = 64  # Taking as reference IdeaScale's limitation

    for word in text.split():
        if not '#' in word:
            if len(title) + len(word) <= TITLE_LENGTH:
                title += ' ' + word
            else:
                break

    return convert_to_utf8_str(title.strip().title())


def remove_hashtags(text):
    text_without_hashtags = ''

    for word in text.split():
        if not '#' in word:
            text_without_hashtags += word + ' '

    return text_without_hashtags


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
                try:
                    app_user = SocialNetworkAppUser.objects.get(external_id=author['id'])
                    author = {'id': app_user.external_id, 'name': app_user.name, 'email': app_user.email,
                              'url': app_user.url}
                except SocialNetworkAppUser.DoesNotExist:
                    params = {'app': platform, 'id_user': author['id']}
                    author = call_social_network_api(connector, 'get_info_user', params)
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


def update_or_create_content(platform, raw_obj, model, filters, obj_attrs, editable_fields, source,
                             changeable_fields):
    # Handle content author
    obj_attrs.update({'author': _update_or_create_author(platform, raw_obj['user_info'], source)})
    # Handle content location
    if 'location_info' in raw_obj.keys():
        obj_attrs.update({'location': _get_or_create_location(raw_obj['location_info'])})
    # Handle content creation or updating
    content_obj, content_created = model.objects.get_or_create(defaults=obj_attrs, **filters)
    if source == 'consultation_platform':
        content_obj.exist_cp = True
    else:
        content_obj.exist_sn = True
    if not content_created and content_obj.source == source:
        for editable_field in editable_fields:
            obj_field = getattr(content_obj, editable_field)
            if obj_field != raw_obj[editable_field]:
                logger.info('The object with the id {} has changed its {}\n.'.format(content_obj.id,
                                                                                     editable_field))
                logger.info('Before {}, now {}'.format(convert_to_utf8_str(obj_field),
                                                       convert_to_utf8_str(raw_obj[editable_field])))
                if editable_field in changeable_fields:
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


def do_create_update_comment(platform, initiative, comment, source):
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
        changeable_fields = ('text', 'positive_votes', 'negative_votes')
        return update_or_create_content(platform, comment, Comment, filters, comment_attrs, editable_fields, source,
                                        changeable_fields)
    else:
        return None


def do_create_update_vote(platform, initiative, vote, source):
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
            if source == 'consultation_platform':
                vote_obj.exist_cp = True
            else:
                vote_obj.exist_sn = True
            if vote_obj.value != vote['value']:
                vote_obj.value = vote['value']
                vote_obj.has_changed = True
            vote_obj.save()
    else:
        logger.error('Vote {} could\'nt be synchronized because its parent {} with id {} couldn\'t be found'.
                     format(vote['id'], vote['parent_type'], vote['parent_id']))


def _get_str_language(lang, type):
    if lang == 'es':
        if type == 'votes':
            return '[Votos +: {}/-: {}]'
        elif type == 'desc_attach':
            return 'Idea enviada por {} en el marco de la iniciativa {}'
        elif type == 'author':
            return 'Autor: {}'
        elif type == 'author_p':
            return 'Autor: {} ({})'
        elif type == 'link':
            return 'Link: {}'
        elif type == 'source':
            return 'Desde: {}'
    elif lang == 'it':
        if type == 'votes':
            return '[Voti +: {}/-: {}]'
        elif type == 'desc_attach':
            return 'L\' idea e stata inviata da {} per l\'iniziativa {}'
        elif type == 'author':
            return 'Autore: {}'
        elif type == 'author_p':
            return 'Autore: {} ({})'
        elif type == 'link':
            return 'Link: {}'
        elif type == 'source':
            return 'Da: {}'
    else:
        # default: lang == 'en'
        if type == 'votes':
            return '[Votes +: {}/-: {}]'
        elif type == 'desc_attach':
            return 'Idea contributed by {} in the initiative {}'
        elif type == 'author':
            return 'Author: {}'
        elif type == 'author_p':
            return 'Author: {} ({})'
        elif type == 'link':
            return 'Link: {}'
        elif type == 'source':
            return 'From: {}'


def _do_publish_idea_sn(sn_app, idea, text_to_sn, mode, app_user=None):
    if mode and mode == 'batch':
        uri = '{}/feed'.format(sn_app.community.external_id)
        params = {'msg': text_to_sn, 'access_token': app_user.access_token, 'uri': uri}
        return call_social_network_api(sn_app.connector, 'create_batch_request', params)
    try:
        params = {'app': sn_app, 'message': text_to_sn, 'app_user': app_user}
        new_post = call_social_network_api(sn_app.connector, 'publish_post', params)
        idea.sn_id = new_post['id']
        idea.is_new = False
        idea.exist_sn = True
        idea.sync = True
        idea.save()
    except Exception as e:
        if 'blocked' in e.message:
            sn_app.blocked = timezone.make_aware(datetime.now(), timezone.get_default_timezone())
            sn_app.save()
        raise AppError(e)


def _do_edit_idea_sn(sn_app, idea, text_to_sn, app_user=None):
    try:
        params = {'app': sn_app, 'id_post': idea.sn_id, 'new_message': text_to_sn, 'app_user': app_user}
        call_social_network_api(sn_app.connector, 'edit_post', params)
        idea.has_changed = False
        idea.exist_sn = True
        idea.sync = True
        idea.save()
    except Exception as e:
        if 'blocked' in e.message:
            sn_app.blocked = timezone.make_aware(datetime.now(), timezone.get_default_timezone())
            sn_app.save()
        raise AppError(e)


def is_user_community_member(sn_app, app_user):
    app_community = sn_app.community
    for reg_member in app_community.members.all():
        if reg_member == app_user:
            return True
    params = {'app': sn_app, 'group_id': sn_app.community.external_id}
    members = call_social_network_api(sn_app.connector, 'get_community_member_list', params)
    for member in members:
        if member == app_user.external_id:
            app_community.members.add(app_user)
            return True
    return False


def publish_idea_sn(idea, sn_app, mode=None):
    initiative = idea.initiative
    LOGO_IDEASCALE_VIA = 'https://dl.dropboxusercontent.com/u/55956367/via_is_white.png'
    template_idea_header_sn = '----------------\n' \
                              '{}\n'
    template_idea_header_sn += _get_str_language(initiative.language, 'votes') + '\n'
    template_idea_header_sn += '----------------\n\n'
    template_idea_body_sn = '{}\n\n' \
                            '#{}\n\n' \
                            '----------------\n'
    template_idea_sn = template_idea_header_sn + template_idea_body_sn
    template_idea_sn += _get_str_language(initiative.language, 'source') + '\n'
    template_idea_sn += _get_str_language(initiative.language, 'link')
    desc_attachment = _get_str_language(initiative.language, 'desc_attach')

    text_uf8 = convert_to_utf8_str(idea.text)
    author_name_utf8 = convert_to_utf8_str(idea.author.screen_name)
    platform_name_utf8 = convert_to_utf8_str(idea.source_consultation.name.title())
    campaign = idea.campaign
    ini_hashtag = initiative.hashtag
    cam_hashtag = campaign.hashtag
    # TODO: New text should be bounded by the social network's text length restriction
    if idea.is_new:
        title_utf8 = convert_to_utf8_str(idea.title)
        text_to_sn = template_idea_sn.format(title_utf8, idea.positive_votes, idea.negative_votes,
                                             text_uf8, cam_hashtag.lower(), platform_name_utf8, idea.url)
        if sn_app.community.type == 'page':
            return _do_publish_idea_sn(sn_app, idea, text_to_sn, mode)
        else:
            if not _user_can_publish(idea, author_name_utf8, sn_app, 'idea'):
                return None
            else:
                #attachment = {
                #    'name': title_utf8,
                #    'link':  idea.url,
                #    'caption': initiative.name.upper(),
                #    'description': desc_attachment.format(author_name_utf8, initiative.name),
                #    'picture': LOGO_IDEASCALE_VIA
                #}
                # From now, let's don't include the attachment
                app_user = SocialNetworkAppUser.objects.get(email=idea.author.email)
                return _do_publish_idea_sn(sn_app, idea, text_to_sn, mode, app_user)
    elif idea.has_changed:
        title_utf8 = convert_to_utf8_str(idea.title)
        text_to_sn = template_idea_sn.format(title_utf8, idea.positive_votes, idea.negative_votes,
                                             text_uf8, ini_hashtag.lower(), cam_hashtag.lower(),
                                             platform_name_utf8, idea.url)
        if sn_app.community.type == 'page':
            _do_edit_idea_sn(sn_app, idea, text_to_sn)
        else:
            app_user = SocialNetworkAppUser.objects.get(email=idea.author.email)
            if not _user_can_publish(idea, author_name_utf8, sn_app, 'idea'):
                return None
            else:
                _do_edit_idea_sn(sn_app, idea, text_to_sn, app_user)


def _do_publish_comment_sn(sn_app, comment, parent, text_to_sn, mode, type='post', app_user=None):
    if mode and mode == 'batch':
        uri = '{}/comments'.format(parent.sn_id)
        params = {'msg': text_to_sn, 'uri': uri,'access_token': app_user.access_token}
        return call_social_network_api(sn_app.connector, 'create_batch_request', params)
    try:
        if type == 'post':
            params = {'app': sn_app, 'id_post': parent.sn_id, 'message': text_to_sn,'app_user': app_user}
            new_comment = call_social_network_api(sn_app.connector, 'comment_post', params)
        else:
            params = {'app': sn_app, 'id_comment': parent.sn_id, 'message': text_to_sn,'app_user': app_user}
            new_comment = call_social_network_api(sn_app.connector, 'comment_comment', params)
        comment.sn_id = new_comment['id']
        comment.is_new = False
        comment.exist_sn = True
        comment.sync = True
        comment.save()
    except Exception as e:
        if 'blocked' in e.message:
            sn_app.blocked = timezone.make_aware(datetime.now(), timezone.get_default_timezone())
            sn_app.save()
        raise AppError(e)


def _do_edit_comment_sn(sn_app, comment, text_to_sn, app_user=None):
    try:
        params = {'app': sn_app, 'id_comment': comment.sn_id, 'message': text_to_sn,'app_user': app_user}
        call_social_network_api(sn_app.connector, 'edit_comment', params)
        comment.has_changed = False
        comment.exist_sn = True
        comment.sync = True
        comment.save()
    except Exception as e:
        if 'blocked' in e.message:
            sn_app.blocked = timezone.make_aware(datetime.now(), timezone.get_default_timezone())
            sn_app.save()
            raise AppError(e)


def publish_comment_sn(comment, sn_app, mode=None):
    initiative = comment.initiative
    template_comment_sn = '{}\n\n----\n'
    template_comment_sn += _get_str_language(initiative.language, 'votes') + '\n'
    template_comment_sn += _get_str_language(initiative.language, 'source')

    text_uf8 = convert_to_utf8_str(comment.text)
    author_name_utf8 = convert_to_utf8_str(comment.author.screen_name)
    if comment.is_new:
        text_to_sn = template_comment_sn.format(text_uf8, comment.positive_votes, comment.negative_votes,
                                                comment.source_consultation.name)
        if sn_app.community.type == 'page':
            try:
                if comment.parent == 'idea':
                    parent = Idea.objects.get(id=comment.parent_idea.id)
                    if parent.exist_sn:
                        return _do_publish_comment_sn(sn_app, comment, parent, text_to_sn, mode, 'post')
                    else:
                        # If the parent does not exist on the social network, ignore the content
                        return None
                elif comment.parent == 'comment':
                    parent = Comment.objects.get(id=comment.parent_comment.id)
                    if parent.exist_sn:
                        return _do_publish_comment_sn(sn_app, comment, parent, text_to_sn, mode, 'comment')
                    else:
                        # If the parent does not exist on the social network, ignore the content
                        return None
                else:
                    raise AppError('Unknown the type of the object\'s parent')
            except Exception as e:
                raise AppError('Something went wrong when trying to publish a comment. Reason: {}'.format(e))
        else:
            if not _user_can_publish(comment, author_name_utf8, sn_app, 'comment'):
                return None
            else:
                app_user = SocialNetworkAppUser.objects.get(email=comment.author.email)
                try:
                    if comment.parent == 'idea':
                        parent = Idea.objects.get(id=comment.parent_idea.id)
                        if parent.exist_sn:
                            return _do_publish_comment_sn(sn_app, comment, parent, text_to_sn, mode,
                                                          'post', app_user)
                        else:
                            return None
                    elif comment.parent == 'comment':
                        parent = Comment.objects.get(id=comment.parent_comment.id)
                        if parent.exist_sn:
                            return _do_publish_comment_sn(sn_app, comment, parent, text_to_sn, mode,
                                                          'comment', app_user)
                        else:
                            return None
                    else:
                        raise AppError('Unknown the type of the object\'s parent')
                except Exception as e:
                    raise AppError('Something went wrong when trying to publish a comment. '
                                   'Reason: {}'.format(e))
    elif comment.has_changed:
        text_to_sn = template_comment_sn.format(text_uf8, comment.positive_votes, comment.negative_votes,
                                                comment.source_consultation.name)
        if sn_app.community.type == 'page':
            _do_edit_comment_sn(sn_app, comment, text_to_sn)
        else:
            app_user = SocialNetworkAppUser.objects.get(email=comment.author.email)
            if not _user_can_publish(comment, author_name_utf8, sn_app, 'comment'):
                return None
            else:
                _do_edit_comment_sn(sn_app, comment, text_to_sn, app_user)


def _prepare_email_msg(content, author_name_utf8, type_content, snapp, type_email):
    if type_content == 'idea':
        t_content = _('idea')
    else:
        t_content = _('comment')
    ctx = {
        'author': author_name_utf8,
        'initiative_name': content.initiative.name,
        'group_url': snapp.community.url,
        'type_content': t_content
    }
    if type_email == 'login_app':
        html_msg = get_template('app/email/email_login_app.html').render(Context(ctx))
        txt_msg = render_to_string('app/email/email_login_app.html', ctx)
    elif type_email == 'authorize_writing':
        html_msg = get_template('app/email/email_writing_perm.html').render(Context(ctx))
        txt_msg = render_to_string('app/email/email_writing_perm.txt', ctx)
    elif type_email == 'join_group':
        html_msg = get_template('app/email/email_join_group.html').render(Context(ctx))
        txt_msg = render_to_string('app/email/email_join_group.txt', ctx)
    else:
        logger.warning('Unknown type of email notification. Message could not be sent')
        return None
    return {'html': html_msg, 'txt': txt_msg}


def _send_notification_email(content, author_name_utf8, snapp, type_content, type_email, language):
        activate(language)
        to_email = [content.author.email]
        from_email = 'Social Ideation App <hola@social-ideation.com>'
        subject = _('Socialize your contribution!')
        msgs = _prepare_email_msg(content, author_name_utf8, type_content, snapp, type_email)
        if msgs:
            email = EmailMessage(subject, msgs['html'], to=to_email, from_email=from_email)
            email.content_subtype = 'html'
            email.send(fail_silently=True)
        deactivate()
        return msgs


def _noti_email_already_sent(author):
    if author.payload:
        author_payload = json.loads(author.payload)
        if 'notification_email' in author_payload.keys():
            return author_payload['notification_email']
        else:
            return False
    else:
        return False


def _update_author_payload(author, value):
    author.payload = json.dumps(value)
    author.save()


def _is_new_content(content, type_content):
    if type_content == 'idea' or type_content == 'comment':
        now = timezone.make_aware(datetime.now(), timezone.get_default_timezone())
        diff = now - content.datetime
        return (diff.total_seconds()/60) <= 60  # A content is 'new' if it was created within the last hour
    else:
        return False


def _user_can_publish(content, author_name_utf8, sn_app, type_content):
    if not content.author.email:
        logger.info('The author of the {} (user: {}) has not provided an email address, therefore '
                    'his/her credentials to publish the {} on behalf of him/her on the social network '
                    'cannot be found'.
                    format(type_content,
                           content.author.email if content.author.email else author_name_utf8),
                           type_content)
        return False
    else:
        initiative = content.initiative
        ini_language = initiative.language
        if not SocialNetworkAppUser.objects.filter(email=content.author.email).exists():
            log_msg = 'It seems the user {} has not logged into the app, his/her {} ' \
                      'cannot be published in the initiative\'s group' \
                      .format(content.author.email if content.author.email else author_name_utf8,
                              type_content)
            if initiative.notification_emails and \
               not _noti_email_already_sent(content.author) and \
               _is_new_content(content, type_content):
                ret = _send_notification_email(content, author_name_utf8, sn_app, type_content, 'login_app',
                                               ini_language)
                if ret:
                    _update_author_payload(content.author, {'notification_email': True})
                    log_msg += '. A notification email was sent to the author'
                else:
                    log_msg += '. A notification email was tried to send but without success'
            logger.info(log_msg)
            return False
        else:
            app_user = SocialNetworkAppUser.objects.get(email=content.author.email)
            if not app_user.write_permissions:
                log_msg = 'The author {} did\'nt give write permissions, so ' \
                          'his/her {} cannot be published'  \
                          .format(content.author.email if content.author.email else author_name_utf8,
                                  type_content)
                if initiative.notification_emails and \
                   not _noti_email_already_sent(content.author) and \
                   _is_new_content(content, type_content):
                    ret = _send_notification_email(content, author_name_utf8, sn_app, type_content, 'authorize_writing',
                                                   ini_language)
                    if ret:
                        _update_author_payload(content.author, {'notification_email': True})
                        log_msg += '. A notification email was sent to the author'
                    else:
                        log_msg += '. A notification email was tried to send but without success'
                logger.info(log_msg)
                return False
            elif not is_user_community_member(sn_app, app_user):
                log_msg = 'The author {} is not member of the initiative\'s group, his/her {} cannot be published'\
                          .format(content.author.email if content.author.email else author_name_utf8, type_content)
                if initiative.notification_emails and \
                   not _noti_email_already_sent(content.author) and \
                   _is_new_content(content, type_content):
                    ret = _send_notification_email(content, author_name_utf8, sn_app, type_content, 'join_group',
                                                   ini_language)
                    if ret:
                        _update_author_payload(content.author, {'notification_email': True})
                        log_msg += '. A notification email was sent to the author'
                    else:
                        log_msg += '. A notification email was tried to send but without success'
                logger.info(log_msg)
                return False
            else:
                return True


def publish_idea_cp(idea):
    initiative = idea.initiative
    template_idea_cp = '{}\n\n----------------\n\n'
    template_idea_cp += _get_str_language(initiative.language, 'author_p')
    template_idea_cp += '\n' + _get_str_language(initiative.language, 'link')
    text_uf8 = convert_to_utf8_str(idea.text)
    author_name_utf8 = convert_to_utf8_str(idea.author.screen_name)
    text_cplatform = remove_hashtags(text_uf8)

    campaign = idea.campaign
    cplatform = initiative.platform
    connector = cplatform.connector
    sn_source = idea.source_social.connector.name
    text_to_cp = template_idea_cp.format(text_cplatform, author_name_utf8, sn_source, idea.url)
    if idea.is_new:
        url_cb = get_url_cb(connector, 'create_idea_cb')
        url = build_request_url(url_cb.url, url_cb.callback, {'initiative_id': initiative.external_id})
        params = {'title': generate_idea_title_from_text(idea.text), 'text': text_to_cp,
                  'campaign_id': campaign.external_id}
        body_param = build_request_body(connector, url_cb.callback, params)
        resp = do_request(connector, url, url_cb.callback.method, body_param)
        new_content = get_json_or_error(connector.name, url_cb.callback, resp)
        idea.cp_id = new_content['id']
        idea.is_new = False
        # From now, don't attach fb icon to the ideas
        # It could introduce some bias by leading the attention of the participants
        # mainly toward the ideas with the icon
        # try:
        #     # Attach img to the new idea
        #     url_cb = get_url_cb(connector, 'attach_file_idea_cb')
        #     url = build_request_url(url_cb.url, url_cb.callback, {'idea_id': idea.cp_id})
        #     params = {'file_str': 'via_fb.png'}
        #     body_param = build_request_body(connector, url_cb.callback, params)
        #     resp = do_request(connector, url, url_cb.callback.method, body_param)
        #     get_json_or_error(connector.name, url_cb.callback, resp)
        # except Exception as e:
        #     logger.warning('An error occurred when trying to attach an image to the new idea. '
        #                    'Reason: {}'.format(e))
    elif idea.has_changed:
        try:
            url_cb = get_url_cb(connector, 'update_idea_cb')
            url = build_request_url(url_cb.url, url_cb.callback, {'idea_id': idea.cp_id})
            params = {'title': generate_idea_title_from_text(idea.text), 'text': text_to_cp,
                      'campaign_id': campaign.external_id}
            body_param = build_request_body(connector, url_cb.callback, params)
            do_request(connector, url, url_cb.callback.method, body_param)
            idea.has_changed = False
        except:
            logger.info('Cannon\'t find the url of the callback to update ideas '
                        'through the API of {}'.format(cplatform.name))
    idea.exist_cp = True
    idea.sync = True
    idea.save()


def publish_comment_cp(comment):
    initiative = comment.initiative
    template_comment_cp = '{}\n'
    template_comment_cp += _get_str_language(initiative.language, 'author_p')

    text_uf8 = convert_to_utf8_str(comment.text)
    author_name_utf8 = convert_to_utf8_str(comment.author.screen_name)
    text_cplatform = remove_hashtags(text_uf8)

    sn_source = comment.source_social.connector.name
    cplatform = initiative.platform
    connector = cplatform.connector
    text_to_cp = template_comment_cp.format(text_cplatform, author_name_utf8, sn_source)
    params = {'text': text_to_cp}
    if comment.is_new:
        if comment.parent == 'idea':
            url_cb = get_url_cb(connector, 'create_comment_idea_cb')
            url = build_request_url(url_cb.url, url_cb.callback, {'idea_id': comment.parent_idea.cp_id})
        elif comment.parent == 'comment':
            url_cb = get_url_cb(connector, 'create_comment_comment_cb')
            url = build_request_url(url_cb.url, url_cb.callback, {'comment_id': comment.parent_comment.cp_id})
        else:
            raise AppError('Unknown the type of the object\'s parent')
        body_param = build_request_body(connector, url_cb.callback, params)
        resp = do_request(connector, url, url_cb.callback.method, body_param)
        new_content = get_json_or_error(connector.name, url_cb.callback, resp)
        comment.cp_id = new_content['id']
        comment.is_new = False
    elif comment.has_changed:
        try:
            url_cb = get_url_cb(connector, 'update_comment_cb')
            url = build_request_url(url_cb.url, url_cb.callback, {'comment_id': comment.cp_id})
            params = {'text': text_to_cp}
            body_param = build_request_body(connector, url_cb.callback, params)
            do_request(connector, url, url_cb.callback.method, body_param)
            comment.has_changed = False
        except:
            logger.info('Cannon\'t find the url of the callback to update comments '
                        'through the API of {}'.format(cplatform.name))
    comment.exist_cp = True
    comment.sync = True
    comment.save()


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
            if initiative.active and initiative.hashtag in hashtags:
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


def _post_authored_by_admin(snapp, post):
    for admin in snapp.community.admins.all():
        if admin.external_id == post['user_info']['id']:
            return True
    return False


def _do_send_notification_comment(snapp, post, msg, admin_user):
    params = {'app': snapp, 'id_post': post['id'], 'message': msg, 'app_user': admin_user}
    try:
        new_comment = call_social_network_api(snapp.connector, 'comment_post', params)
        auto_comment = AutoComment(sn_id=new_comment['id'], author=admin_user, parent_idea=post['id'])
        auto_comment.save()
        return True
    except Exception as e:
        logger.info('The notification comment could not be posted. Reason: {}'.format(e))
        return False


def _post_auto_commented(post):
    auto_comments = AutoComment.objects.all()
    for auto_comment in auto_comments:
        if post['id'] == auto_comment.parent_idea and auto_comment.exist:
            return auto_comment
    return None


def _send_notification_comment(snapp, post, initiative, problem):
    if 'story' in post.keys() and _post_authored_by_admin(snapp, post):
        return
    if _post_auto_commented(post):
        return
    campaigns = initiative.campaign_set.all()
    campaign_hashtags = ''
    campaign_counter = 0
    for campaign in campaigns:
        campaign_counter += 1
        if campaign_counter == len(campaigns):
            campaign_hashtags += '#{}'.format(campaign.hashtag)
        else:
            campaign_hashtags += '#{}, '.format(campaign.hashtag)
    with override(initiative.language):
        if problem == 'missing_hashtag':
            msg = _('Hi {}!, it seems you\'ve tried to submit an idea without specifying the hashtag of the '
                    'campaign. If you\'ve forgotten to include the hashtag, please edit your post '
                    'and add one of the followings: {}. Thanks!')
        else:
            msg = _('Hi {}!, it seems you\'ve tried to submit an idea however the hashtag included in your post '
                    'matches none of the hashtags defined to identify the initiative\'s idea campaigns. '
                    'If you have misspelled the campaign hashtag, please edit the post and correct it using one '
                    'of the followings: {}. Thanks!')
        msg = msg.format(post['user_info']['name'], campaign_hashtags)
        for admin in snapp.community.admins.all():
            # If there are problems sending the notification with the first admin
            # let's try with all of them until having success
            if _do_send_notification_comment(snapp, post, msg, admin):
                break


def save_sn_post(sn_app, post, initiative):
    hashtags = _extract_hashtags(post)
    if len(hashtags) > 0 and initiative:
        campaign = _get_campaign(hashtags, initiative)
        if campaign:
            try:
                filters = {'sn_id': post['id']}
                idea_attrs = {'sn_id': post['id'], 'source': 'social_network', 'datetime': post['datetime'],
                              'title': post['title'], 'text': post['text'], 'url': post['url'],
                              'comments': post['comments'], 'initiative': initiative, 'campaign': campaign,
                              'positive_votes': post['positive_votes'], 'negative_votes': post['negative_votes'],
                              'source_social': sn_app}
                editable_fields = ('title', 'text', 'comments', 'positive_votes', 'negative_votes')
                changeable_fields = ('title', 'text')
                idea = update_or_create_content(sn_app, post, Idea, filters, idea_attrs, editable_fields,
                                                'social_network', changeable_fields)
                # Check if the post has an auto comment, if it has then delete the comment
                auto_comment = _post_auto_commented(post)
                if auto_comment:
                    params = {'app': sn_app, 'id_comment': auto_comment.sn_id, 'app_user': auto_comment.author}
                    try:
                        call_social_network_api(sn_app.connector, 'delete_comment', params)
                        auto_comment.exist = False
                        auto_comment.save()
                    except Exception as e:
                        logger.warning('An error occurred when trying to delete the auto comment placed '
                                       'on the post \'{}\'. Reason: {}'.format(post['text'], e))
                return {'idea': idea, 'initiative': initiative, 'campaign': campaign}
            except Exception as e:
                logger.warning('An error occurred when trying to insert/update the post {} in the db. '
                               'Reason: {}'.format(post, e))
                logger.warning(traceback.format_exc())
        else:
            _send_notification_comment(sn_app, post, initiative, 'wrong_hashtag')
            if 'text' in post.keys():
                logger.info('The post \'{}\' could not be created/updated. Reason: The campaign could not be '
                            'identified from the hashtags.'.format(post['text']))
            else:
                logger.info('A post could not be created/updated. Reason: It seems it does not have hashtags')
    else:
        _send_notification_comment(sn_app, post, initiative, 'missing_hashtag')
        if 'text' in post.keys():
            logger.info('The post \'{}\' could not be created/updated. Reason: It seems it does not have hashtags'.
                        format(post['text']))
        else:
            logger.info('A post could not be created/updated. Reason: It seems it does not have hashtags')
    return None


def _find_initiative(parent_type, parent_id):
    if parent_type == 'idea':
        try:
            return Idea.objects.get(sn_id=parent_id).initiative
        except Idea.DoesNotExist:
            return None
    else:
        try:
            return Comment.objects.get(sn_id=parent_id).initiative
        except Comment.DoesNotExist:
            return None


def save_sn_comment(sn_app, comment):
    try:
        #Ignore auto comments
        AutoComment.objects.get(sn_id=comment['id'])
        return
    except AutoComment.DoesNotExist:
        if comment['parent_type'] == 'post':
            comment.update({'parent_type': 'idea'})
        initiative = _find_initiative(comment['parent_type'], comment['parent_id'])
        if initiative:
            comment = do_create_update_comment(sn_app, initiative, comment, 'social_network')
            return {'comment': comment, 'initiative': initiative}
        else:
            logger.warning('An error occurred when trying to create/update the comment {}. '
                           'Reason: The initiative could not be found'.format(comment))
            return None


def save_sn_vote(sn_app, vote):
    if vote['parent_type'] == 'post':
        vote.update({'user_id': vote['user_info']['id'], 'parent_type': 'idea'})
    else:
        vote.update({'user_id': vote['user_info']['id']})
    initiative = _find_initiative(vote['parent_type'], vote['parent_id'])
    if initiative:
        do_create_update_vote(sn_app, initiative, vote, 'social_network')
    else:
        logger.warning('An error occurred when trying to create the vote {}. '
                       'Reason: The initiative could not be found'.format(vote))
        return None


def delete_post(post_id):
    try:
        idea_obj = Idea.objects.get(cp_id=post_id)
        platform = idea_obj.initiative.platform
        connector = platform.connector
        url_cb = get_url_cb(connector, 'delete_idea_cb')
        url = build_request_url(url_cb.url, url_cb.callback, {'idea_id': idea_obj.cp_id})
        do_request(connector, url, url_cb.callback.method)
        logger.info('The idea {} does not exists anymore and thus it was deleted from {}'.
                     format(idea_obj.id, platform))
        _delete_obj(idea_obj)
        #idea_obj.delete()
    except Idea.DoesNotExist:
        logger.warning('The social network idea (id={}) could not be found in the system'.format(post_id))


def delete_comment(comment_id):
    try:
        comment_obj = Comment.objects.get(cp_id=comment_id)
        platform = comment_obj.initiative.platform
        connector = platform.connector
        url_cb = get_url_cb(connector, 'delete_comment_cb')
        url = build_request_url(url_cb.url, url_cb.callback, {'comment_id': comment_obj.cp_id})
        do_request(connector, url, url_cb.callback.method)
        logger.info('The comment {} does not exists anymore and thus it was deleted from {}'.
                     format(comment_obj.id, platform))
        _delete_obj(comment_obj)
        #comment_obj.delete()
    except Comment.DoesNotExist:
        logger.warning('The social network comment (id={}) could not be found in the system'.format(comment_id))


def delete_vote(vote_id):
    try:
        vote_obj = Vote.objects.filter(sn_id=vote_id)
        _delete_obj(vote_obj)
        #vote_obj.delete()
    except Vote.DoesNotExist:
        logger.warning('The social network vote (id={}) could not be found in the system'.format(vote_id))


def _delete_obj(obj):
    obj.cp_id = None
    obj.sn_id = None
    obj.exist_cp = False
    obj.exist_sn = False
    obj.save()


##
# General synchronization method
#
def invalidate_initiative_content(filters, update_attrs):
    # The invalidation process consist in assuming that all ideas, comments,
    # and votes don't exist anymore. Then as they are obtained from the external
    # platforms they will be marked as still existing
    Idea.objects.filter(**filters).update(**update_attrs)
    Comment.objects.filter(**filters).update(**update_attrs)
    Vote.objects.filter(**filters).update(**update_attrs)


def revalidate_initiative_content(filters, update_attrs):
    # The re-validation process consist in re-validating the ideas, comments,
    # and votes that were invalided before
    Idea.objects.filter(**filters).update(**update_attrs)
    Comment.objects.filter(**filters).update(**update_attrs)
    Vote.objects.filter(**filters).update(**update_attrs)


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
        filters = {'source_consultation': platform, 'exist_cp': True}
    else:
        filters = {'source_social': platform, 'exist_sn': True}
    objs_consolidated += _do_data_consolidation('idea', filters)
    objs_consolidated += _do_data_consolidation('comment', filters)

    return objs_consolidated


def consolidate_app_db():
    for cplatform in ConsultationPlatform.objects.all():
        objs_consolidated = _consolidate_data(cplatform, 'consultation_platform')
        logger.info('{} objects were consolidated in the platform {}'.format(objs_consolidated, cplatform))
    for socialnetwork in SocialNetworkApp.objects.all():
        objs_consolidated = _consolidate_data(socialnetwork, 'social_network')
        logger.info('{} objects were consolidated in the social_network {}'.format(objs_consolidated, socialnetwork))


def _is_social_network_enabled(social_network):
    if not social_network.blocked:
        return True
    else:
        t_now = timezone.make_aware(datetime.now(), timezone.get_default_timezone())
        t_delta = t_now - social_network.blocked
        if t_delta.seconds >= 600:
            # Let's try again if 10 minutes have already passed
            social_network.blocked = None
            social_network.save()
            return True
        else:
            return False


def _do_batch_request(sn_app, batch):
    if len(batch) > 0:
        connector = sn_app.connector
        params = {'app': sn_app, 'batch': batch}
        return call_social_network_api(connector, 'make_batch_request', params)
    else:
        return None


def _process_batch_request(resp_batch_req, objs):
    for i in range(0,len(resp_batch_req)):
        req = resp_batch_req[i]
        obj = objs[i]
        body_json = json.loads(req['body'])
        if req['code'] == 200:
            sn_obj_id = body_json['id']
            if type(sn_obj_id) == type(' '.decode()):
                id = sn_obj_id.encode()
            else:
                id = sn_obj_id
            obj.sn_id = id
            obj.is_new = False
            obj.has_change = False
            obj.exist_sn = True
            obj.sync = True
            obj.save()
        else:
            msg = 'There was an error in doing a request of the batch.'
            if 'error' in body_json.keys():
                if 'type' in body_json['error'].keys():
                    msg += ' Error type: {}.'.format(body_json['error']['type'])
                if 'message' in body_json['error'].keys():
                    msg += ' Reason: {}'.format(body_json['error']['message'])
            logger.warning(msg)


def do_push_content(obj, type, last_obj=None, batch_reqs=None):
    if obj.source == 'consultation_platform':
        # Push object to the initiative's social networks
        for social_network in obj.initiative.social_network.all():
            if _is_social_network_enabled(social_network):
                if type == 'idea':
                    if social_network.batch_requests and obj.is_new:
                        if not social_network.name.lower() in batch_reqs.keys():
                            batch_reqs[social_network.name.lower()] = {'reqs': [], 'objs': []}
                        req = publish_idea_sn(obj, social_network, 'batch')
                        if req:
                            batch_reqs[social_network.name.lower()]['reqs'].\
                                append(req)
                            batch_reqs[social_network.name.lower()]['objs'].append(obj)
                        if len(batch_reqs[social_network.name.lower()]) == social_network.max_batch_requests:
                            ret = _do_batch_request(social_network, batch_reqs[social_network.name.lower()]['reqs'])
                            if ret:
                                _process_batch_request(ret, batch_reqs[social_network.name.lower()]['objs'])
                                batch_reqs[social_network.name.lower()]['reqs'] = []
                                batch_reqs[social_network.name.lower()]['objs'] = []
                        elif last_obj:
                            ret = _do_batch_request(social_network, batch_reqs[social_network.name.lower()]['reqs'])
                            if ret:
                                _process_batch_request(ret, batch_reqs[social_network.name.lower()]['objs'])
                    else:
                        publish_idea_sn(obj, social_network)
                elif type == 'comment':
                    if social_network.batch_requests and obj.is_new:
                        if not social_network.name.lower() in batch_reqs.keys():
                            batch_reqs[social_network.name.lower()] = {'reqs': [], 'objs': []}
                        req = publish_comment_sn(obj, social_network, 'batch')
                        if req:
                            batch_reqs[social_network.name.lower()]['reqs'].\
                                append(req)
                            batch_reqs[social_network.name.lower()]['objs'].append(obj)
                        if len(batch_reqs[social_network.name.lower()]) == social_network.max_batch_requests:
                            ret = _do_batch_request(social_network, batch_reqs[social_network.name.lower()]['reqs'])
                            if ret:
                                _process_batch_request(ret, batch_reqs[social_network.name.lower()]['objs'])
                                batch_reqs[social_network.name.lower()]['reqs'] = []
                                batch_reqs[social_network.name.lower()]['objs'] = []
                        elif last_obj:
                            ret = _do_batch_request(social_network, batch_reqs[social_network.name.lower()]['reqs'])
                            if ret:
                                _process_batch_request(ret, batch_reqs[social_network.name.lower()]['objs'])
                    else:
                        publish_comment_sn(obj, social_network)
                else:
                    logger.info('Objects of type {} are ignored and not synchronized'.format(type))
            else:
                logger.info('Still blocked to post on {}'.format(social_network.name))
        return batch_reqs
    else:
        # Push object to the initiative's consultation_platform
        if type == 'idea':
            publish_idea_cp(obj)
        elif type == 'comment':
            publish_comment_cp(obj)


def do_delete_content(obj, type):
    initiative = obj.initiative
    if not obj.exist_cp and obj.exist_sn:
        # Delete object from the initiative's social networks
        for social_network in initiative.social_network.all():
            connector = social_network.connector
            app_user = SocialNetworkAppUser.objects.filter(email=obj.author.email, snapp=social_network)[0]
            if app_user:
                if type == 'idea':
                    params = {'app': social_network, 'id_post': obj.sn_id, 'app_user': app_user}
                    call_social_network_api(connector, 'delete_post', params)
                    logger.info('The idea {} does not exists anymore and thus it was deleted from {}'.
                                format(obj.id, social_network))
                else:
                    params = {'app': social_network, 'id_comment': obj.sn_id, 'app_user': app_user}
                    call_social_network_api(connector, 'delete_comment', params)
                    logger.info('The comment {} does not exists anymore and thus it was deleted from {}'.
                                format(obj.id, social_network))
        #obj.delete()
        _delete_obj(obj)
    elif not obj.exist_sn and obj.exist_cp:
        # Delete object from the initiative's consultation platform
        if type == 'idea':
            delete_post(obj.cp_id)
        else:
            delete_comment(obj.cp_id)
    else:
        _delete_obj(obj)


##
# Methods to pull content from consultation platform
##

def cud_initiative_votes(platform, initiative):
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
        do_create_update_vote(platform, initiative, vote, 'consultation_platform')


def cud_initiative_comments(platform, initiative):
    # Fetch initiative's comments
    connector = platform.connector
    url_cb = get_url_cb(connector, 'get_comments_cb')
    url = build_request_url(url_cb.url, url_cb.callback, {'initiative_id': initiative.external_id})
    resp = do_request(connector, url, url_cb.callback.method)
    comments = get_json_or_error(connector.name, url_cb.callback, resp)
    delayed_comments = []
    # Iterate over initiative's comments
    for comment in comments:
        comment_obj = do_create_update_comment(platform, initiative, comment, 'consultation_platform')
        if not comment_obj:
            delayed_comments.append(comment)
    for delayed_comment in delayed_comments:
        comment_obj = do_create_update_comment(platform, initiative, delayed_comment, 'consultation_platform')
        if not comment_obj:
            logger.warning('Comment {} couldn\'t be synchronized because its parent {} with id {} couldn\'t be found. '
                           '{}'.format(delayed_comment['id'], delayed_comment['parent_type'],
                                       delayed_comment['parent_id'], delayed_comment['text']))


def cud_initiative_ideas(platform, initiative):
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
        changeable_fields = ('title', 'text', 'positive_votes', 'negative_votes')
        update_or_create_content(platform, idea, Idea, filters, idea_attrs, editable_fields, 'consultation_platform',
                                 changeable_fields)
