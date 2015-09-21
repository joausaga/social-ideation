from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    # Examples:
    url(r'^$', include('app.urls', namespace="app")),
    url(r'^connectors/', include('connectors.urls', namespace="connectors")),
    url(r'^ideascale/', include('ideascale.urls', namespace="ideascale")),
    url(r'^app/', include('app.urls', namespace="app")),
    url(r'^admin/', include(admin.site.urls)),
]
