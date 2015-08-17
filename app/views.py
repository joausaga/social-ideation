import logging
import hashlib
import hmac
import json

from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from app.models import SocialNetworkApp

logger = logging.getLogger(__name__)


def _get_facebook_app():
    apps = SocialNetworkApp.objects.all()
    for app in apps:
        if app.connector.name.lower() == 'facebook':
            return app
    return None


def _valid_request(app_secret, req_signature, payload):
    exp_signature = 'sha1=' + hmac.new(app_secret, msg=unicode(payload), digestmod=hashlib.sha1).hexdigest()
    return exp_signature == req_signature


@csrf_exempt
def fb_real_time_updates(request):
    fb_app = _get_facebook_app()
    if fb_app:
        if request.method == 'GET':
            challenge = request.GET.get('hub.challenge')
            token = request.GET.get('hub.verify_token')
            if fb_app.token_real_time_updates == token:
                logger.info('Token received!')
                return HttpResponse(challenge)
        elif request.method == 'POST':
            logger.info(request.body)
            req_signature = request.META.get('HTTP_X_HUB_SIGNATURE')
            if _valid_request(fb_app.app_secret,req_signature,request.body):
                req_json = json.loads(request.body)
                logger.info(req_json)
                return HttpResponse()
            else:
                logger.info('The received signature does not correspond to the expected one!')
    return HttpResponseForbidden()
