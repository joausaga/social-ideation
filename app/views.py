import datetime
import logging
import hashlib
import hmac
import json
import traceback

from app.models import SocialNetworkApp, SocialNetworkAppUser, Initiative
from app.sync import save_sn_post, publish_idea_cp, save_sn_comment, publish_comment_cp, save_sn_vote, \
                     delete_post, delete_comment, delete_vote
from app.utils import get_timezone_aware_datetime, calculate_token_expiration_time
from connectors.social_network import Facebook
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.translation import activate, ugettext as _


logger = logging.getLogger(__name__)


def _process_post(post_id, update, fb_app, u_datetime):
    template_url_post = 'https://www.facebook.com/{}/posts/{}'

    if not 'message' in update.keys() or not update['message'].strip():
        # Posts without text are ignored
        return None
    url = template_url_post.format(post_id.split('_')[0],post_id.split('_')[1])
    post = {'id': post_id, 'text': update['message'], 'title': '',
            'user_info': {'name': update['sender_name'], 'id': str(update['sender_id'])},
            'url': url, 'datetime': u_datetime, 'positive_votes': 0, 'negative_votes': 0,
            'comments': 0}
    ret_data = save_sn_post(fb_app, post)
    if ret_data: publish_idea_cp(ret_data['idea'])


def _process_comment(comment_id, comment_raw, fb_app, c_datetime):
    if not comment_raw['message'].strip():
        # Comments without text are ignored
        return None
    if comment_raw['post_id'] == comment_raw['parent_id']:
        parent_type = 'post'
    else:
        parent_type = 'comment'
    comment = {'id': comment_id, 'text': comment_raw['message'],
               'user_info': {'name': comment_raw['sender_name'], 'id': str(comment_raw['sender_id'])},
               'datetime': c_datetime, 'positive_votes': 0, 'negative_votes': 0, 'url': None,
               'parent_type': parent_type, 'parent_id': comment_raw['parent_id'], 'comments': 0}
    ret_data = save_sn_comment(fb_app, comment)
    if ret_data: publish_comment_cp(ret_data['comment'])


def _generate_like_id(like_raw):
    return like_raw['parent_id'].split('_')[1]+'_'+str(like_raw['sender_id'])


def _process_like(like_raw, fb_app, l_datetime):
    if like_raw['post_id'] == like_raw['parent_id']:
        parent_type = 'post'
    else:
        parent_type = 'comment'
    like = {'id': _generate_like_id(like_raw),
            'user_info': {'id': str(like_raw['sender_id']), 'name': like_raw['sender_name']},
            'parent_type': parent_type, 'parent_id': like_raw['parent_id'], 'value': 1,
            'datetime': l_datetime}
    save_sn_vote(fb_app, like)


def _process_update(fb_app, update, u_datetime):
    if update['item'] == 'post' or update['item'] == 'share' or update['item'] == 'status':
        post_id = str(update['post_id'])
        if update['verb'] == 'add':
            _process_post(post_id, update, fb_app, u_datetime)
        elif update['verb'] == 'remove':
            delete_post(post_id)
        else:
            logger.info('Action type {} are ignored'.format(update['verb']))
    elif update['item'] == 'comment':
        comment_id = str(update['comment_id'])
        if update['verb'] == 'add':
            _process_comment(comment_id, update, fb_app, u_datetime)
        elif update['verb'] == 'remove':
            delete_comment(comment_id)
        else:
            logger.info('Action type {} are ignored'.format(update['verb']))
    elif update['item'] == 'like':
        if update['verb'] == 'add':
            _process_like(update, fb_app, u_datetime)
        elif update['verb'] == 'remove':
            delete_vote(_generate_like_id(update))
        else:
            logger.info('Action type {} are ignored'.format(update['verb']))
    else:
        # Ignore the rest
        logger.info('Updates of type {} are ignored'.format(update['item']))


def _get_datetime(raw_datetime):
    try:
        dt = datetime.datetime.fromtimestamp(raw_datetime)
        if timezone.is_naive(dt):
            return get_timezone_aware_datetime(dt).isoformat()
        else:
            return dt.isoformat()
    except Exception as e:
        logger.warning('Error when trying to calculate the update datetime. Reason: {}'.format(e))
        logger.warning(traceback.format_exc())
        return None

def _encode_payload(payload):
    try:
        if type(payload) == type(' '.decode()):
            return payload.encode()
        else:
            return payload
    except Exception as e:
        logger.warning('Error when trying to encode a payload. Reason: {}'.format(e))
        logger.warning(traceback.format_exc())
        return None


def _process_post_request(fb_app, exp_signature, payload):
    # Save the current signature
    fb_app.last_real_time_update_sig = str(exp_signature)
    fb_app.save()
    req_json = json.loads(payload)
    req_json = _encode_payload(req_json)
    if req_json['object'] == fb_app.object_real_time_updates:
        entries = req_json['entry']
        for entry in entries:
            if entry['id'] == fb_app.page_id:
                e_datetime = _get_datetime(entry['time'])
                if e_datetime:
                    changes = entry['changes']
                    for change in changes:
                        if change['field'] == fb_app.field_real_time_updates:
                            _process_update(fb_app, change['value'], e_datetime)
                        else:
                            logger.info('Unknown update field. Expected: {}, received: {}'.
                                        format(fb_app.field_real_time_updates, change['field']))
            else:
                logger.info('Unknown page id {}. Update will be ignored'.format(entry['id']))
    else:
        logger.info('Unknown update objects. Expected: {}, received: {}'.
                    format(fb_app.object_real_time_updates, req_json['object']))


def _calculate_signature(app_secret, payload):
    try:
        return 'sha1=' + hmac.new(str(app_secret), msg=unicode(str(payload)), digestmod=hashlib.sha1).hexdigest()
    except Exception as e:
        logger.warning('Signature could not be generated. Reason: {}'.format(e))
        logger.warning(traceback.format_exc())
        return None


def _get_facebook_app():
    apps = SocialNetworkApp.objects.all()
    for app in apps:
        if app.connector.name.lower() == 'facebook':
            return app
    return None

@csrf_exempt
def fb_real_time_updates(request):
    fb_app = _get_facebook_app()
    if fb_app:
        if request.method == 'GET':
            challenge = request.GET.get('hub.challenge')
            token = request.GET.get('hub.verify_token')
            if fb_app.token_real_time_updates == token:
                return HttpResponse(challenge)
        elif request.method == 'POST':
            req_signature = request.META.get('HTTP_X_HUB_SIGNATURE')
            exp_signature = _calculate_signature(fb_app.app_secret, request.body)
            if req_signature == exp_signature and \
               not exp_signature == fb_app.last_real_time_update_sig:
                # I'm comparing the current signature against the last one
                # to discard duplicates that seem to arrive consecutively
                _process_post_request(fb_app, exp_signature, request.body)
                return HttpResponse()
            else:
                logger.info('The received signature does not correspond to the expected one or '
                            'the request is a duplicate')
    return HttpResponseForbidden()


def is_supported_language(language_code):
    supported_languages = dict(settings.LANGUAGES).keys()
    return language_code in supported_languages


def index(request):
    # Detect the default language to show the page
    # If the preferred language is supported, the page will be presented in that language
    # Otherwise english will be chosen
    language_to_render = None

    browser_language_code = request.META.get('HTTP_ACCEPT_LANGUAGE', None)

    logger.info('Languages info: ' + browser_language_code)

    if browser_language_code:
        languages = [language for language in browser_language_code.split(',') if
                     '=' not in language]
        for language in languages:
            language_code = language.split('-')[0]
            if is_supported_language(language_code):
                language_to_render = language_code
                break

    if not language_to_render:
        activate('en')
    else:
        activate(language_to_render)

    logger.info(language_to_render)

    return render(request, 'app/index.html')


def login_fb(request):
    fb_app = _get_facebook_app()

    access_token = request.GET.get('access_token')
    user_id = request.GET.get('user_id')
    ret_token = Facebook.get_long_lived_access_token(fb_app.app_id, fb_app.app_secret,
                                                     access_token)
    try:
        user = SocialNetworkAppUser.objects.get(external_id=user_id)
        user.access_token = ret_token['access_token']
        user.access_token_exp = calculate_token_expiration_time(ret_token['expiration'])
        user.save()
    except SocialNetworkAppUser.DoesNotExist:
        user_fb = Facebook.get_info_user(fb_app, user_id, access_token)
        new_app_user = {'email': user_fb['email'], 'snapp': fb_app, 'access_token': ret_token['access_token'],
                        'access_token_exp': calculate_token_expiration_time(ret_token['expiration']),
                        'external_id': user_id}
        if 'name' in user_fb.keys():
            new_app_user.update({'name': user_fb['name']})
        if 'url' in user_fb.keys():
            new_app_user.update({'url': user_fb['url']})
        user = SocialNetworkAppUser(**new_app_user)
        user.save()

    return redirect('/')


def check_user(request):
    user_id = request.GET.get('user_id')
    try:
        msg_logged = _('Congrats!, You are already logged into')
        msg_group = _('{}group{}').format('<a href="{}" target="_blank"><u>','</u></a>')
        msg_join = _('Join the ')
        msg_ini = _('of the initiative to start participate from Facebook')
        user = SocialNetworkAppUser.objects.get(external_id=user_id)
        # Taking (hardcoded) the first active initiative where the user participate in
        fb_app = user.snapp
        for initiative in fb_app.initiative_set.all():
            if initiative.active:
                msg_group = msg_group.format(initiative.social_network.all()[0].community.url)
                return HttpResponse(msg_logged + ' <b>Social Ideation App</b>. ' + msg_join + msg_group + ' ' + msg_ini)
        return HttpResponse(msg_logged)
    except SocialNetworkAppUser.DoesNotExist:
        return HttpResponse()