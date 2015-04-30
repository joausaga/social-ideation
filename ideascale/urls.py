from . import views

from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns


re_url = '(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)'

urlpatterns = [
    # ex: /testing-params/
    url(r'^testing-params/$', views.TestingParams.as_view()),
    # ex: /initiatives/
    url(r'^initiatives/$', views.Initiatives.as_view()),
    # ex: /campaigns/initiative_id
    url(r'^campaigns/(?P<initiative_id>[0-9]+)$', views.Campaigns.as_view()),
    # ex: /ideas/initiative_id
    url(r'^ideas/(?P<initiative_id>[0-9]+)$', views.Ideas.as_view()),
    # ex: /idea/idea_id
    url(r'^idea/(?P<idea_id>[0-9]+)$', views.IdeaDetail.as_view()),
    # ex: /authors/initiative_id
    url(r'^authors/(?P<initiative_id>[0-9]+)$', views.Authors.as_view()),
    # ex: /author/user_id
    url(r'^author/(?P<user_id>[0-9]+)$', views.AuthorDetail.as_view()),
    # ex: /comments/initiative_id
    url(r'^comments/(?P<initiative_id>[0-9]+)$', views.Comments.as_view()),
    # ex: /comments/idea/idea_id
    url(r'^comments/idea/(?P<idea_id>[0-9]+)$', views.CommentsIdea.as_view()),
    # ex: /comments/comment/comment_id
    url(r'^comments/comment/(?P<comment_id>[0-9]+)$', views.CommentsComment.as_view()),
    # ex: /comment/comment_id
    url(r'^comment/(?P<comment_id>[0-9]+)$', views.CommentDetail.as_view()),
    # ex: /votes/initiative_id
    url(r'^votes/(?P<initiative_id>[0-9]+)$', views.Votes.as_view()),
    # ex: /vote/vote_id
    url(r'^vote/(?P<vote_id>[0-9]+)$', views.VoteDetail.as_view()),
    # ex: /votes/idea/idea_id
    url(r'^votes/idea/(?P<idea_id>[0-9]+)$', views.VotesIdea.as_view()),
    # ex: /votes/comment/comment_id
    url(r'^votes/comment/(?P<comment_id>[0-9]+)$', views.VotesComment.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)