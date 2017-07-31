from appcivist import views

from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

re_url = '(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)'

urlpatterns = [
    # ex: /assemblies/
    url(r'^assemblies/$', views.Assemblies.as_view()), 
    # ex: /campaigns/assembly_id
    url(r'^campaigns/(?P<assembly_id>[0-9]+)$', views.Campaigns.as_view()), 
    # ex: /proposals/assembly_id
    url(r'^proposals/(?P<assembly_id>[0-9]+)$', views.Proposals.as_view()), 
    # ex: /proposal/proposal_id
    url(r'^proposal/(?P<proposal_id>[0-9]+)$', views.ProposalDetail.as_view()), 
    # ex: /authors/assembly_id
    url(r'^authors/(?P<assembly_id>[0-9]+)$', views.Authors.as_view()), 
    # ex: /author/user_id
    url(r'^author/(?P<user_id>[0-9]+)$', views.AuthorDetail.as_view()), 
    # ex: /comments/assembly_id
    url(r'^comments/(?P<assembly_id>[0-9]+)$', views.Comments.as_view()),
    # ex: /comments/proposal/proposal_id
    url(r'^comments/proposal/(?P<proposal_id>[0-9]+)$', views.CommentsProposal.as_view()), 
    # ex: /comments/comment/comment_id
    url(r'^comments/comment/(?P<comment_id>[0-9]+)$', views.CommentsComment.as_view()),
    # ex: /comment/comment_id
    url(r'^comment/(?P<comment_id>[0-9]+)$', views.CommentDetail.as_view()),
    # ex: /feedbacks-proposals/assembly_id
    url(r'^feedbacks-proposals/(?P<assembly_id>[0-9]+)$', views.FeedbacksProposals.as_view()),
    # ex: /feedbacks-comments/assembly_id
    url(r'^feedbacks-comments/(?P<assembly_id>[0-9]+)$', views.FeedbacksComments.as_view()),
    # ex: /vote/vote_id
    url(r'^feedback/(?P<feedback_id>[0-9]+)$', views.FeedbackDetail.as_view()),
    # ex: /feedbacks/proposal/idea_id
    url(r'^feedbacks/proposal/(?P<proposal_id>[0-9]+)$', views.FeedbacksProposal.as_view()),
    # ex: /feedbacks/comment/comment_id
    url(r'^feedbacks/comment/(?P<comment_id>[0-9]+)$', views.FeedbacksComment.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)