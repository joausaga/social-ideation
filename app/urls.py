from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /fb_real_time_updates/
    url(r'^fb_real_time_updates/$', views.fb_real_time_updates, name='fb_real_time_updates'),
]
