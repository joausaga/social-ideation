from appcivist import views

from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

re_url = '(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)'

urlpatterns = [
    # ex: /assemblies/
    url(r'^assemblies/$', views.Campaigns.as_view()), 
    # ex: /campaigns/initiative_id
    url(r'^campaigns/(?P<initiative_id>[0-9]+)$', views.Themes.as_view()), 
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
    # ex: /feedbacks-ideas/initiative_id
    url(r'^feedbacks-ideas/(?P<initiative_id>[0-9]+)$', views.FeedbacksIdeas.as_view()),
    # ex: /feedbacks-comments/initiative_id
    url(r'^feedbacks-comments/(?P<initiative_id>[0-9]+)$', views.FeedbacksComments.as_view()),
    # ex: /vote/vote_id
    url(r'^feedback/(?P<vote_id>[0-9]+)$', views.FeedbackDetail.as_view()),
    # ex: /feedbacks/idea/idea_id
    url(r'^feedbacks/idea/(?P<idea_id>[0-9]+)$', views.FeedbacksIdea.as_view()),
    # ex: /feedbacks/comment/comment_id
    url(r'^feedbacks/comment/(?P<comment_id>[0-9]+)$', views.FeedbacksComment.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)