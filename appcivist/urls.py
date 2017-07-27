from appcivist import views

from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

re_url = '(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)'

urlpatterns = [
    # ex: /testing-params/
    # url(r'^testing-params/$', views.TestingParams.as_view()),
    # ex: /initiatives/
    url(r'^assemblies/$', views.Assemblies.as_view()), #TESTED
    # ex: /campaigns/initiative_id
    url(r'^campaigns/(?P<assembly_id>[0-9]+)$', views.Campaigns.as_view()), #TESTED
    # ex: /ideas/initiative_id
    url(r'^proposals/(?P<assembly_id>[0-9]+)$', views.Proposals.as_view()), #TESTED
    # ex: /idea/idea_id
    url(r'^proposal/(?P<proposal_id>[0-9]+)$', views.ProposalDetail.as_view()), #TESTED
    # ex: /idea/attach-file/idea_id
    # url(r'^idea/attach-file/(?P<idea_id>[0-9]+)$', views.IdeaAttachFile.as_view()),
    # ex: /authors/initiative_id
    url(r'^authors/(?P<assembly_id>[0-9]+)$', views.Authors.as_view()), #TESTED
    # ex: /author/user_id
    url(r'^author/(?P<user_id>[0-9]+)$', views.AuthorDetail.as_view()), #TESTED
    # ex: /comments/initiative_id
    url(r'^comments/(?P<assembly_id>[0-9]+)$', views.Comments.as_view()),
    # ex: /comments/idea/idea_id
    url(r'^comments/proposal/(?P<proposal_id>[0-9]+)$', views.CommentsProposal.as_view()), #TESTED
    # ex: /comments/comment/comment_id
    url(r'^comments/comment/(?P<comment_id>[0-9]+)$', views.CommentsComment.as_view()),
    # ex: /comment/comment_id
    url(r'^comment/(?P<comment_id>[0-9]+)$', views.CommentDetail.as_view()),
    # ex: /votes-ideas/initiative_id
    url(r'^feedbacks-proposals/(?P<assembly_id>[0-9]+)$', views.FeedbacksProposals.as_view()),
    # ex: /votes-comments/initiative_id
    url(r'^feedbacks-comments/(?P<assembly_id>[0-9]+)$', views.FeedbacksComments.as_view()),
    # ex: /vote/vote_id
    url(r'^feedback/(?P<feedback_id>[0-9]+)$', views.FeedbackDetail.as_view()),
    # ex: /votes/idea/idea_id
    url(r'^feedbacks/proposal/(?P<proposal_id>[0-9]+)$', views.FeedbacksProposal.as_view()),
    # ex: /votes/comment/comment_id
    url(r'^feedbacks/comment/(?P<comment_id>[0-9]+)$', views.FeedbacksComment.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)