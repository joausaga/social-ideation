import logging

from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from app.models import SocialNetworkApp

logger = logging.getLogger(__name__)

@csrf_exempt
def fb_real_time_updates(request):
    logger.info('Got a request!')
    if request.method == 'GET':
        challenge = request.GET.get('hub.challenge')
        token = request.GET.get('hub.verify_token')
        fb = SocialNetworkApp.objects.get(name__contains='Facebook')
        if fb.token_real_time_updates == token:
            logger.info('Token received!')
            return HttpResponse(challenge)
        else:
            logger.warning('Token is not the same!')
            return HttpResponseForbidden()
    elif request.method == 'POST':
        logger.info('There is an update!')
        return HttpResponse()
    else:
        return HttpResponseForbidden()
