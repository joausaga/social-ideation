import datetime
import logging
import hashlib
import hmac
import json

from app.models import SocialNetworkApp
from app.sync import save_sn_post, publish_idea_cp, save_sn_comment, publish_comment_cp, save_sn_vote, \
                     delete_post, delete_comment, delete_vote
from app.utils import get_timezone_aware_datetime
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone


logger = logging.getLogger(__name__)


def _process_post(post_id, update, fb_app, u_datetime):
    template_url_post = 'https://www.facebook.com/{}/posts/{}'

    if not 'message' in update.keys() or not update['message'].strip():
        # Posts without text are ignored
        return None
    url = template_url_post.format(post_id.split('_')[0],post_id.split('_')[1])
    post = {'id': post_id, 'text': update['message'], 'title': '',
            'user_info': {'name': update['sender_name'], 'id': update['sender_id']},
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
               'user_info': {'name': comment_raw['sender_name'], 'id': comment_raw['sender_id']},
               'datetime': c_datetime, 'positive_votes': 0, 'negative_votes': 0, 'url': None,
               'parent_type': parent_type, 'parent_id': comment_raw['parent_id'], 'comments': 0}
    ret_data = save_sn_comment(fb_app, comment)
    if ret_data: publish_comment_cp(ret_data['comment'])


def _generate_like_id(like_raw):
    return like_raw['parent_id'].split('_')[1]+'_'+like_raw['sender_id']


def _process_like(like_raw, fb_app, l_datetime):
    if like_raw['post_id'] == like_raw['parent_id']:
        parent_type = 'post'
    else:
        parent_type = 'comment'

    like = {'id': _generate_like_id(like_raw),
            'user_info': {'id': like_raw['sender_id'], 'name': like_raw['sender_name']},
            'parent_type': parent_type, 'parent_id': like_raw['parent_id'], 'value': 1,
            'datetime': l_datetime}
    save_sn_vote(fb_app, like)


def _process_update(fb_app, update, u_datetime):
    if update['item'] == 'post':
        post_id = update['post_id']
        if update['verb'] == 'add':
            _process_post(post_id, update, fb_app, u_datetime)
        elif update['verb'] == 'remove':
            delete_post(post_id)
        else:
            pass # Ignore other (e.g., hide)
    elif update['item'] == 'comment':
        comment_id = update['comment_id']
        if update['verb'] == 'add':
            _process_comment(comment_id, update, fb_app, u_datetime)
        elif update['verb'] == 'remove':
            delete_comment(comment_id)
        else:
            pass # Ignore other (e.g., hide)
    elif update['item'] == 'like':
        if update['verb'] == 'add':
            _process_like(update, fb_app, u_datetime)
        elif update['verb'] == 'remove':
            delete_vote(_generate_like_id(update))
        else:
            pass # Ignore other
    else:
        pass # Ignore (e.g., status)


def _get_datetime(raw_datetime):
    dt = datetime.datetime.fromtimestamp(raw_datetime)
    if timezone.is_naive(dt):
        return get_timezone_aware_datetime(dt).isoformat()
    else:
        return dt.isoformat()


def _process_post_request(fb_app, exp_signature, payload):
    # Save the current signature
    fb_app.last_real_time_update_sig = exp_signature
    fb_app.save()
    req_json = json.loads(payload)
    logger.info(req_json)
    if req_json['object'] == fb_app.object_real_time_updates:
        entries = req_json['entry']
        for entry in entries:
            if entry['id'] == fb_app.page_id:
                e_datetime = _get_datetime(entry['time'])
                changes = entry['changes']
                for change in changes:
                    if change['field'] == fb_app.field_real_time_updates:
                        _process_update(fb_app, change['value'], e_datetime)


def _calculate_signature(app_secret, payload):
    logger.info('hi!')
    sig = 'sha1=' + hmac.new(app_secret, msg=unicode(payload), digestmod=hashlib.sha1).hexdigest()
    logger.info(sig)
    return sig


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
            logger.info(request.body)
            req_signature = request.META.get('HTTP_X_HUB_SIGNATURE')
            exp_signature = _calculate_signature(fb_app.app_secret,request.body)
            logger.info(exp_signature)
            logger.info(fb_app.last_real_time_update_sig)
            if req_signature == exp_signature and \
               not exp_signature == fb_app.last_real_time_update_sig:
                logger.info('Valid request!')
                # I'm comparing the current signature against the last one
                # to discard duplicates that seem to arrive consecutively
                _process_post_request(fb_app, exp_signature, request.body)
                return HttpResponse()
            else:
                logger.info('The received signature does not correspond to the expected one!')
    return HttpResponseForbidden()
