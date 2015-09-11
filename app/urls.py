from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /app/
    url(r'^$', views.index, name='index'),
    # ex: /app/login_fb
    url(r'^login_fb$', views.login_fb, name='login_fb'),
    # ex: /app/fb_real_time_updates/
    url(r'^fb_real_time_updates/$', views.fb_real_time_updates, name='fb_real_time_updates'),
]
