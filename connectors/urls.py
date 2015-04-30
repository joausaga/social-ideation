from django.conf.urls import patterns, url
from connectors import views

urlpatterns = patterns('',
    # ex: /connectors/test_connector/1
    url(r'^test_connector/(?P<connector_id>[A-Za-z]+)$', views.test_connector, name='test_connector'),
)
