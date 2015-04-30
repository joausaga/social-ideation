from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    # Examples:
    # url(r'^$', 'social_ideation.views.home', name='home'),
    url(r'^connectors/', include('connectors.urls', namespace="connectors")),
    url(r'^ideascale/', include('ideascale.urls', namespace="ideascale")),
    url(r'^admin/', include(admin.site.urls)),
]
