import logging
import hashlib
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
            logger.info(req_signature)
            exp_signature = 'sha1=' + hashlib.sha1('sha1='+unicode(request.body)+fb_app.app_secret).hexdigest()
            logger.info(exp_signature)
            req_json = json.loads(request.body)
            if req_signature == exp_signature:
                logger.info(req_json)
                return HttpResponse()
            else:
                logger.info('The received signature does not correspond to the expected one!')
    return HttpResponseForbidden()
