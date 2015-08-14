from django.http import HttpResponse, HttpResponseForbidden
from app.models import SocialNetwork


def fb_real_time_updates(request):
    if request.method == 'GET':
        challenge = request.GET.get('hub.challenge')
        token = request.GET.get('hub.verify_token')
        fb = SocialNetwork.objects.get(name__contains='facebook')
        if fb.token_real_time_updates == token:
            print 'Token received!'
            return HttpResponse(challenge)
        else:
            print 'Token is not the same!'
            return HttpResponseForbidden()
    elif request.method == 'POST':
        print 'There is an update!'
        return HttpResponse()
    else:
        return HttpResponseForbidden()
