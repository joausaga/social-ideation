import datetime
import logging
import hashlib
import hmac
import json
import traceback

from app.models import SocialNetworkApp, SocialNetworkAppUser, Initiative, Idea, Campaign
from app.sync import save_sn_post, publish_idea_cp, save_sn_comment, publish_comment_cp, save_sn_vote, \
                     delete_post, delete_comment, delete_vote, is_user_community_member
from app.utils import get_timezone_aware_datetime, calculate_token_expiration_time, get_url_cb, \
                      build_request_url, build_request_body, do_request, get_json_or_error
from connectors.social_network import Facebook
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.translation import activate, ugettext as _

#from .forms import SignInForm
#from social_ideation.settings import URL_1, URL_2

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

# cambiar initiative_url por site_url
def get_initiative_info(initiative_url=None):
    # Hardcoded get the first active initiative and the
    # url of the community associated to the first social network
    # where it is executed
    if initiative_url:
        initiative = Initiative.objects.get(active=True, url=initiative_url)
    else:
        initiative = Initiative.objects.filter(active=True)[0]
    return {'initiative_name': initiative.name, 'initiative_url': initiative.url,
            'fb_group_url': initiative.social_network.all()[0].community.url, 
             'site_url': initiative.site_url}


def _get_recent_ideas (n_ideas, initiative_url):
    ideas = Idea.objects.all().filter(initiative__url = initiative_url).exclude(sn_id=None, cp_id=None)
    for idea in ideas:
        other_positive = int(idea.payload.split(',')[0].split('=')[1])
        idea.positive_votes = idea.positive_votes + other_positive
    recent_ideas = sorted(ideas, key=lambda x: x.datetime, reverse=True)[0:n_ideas]
    for idea in recent_ideas:
        if idea.title == '' or idea.title == None:
            idea.title = ' '.join(idea.text.split()[:5])
        idea.text = idea.text[0:175] + '...'
    return recent_ideas

def _get_top_ideas (n_ideas, initiative_url):
    ideas = Idea.objects.all().filter(initiative__url = initiative_url).exclude(sn_id=None, cp_id=None)
    for idea in ideas:
        other_positive = int(idea.payload.split(',')[0].split('=')[1])
        idea.positive_votes = idea.positive_votes + other_positive
    top_ideas = sorted(ideas, key=lambda x: x.positive_votes, reverse=True)[0:n_ideas]
    for idea in top_ideas:
        if idea.title == '' or idea.title == None:
            idea.title = ' '.join(idea.text.split()[:5])
        idea.text = idea.text[0:175] + '...'
    return top_ideas

def _get_campaigns (initiative_url):
    #campaigns = Campaign.objects.all() #Hardcoded for the first initiative
    campaigns = Campaign.objects.filter(initiative__url = initiative_url)
    return campaigns


def index(request):
    # Detect the default language to show the page
    # If the preferred language is supported, the page will be presented in that language
    # Otherwise english will be chosen
    language_to_render = None

    browser_language_code = request.META.get('HTTP_ACCEPT_LANGUAGE', None)

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
    # TODO, cambiar URL1 por la url del request. User request.get_host()
    context = get_initiative_info()
    # form = SignInForm()
    # context['form'] = form
    context['top'] = _get_top_ideas(3, context['initiative_url'])
    context['recent'] = _get_recent_ideas(3, context['initiative_url'])
    context['campaigns'] = _get_campaigns(context['initiative_url'])
    return render(request, 'app/index.html', context)

# def index_v1(request):
#     # Detect the default language to show the page
#     # If the preferred language is supported, the page will be presented in that language
#     # Otherwise english will be chosen
#     language_to_render = None

#     browser_language_code = request.META.get('HTTP_ACCEPT_LANGUAGE', None)

#     if browser_language_code:
#         languages = [language for language in browser_language_code.split(',') if
#                      '=' not in language]
#         for language in languages:
#             language_code = language.split('-')[0]
#             if is_supported_language(language_code):
#                 language_to_render = language_code
#                 break

#     if not language_to_render:
#         activate('en')
#     else:
#         activate(language_to_render)

#     context = get_initiative_info(URL_1)
#     form = SignInForm()
#     context['form'] = form
#     context['top'] = _get_top_ideas(3, context['initiative_url'])
#     context['recent'] = _get_recent_ideas(3, context['initiative_url'])
#     context['campaigns'] = _get_campaigns(context['initiative_url'])
#     return render(request, 'app/index-v1.html', context)


# def index_v2(request):
#     # Detect the default language to show the page
#     # If the preferred language is supported, the page will be presented in that language
#     # Otherwise english will be chosen
#     language_to_render = None

#     browser_language_code = request.META.get('HTTP_ACCEPT_LANGUAGE', None)

#     if browser_language_code:
#         languages = [language for language in browser_language_code.split(',') if
#                      '=' not in language]
#         for language in languages:
#             language_code = language.split('-')[0]
#             if is_supported_language(language_code):
#                 language_to_render = language_code
#                 break

#     if not language_to_render:
#         activate('en')
#     else:
#         activate(language_to_render)

#     context = get_initiative_info(URL_2)
#     form = SignInForm()
#     context['form'] = form
#     context['top'] = _get_top_ideas(3, context['initiative_url'])
#     context['recent'] = _get_recent_ideas(3, context['initiative_url'])
#     context['campaigns'] = _get_campaigns(context['initiative_url'])
#     return render(request, 'app/index-v2.html', context)


# def register(request):
#     language_to_render = None

#     browser_language_code = request.META.get('HTTP_ACCEPT_LANGUAGE', None)

#     if browser_language_code:
#         languages = [language for language in browser_language_code.split(',') if
#                      '=' not in language]
#         for language in languages:
#             language_code = language.split('-')[0]
#             if is_supported_language(language_code):
#                 language_to_render = language_code
#                 break

#     if not language_to_render:
#         activate('en')
#     else:
#         activate(language_to_render)

#     context = get_initiative_info()
#     form = SignInForm()
#     context['form'] = form
#     return render(request, 'app/register.html', context)

# def register_v1(request):
#     language_to_render = None

#     browser_language_code = request.META.get('HTTP_ACCEPT_LANGUAGE', None)

#     if browser_language_code:
#         languages = [language for language in browser_language_code.split(',') if
#                      '=' not in language]
#         for language in languages:
#             language_code = language.split('-')[0]
#             if is_supported_language(language_code):
#                 language_to_render = language_code
#                 break

#     if not language_to_render:
#         activate('en')
#     else:
#         activate(language_to_render)

#     context = get_initiative_info()
#     form = SignInForm()
#     context['form'] = form
#     return render(request, 'app/register-v1.html', context)


# TODO change this function name. This is the new index redirect
# def process_login(request):
#     context = {}
#     # We remove the htt:// from the urls to do comparissons with and withouy www. in the beggining
#     try:
#         context['site1'] = get_initiative_info(URL_1)['site_url'].replace('http://', '')
#     except:
#         pass
#     try:
#         context['site2'] = get_initiative_info(URL_2)['site_url'].replace('http://', '')
#     except:
#         pass
#     return render(request, 'app/index.html', context)

def _get_initiative_fb_app(initiative_url):
    initiative = Initiative.objects.get(url=initiative_url)
    for snapp in initiative.social_network.all():
        connector = snapp.connector
        if connector.name.lower() == 'facebook':  # Take the Facebook app used to execute the initiative on this sn
            return snapp
    return None


def _save_user(user_id, access_token, initiative_url, type_permission):
    fb_app = _get_initiative_fb_app(initiative_url)
    if fb_app:
        ret_token = Facebook.get_long_lived_access_token(fb_app.app_id, fb_app.app_secret,
                                                         access_token)
        try:
            user = SocialNetworkAppUser.objects.get(external_id=user_id, snapp=fb_app)
            user.access_token = ret_token['access_token']
            user.access_token_exp = calculate_token_expiration_time(ret_token['expiration'])
            if type_permission == 'write':
                user.write_permissions = True
            else:
                user.read_permissions = True
            user.save()
            #############################################################################
            #try:
            #    participa_user = ParticipaUser.objects.get(email=demo_data['email'])
            #except ParticipaUser.DoesNotExist:
            #    participa_user = ParticipaUser(**demo_data)
            #    participa_user.save()
            #    user.participa_user = participa_user
            #    user.save()
            #############################################################################

        except SocialNetworkAppUser.DoesNotExist:
            user_fb = Facebook.get_info_user(fb_app, user_id, access_token)
            new_app_user = {'email': user_fb['email'].lower(), 'snapp': fb_app, 'access_token': ret_token['access_token'],
                            'access_token_exp': calculate_token_expiration_time(ret_token['expiration']),
                            'external_id': user_id}
            if type_permission == 'write':
                new_app_user.update({'write_permissions': True})
            else:
                new_app_user.update({'read_permissions': True})
            if 'name' in user_fb.keys():
                new_app_user.update({'name': user_fb['name']})
            if 'url' in user_fb.keys():
                new_app_user.update({'url': user_fb['url']})
            user = SocialNetworkAppUser(**new_app_user)
            user.save()
            #############################################################################
            # try:
            #     participa_user = ParticipaUser.objects.get(email=demo_data['email'], initiative__url= initiative_url)
            # except ParticipaUser.DoesNotExist:
            #     demo_data['initiative'] = Initiative.objects.get(url=initiative_url)
            #     participa_user = ParticipaUser(**demo_data)
            #     participa_user.save()
            # user.participa_user = participa_user
            user.save()
            #############################################################################
    else:
        logger.warning('It could not be found the facebook app used to execute '
                       'the initiative {}'.format(initiative_url))


# def _get_demo_data(request):
#     first_name = request.GET.get('first_name')
#     last_name = request.GET.get('last_name')
#     birthdate = request.GET.get('birthdate')
#     #birthdate = birthdate.split('-')
#     #birthdate = birthdate[2] + '-' + birthdate[1] + '-' + birthdate[0]
#     sex = request.GET.get('sex')
#     email = request.GET.get('email')
#     city = request.GET.get('city')
#     profession = request.GET.get('profession')
#     demo_data = {'first_name':first_name, 'last_name':last_name, 'birthdate': birthdate, 'sex':sex, 'email':email, 'city':city, 'profession':profession}
#     if (first_name!=None and last_name!=None and email!=None):
#         return demo_data
#     else:
#     return None


def login_fb(request):
    access_token = request.GET.get('access_token')
    user_id = request.GET.get('user_id')
    initiative_url = request.GET.get('initiative_url')
    #demo_data = _get_demo_data(request)
    _save_user(user_id, access_token, initiative_url, 'read')
    return redirect('/')
    # if initiative_url == URL_1:
    #     return redirect('/app/v1#askWRperm')
    # elif initiative_url == URL_2:
    #     return redirect('/app/v2#askWRperm')

# def _create_IS_user (initiative_url, demo_data):
#     initiative = Initiative.objects.get(url=initiative_url)
#     cplatform = initiative.platform
#     connector = cplatform.connector
#     url_cb = get_url_cb(connector, 'create_user_cb')
#     url = build_request_url(url_cb.url, url_cb.callback, {'initiative_id': initiative.external_id})
#     params = {'name': demo_data['first_name']+' '+demo_data['last_name'], 'email': demo_data['email']}
#     body_param = build_request_body(connector, url_cb.callback, params)
#     resp = do_request(connector, url, url_cb.callback.method, body_param)
#     user = get_json_or_error(connector.name, url_cb.callback, resp)
#     return user

# def _save_IS_user(initiative_url, demo_data):
#     try:
#         participa_user = ParticipaUser.objects.get(email=demo_data['email'], initiative__url=initiative_url)
#         user = _create_IS_user(initiative_url, demo_data)
#         participa_user.ideascale_id = user['id']
#         participa_user.save()
#     except ParticipaUser.DoesNotExist:    
#         user = _create_IS_user(initiative_url, demo_data)
#         demo_data['ideascale_id'] = user['id']
#         demo_data['initiative'] = Initiative.objects.get(url=initiative_url)
#         participa_user = ParticipaUser(**demo_data)
#         participa_user.save()


# def login_IS(request):
#     initiative_url = request.GET.get('initiative_url')
#     demo_data = _get_demo_data(request)
#     _save_IS_user(initiative_url, demo_data) ## After retrieving the data a new IS_user object should be created and saved
#     # After the new user is created in our DB a register-confirmation mail must be sent through the API
#     # a session value (cookie) should be set here probably to recognize this user.
#     logger.info('26oct ' + str(request.get_full_path()))
#     if initiative_url == URL_1:
#         return redirect("/app/v1#mailSent")
#     elif initiative_url == URL_2:
#         return redirect("/app/v2#mailSent")

def check_user(request): #puede que le agregue otro parametro que me diga si el id es de FB o de IS
    user_id = request.GET.get('user_id')
    initiative_url = request.GET.get('initiative_url')
    fb_app = _get_initiative_fb_app(initiative_url)
    try:
        msg_logged = _('Congrats!, You are already logged into') + ' <b>Social Ideation App</b>. '
        msg_group = _('{}group{}').format('<a href="{}" target="_blank"><u>','</u></a>')
        msg_join = _('Join the ')
        msg_ini = _('of the initiative to start participate from Facebook')
        user = SocialNetworkAppUser.objects.get(external_id=user_id, snapp=fb_app)
        # Taking (hardcoded) the first active initiative where the user participate in
        fb_app = user.snapp
        for initiative in fb_app.initiative_set.all():
            if initiative.active:
                msg_group = msg_group.format(initiative.social_network.all()[0].community.url)
                if not user.read_permissions:
                    return HttpResponse()
                if not user.write_permissions:
                    msg_give_write_perm = _('Please consider allowing the app the permission to post '
                                            'on your behalf inside the Facebook')
                    msg_ini_short = _('of the initiative (step 3 below)')
                    msg = msg_logged + msg_give_write_perm + ' ' + msg_group + ' ' + msg_ini_short
                elif not is_user_community_member(fb_app, user):
                    msg = msg_logged + msg_join + msg_group + ' ' + msg_ini
                else:
                    msg_get_in_group = _('Get into the')
                    msg = msg_logged + msg_get_in_group + ' ' + msg_group + ' ' + msg_ini
                return HttpResponse(msg)
        return HttpResponse(msg_logged)
    except SocialNetworkAppUser.DoesNotExist:
        return HttpResponse()


def write_permissions_fb(request):
    access_token = request.GET.get('access_token')
    user_id = request.GET.get('user_id')
    initiative_url = request.GET.get('initiative_url')
    #demo_data = _get_demo_data(request)
    _save_user(user_id, access_token, initiative_url, 'write')
    return redirect('/')
    # if initiative_url == URL_1:
    #     return redirect("/app/v1#joinFB")
    # elif initiative_url == URL_2:
    #     return redirect("/app/v2#joinFB")
