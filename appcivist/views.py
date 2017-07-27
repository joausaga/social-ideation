import logging
import os
import six
import sys

from django.shortcuts import render

from dateutil.parser import parse
from datetime import datetime

from django.http import HttpResponse, Http404
from django.utils import timezone

# from ideascaly.auth import AuthNonSSO
# from ideascaly.error import IdeaScalyError
# from ideascaly.api import API

from appcivist.models import Assembly, Author, Campaign, Proposal, Comment, Feedback
from appcivist.serializers import AssemblySerializer, CampaignSerializer, AuthorSerializer, ProposalSerializer, CommentSerializer, FeedbackSerializer

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer

from django.utils.encoding import smart_str, smart_unicode

from appcivist_client import appcivist_api

logger = logging.getLogger(__name__)
# Create your views here.


# ---
# General methods and classes
# ---



def convert_to_utf8_str(arg):
    try:
        return smart_str(arg)
    except:
        # written by Michael Norton (http://docondev.blogspot.com/)
        if isinstance(arg, six.text_type):
            arg = arg.encode('utf-8')
        elif not isinstance(arg, bytes):
            arg = six.text_type(arg).encode('utf-8')
        elif isinstance(arg, bytes):
            arg = arg.decode('utf-8')
        return arg
        #return str(arg)


def _get_timezone_aware_datetime(datetime):
    return timezone.make_aware(datetime, timezone.get_default_timezone())


def get_api_obj(assembly):

    api = appcivist_api()
    api.base_url = assembly.url
    api.session_key = assembly.admin_session_key

    return api


def get_appcivist_data(assembly, api_method, method_params=None, pag_params=None):
    api = get_api_obj(assembly)
    if not method_params:
        objs = getattr(api, api_method)()
    elif method_params:
        objs = getattr(api, api_method)(**method_params)
    return objs


def cru_author(author_id, assembly, author_info=None):
    try:
        author = Author.objects.get(appcivist_id=author_id)
        if author_info:
            author.name = author_info['name']
            if "email" in author_info.keys():
                author.email = author_info["email"]
            author.save()
        return author
    except Author.DoesNotExist:
        if not author_info:
            author_info = get_appcivist_data(assembly, 'get_author_info', {'uid': author_id})
        if "email" in author_info.keys():
            author = Author(appcivist_id=author_info["userId"], name=author_info["name"], email=author_info["email"],
                            assembly=assembly, appcivist_uuid=author_info["uuid"])
        else:
            author = Author(appcivist_id=author_info["userId"], name=author_info["name"], assembly=assembly, appcivist_uuid=author_info["uuid"])
        author.save()
        return author


def cu_campaigns(assembly):
    campaigns_raw = get_appcivist_data(assembly, 'get_campaigns', {'aid': assembly.appcivist_id})
    for campaign_raw in campaigns_raw:
        try:
            campaign = Campaign.objects.get(appcivist_id=campaign_raw["campaignId"])
            campaign.name = campaign_raw["title"]
            campaign.save()
        except Campaign.DoesNotExist:
            campaign = Campaign(appcivist_id=campaign_raw["campaignId"], appcivist_uuid=campaign_raw["uuid"], name=campaign_raw["title"], assembly=assembly, resource_space_id=campaign_raw["resourceSpaceId"], forum_resource_space_id=campaign_raw["forumResourceSpaceId"])
            campaign.save()


def cru_campaign(campaign_id, assembly):
    if campaign_id > 0:
        try:
            return Campaign.objects.get(appcivist_id=campaign_id)
        except Campaign.DoesNotExist:
            cu_campaigns(assembly)
    else:
        cu_campaigns(assembly)
        return Campaign.objects.filter(assembly=assembly)




def cru_proposal(proposal_id, assembly, proposal_obj=None):
    try:
        proposal = Proposal.objects.get(appcivist_id=proposal_id)
        if proposal_obj:
            proposal.title = proposal_obj["title"]
            proposal.text = proposal_obj["text"]
            proposal.positive_votes = proposal_obj["stats"]['ups']
            proposal.negative_votes = proposal_obj["stats"]['downs']
            proposal.comments = proposal_obj["commentCount"]
            proposal.campaign = cru_campaign(proposal_obj["campaignIds"][0], assembly)
        proposal.sync = False
        proposal.save()
        return proposal
    except Proposal.DoesNotExist:
        if not proposal_obj:
            proposal_obj = get_appcivist_data(assembly, 'get_proposal_details', {'coid': proposal_id, 'aid': assembly.appcivist_id})
        author = cru_author(proposal_obj["firstAuthor"]['userId'], assembly, proposal_obj["firstAuthor"])
        campaign_proposal = cru_campaign(proposal_obj["campaignIds"][0], assembly)
        positive_votes = proposal_obj["stats"]['ups']
        negative_votes = proposal_obj["stats"]['downs']
        comments = proposal_obj["commentCount"]
        url = ""
        proposal_ac_dt = datetime.strptime(proposal_obj["creation"].replace(" GMT", ""), "%Y-%m-%d %H:%M %p")
        proposal_dt = _get_timezone_aware_datetime(proposal_ac_dt) if timezone.is_naive(proposal_ac_dt) else proposal_ac_dt
        proposal = Proposal(appcivist_id=proposal_obj["contributionId"], appcivist_uuid=proposal_obj["uuidAsString"] ,title=proposal_obj["title"], text=proposal_obj["text"],
                    datetime=proposal_dt, positive_votes=positive_votes, negative_votes=negative_votes, comments=comments,
                    campaign=campaign_proposal, url=url, user=author, sync=False, resource_space_id=proposal_obj["resourceSpaceId"], forum_resource_space_id=proposal_obj["forumResourceSpaceId"])
        proposal.save()
        return proposal


def get_parent_comment(parent_type, parent_id, assembly):
    if parent_type == 'proposal':
        try:
            return Proposal.objects.get(appcivist_id=parent_id)
        except Proposal.DoesNotExist:
            return cru_proposal(parent_id, assembly)
    else:
        try:
            return Comment.objects.get(appcivist_id=parent_id)
        except Comment.DoesNotExist:
            return cru_comment(parent_id, assembly)

def cru_comment(comment_id, assembly, comment_obj=None):
    try:
        comment = Comment.objects.get(appcivist_id=comment_id)
        if comment_obj:
            comment.text = comment_obj["text"]
            comment.positive_votes = comment_obj["stats"]['ups']
            comment.negative_votes = comment_obj["stats"]['downs']
            comment.comments = comment_obj["commentCount"]
        comment.sync = False
        comment.save()
        return comment
    except Comment.DoesNotExist:
        if not comment_obj:
            comment_obj = get_appcivist_data(assembly, 'get_comment_details', {'coid': comment_id, 'aid': assembly.appcivist_id})
        author = cru_author(comment_obj["firstAuthor"]['userId'], assembly, comment_obj["firstAuthor"])
        positive_votes = comment_obj["stats"]['ups']
        negative_votes = comment_obj["stats"]['downs']
        comments = comment_obj["commentCount"]
        url = ""
        if comment_obj["type"] == "DISCUSSION":
            parent_type = "proposal"
        else:
            parent_type = "comment"
        comment_ac_dt = parse(comment_obj["creation"])
        comment_dt = _get_timezone_aware_datetime(comment_ac_dt) if timezone.is_naive(comment_ac_dt) else comment_ac_dt
        comment = Comment(appcivist_id=comment_obj["contributionId"], appcivist_uuid=comment_obj["uuidAsString"], text=comment_obj["text"],
                          datetime=comment_dt, positive_votes=positive_votes, negative_votes=negative_votes,
                          comments=comments, url=url, user=author,
                          parent_type=parent_type, sync=False, resource_space_id=comment_obj["resourceSpaceId"], forum_resource_space_id=comment_obj["forumResourceSpaceId"])
        parent_id = comment_obj["containingContributionsIds"][0]
        parent = get_parent_comment(parent_type, parent_id, assembly)
        if parent_type == 'proposal':
            comment.parent_proposal = parent
        else:
            comment.parent_comment = parent
        comment.save()
        return comment

def get_parent_feedback(parent_type, parent_id, assembly):
    get_parent_comment(parent_type, parent_id, assembly)

def cru_feedback(feedback_id, assembly, feedback_obj):
    try:
        feedback = Feedback.objects.get(appcivist_id=feedback_id)
        if feedback_obj:
            if feedback_obj["up"]:
                feedback.value = 1
            elif feedback_obj["down"]:
                feedback.value = -1
        feedback.sync = False
        feedback.save()
        return feedback
    except Feedback.DoesNotExist:
        # author_id = vote_obj.authorId if hasattr(vote_obj, 'authorId') else vote_obj.memberId
        author_id = feedback_obj["userId"]
        author = cru_author(author_id, assembly)
        feedback_ac_dt = parse(feedback_obj["creation"])
        feedback_dt = _get_timezone_aware_datetime(feedback_ac_dt) if timezone.is_naive(feedback_ac_dt) else feedback_ac_dt
        
        if feedback_obj["up"]:
            feedback_value = 1
        elif feedback_obj["down"]:
            feedback_value = -1
        feedback_parent_type = feedback_obj["parentType"]
        feedback_parent_id = feedback_obj["contributionId"]
        feedback = Feedback(appcivist_id=feedback_obj["id"], value=feedback_value, datetime=feedback_dt, author=author, sync=False,
                    parent_type=feedback_parent_type)
        if feedback_parent_type == 'proposal':
            feedback.parent_proposal = cru_proposal(feedback_parent_id, assembly)
        else:
            feedback.parent_comment = cru_comment(feedback_parent_id, proposal)
        feedback.save()
        return feedback


def find_obj_id(obj_raw):
    if "id" in obj_raw.keys():
        return int(obj_raw["id"])
    elif "userId" in obj_raw.keys():
        return int(obj_raw["userId"])
    elif "contributionId" in obj_raw.keys():
        return int(obj_raw["contributionId"])
    elif "campaignId" in obj_raw.keys():
        return int(obj_raw["campaignId"])

# ---
# API Meta Classes
# ---

class AppCivistObject(APIView):
    """
    Return the list of objects or create a new one.
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    api_method = ''
    api_method_params = None
    client_attr = ''
    pag_params = None
    iterate = False
    create_obj = None
    queryset = None
    serializer_class = None
    filters = None
    PAGE_SIZE = 25
    PAGE_NUMBER = 0

    def get(self, request, assembly, format=None):
        call_api = True
        try:
            self.queryset.objects.all().update(sync=True)
            while call_api:
                objs_raw = get_appcivist_data(assembly, self.api_method, self.api_method_params, self.pag_params)
                if len(objs_raw) > 0:
                    for obj_raw in objs_raw:
                        # TODO, aca no necesariamente se va a llamar id, puede ser id, o contributionId o CampaignId
                        obj_id = find_obj_id(obj_raw)
                        self.create_obj(obj_id, assembly, obj_raw)
                    if self.pag_params:
                        self.pag_params['page_number'] += 1
                    if not self.iterate:
                        call_api = False
                else:
                    call_api = False
            if self.filters:
                objs = self.queryset.objects.filter(**self.filters)
                # Delete all that have sync=True (?)
            else:
                objs = self.queryset.objects.all()
            serializer = self.serializer_class(objs, many=True)
            # if self.client_attr:
            #     try:
            #         client = Client.objects.get(user=request.user)
            #         setattr(client, self.client_attr, objs.order_by('-datetime').first())
            #         client.save()
            #     except Client.DoesNotExist:
            #         pass
            serialized_data = serializer.data
            return Response(serialized_data)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, assembly, format=None):
        try:
            api = get_api_obj(assembly)

            api.ignore_admin_user = True
            api.social_ideation_source = reques.source # indicates the name of the providerId (e.g., social_ideation_facebook)
            api.social_ideation_source_url= request.source_url # source to the original post
            api.social_ideation_user_source_url= request.user_url # link to the user
            api.social_ideation_user_source_id= request.user_id # email or id of the user in the source social network

            new_obj_raw = getattr(api, self.api_method)(**self.api_method_params)
            new_obj_id = find_obj_id(new_obj_raw)
            new_obj= self.create_obj(new_obj_id, assembly, new_obj_raw)
            serializer = self.serializer_class(new_obj)
            if self.filters:
                new_obj.sync = True
                new_obj.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp


class AppCivistObjectDetail(APIView):
    """
    Retrieve or delete an object instance
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    
    api_method = ''
    api_method_params = None
    assembly = None
    create_obj = None
    queryset = None
    serializer_class = None

    def get(self, request, obj_id, format=None):
        try:
            api = get_api_obj(self.assembly)
            obj_raw = getattr(api, self.api_method)(**self.api_method_params)
            obj = self.create_obj(find_obj_id(obj_raw), self.assembly, obj_raw)
            serializer = self.serializer_class(obj)
            return Response(serializer.data)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def delete(self, request, obj_id, format=None):
        try:
            obj = self.queryset.objects.get(appcivist_id=obj_id)
            obj.delete()
            content = JSONRenderer().render({'text': 'The object was deleted correctly'})
            resp = Response(status=status.HTTP_200_OK)
            resp.content = content
            return resp
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp


# ---
# API View Classes
# ---


class TestingParams(APIView):
    """
    Return testing parameters
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        try:
            testing_params = TestingParameter.get_params()
            content = JSONRenderer().render(testing_params)
            resp = HttpResponse(content)
            resp.content_type = 'application/json'
            return resp
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp


class Assemblies(APIView):
    """
    Return the list of assemblies
    # """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        try:
            assemblies = Assembly.objects.all()
            serializer = AssemblySerializer(assemblies, many=True)
            return Response(serializer.data)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp


class Campaigns(APIView):
    """
    Return the list of initiatives
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, assembly_id, format=None):
        try:
            assembly = Assembly.objects.get(appcivist_id=assembly_id)
            campaigns = cru_campaign(-100, assembly)
            serializer = CampaignSerializer(campaigns, many=True)
            return Response(serializer.data)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

class Proposals(AppCivistObject):
    """
    Return the list of ideas or create a new one.
    """

    def get(self, request, assembly_id, format=None):
        try:
            self.api_method = 'get_all_proposals'
            self.pag_params = {'page_number': self.PAGE_NUMBER, 'page_size': self.PAGE_SIZE}
            self.iterate = False
            self.create_obj = cru_proposal
            self.queryset = Proposal
            self.serializer_class = ProposalSerializer
            self.filters = {'sync': False}
            self.client_attr = 'last_idea'
            assembly = Assembly.objects.get(appcivist_id=assembly_id)
            self.api_method_params = {"aid" : assembly.appcivist_id}
            return super(Proposals, self).get(request, assembly)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, assembly_id, format=None):
        try:
            proposal_details = {"status": "PUBLISHED", "titel": request.data["title"], "text": request.data["text"], "type": "PROPOSAL", "campaigns":[request.data['campaign_id']]}
            campaign = Campaign.objects.get(appcivist_id=request.data["campaign_id"])
            if 'tags' in request.data.keys():
                tags = [tag.strip() for tag in proposal_details['tags'].split(',')]
                proposal_details['tags'] = tags
            self.api_method_params = {"sid": campaign.resource_space_id, "proposal": proposal_details}
            self.api_method = 'create_proposal'
            self.create_obj = cru_proposal
            self.serializer_class = ProposalSerializer
            self.filters = {}
            assembly = Assembly.objects.get(appcivist_id=assembly_id)
            return super(Proposals,self).post(request, assembly)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp


class ProposalDetail(AppCivistObjectDetail):
    """
    Retrieve or delete an idea instance
    """
    queryset = Proposal
    serializer_class = ProposalSerializer

    def get(self, request, proposal_id, format=None):
        try:
            proposal = Proposal.objects.get(appcivist_id=proposal_id)
            self.assembly = proposal.campaign.assembly
            self.api_method = 'get_proposal_details'
            self.api_method_params = {"aid": self.assembly.appcivist_id, "coid": proposal_id}
            self.create_obj = cru_proposal
            return super(ProposalDetail, self).get(request, proposal_id)
        except Proposal.DoesNotExist, e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp
    def delete(self, request, proposal_id, format=None):
        try:
            proposal = Proposal.objects.get(appcivist_id=proposal_id)
            api = get_api_obj(proposal.campaign.assembly)
            api.delete_proposal(aid=proposal.campaign.assembly.appcivist_id, coid=proposal.appcivist_id)
            return super(ProposalDetail, self).delete(request, proposal_id)
        except Exception as e:
            return Response('Error: {}'.format(e.reason), status=status.HTTP_400_BAD_REQUEST)



class Authors(AppCivistObject):
    """
    Return the list of users or create a new one.
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, assembly_id, format=None):
        try:
            self.api_method = 'get_all_authors'
            self.pag_params = {'page_number': self.PAGE_NUMBER, 'page_size': self.PAGE_SIZE}
            self.iterate = False
            self.create_obj = cru_author
            self.queryset = Author
            self.serializer_class = AuthorSerializer
            assembly = Assembly.objects.get(appcivist_id=assembly_id)
            self.api_method_params = {"aid" : assembly.appcivist_id}
            return super(Authors,self).get(request, assembly)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp
    # def post(self, request, assembly_id, format=None):
    #     try:
    #         author_details = {'name': request.data['name'], 'email': request.data['email']}
    #         author_details.update({'silent': False}) # by Marce: previously True. 
    #         self.api_method_params = author_details
    #         self.api_method = 'create_new_author'
    #         self.create_obj = cru_author
    #         self.serializer_class = AuthorSerializer
    #         initiative = Initiative.objects.get(id=initiative_id)
    #         return super(Authors,self).post(request, initiative)
    #     except Exception as e:
    #         resp = Response(status=status.HTTP_400_BAD_REQUEST)
    #         resp.content = e
    #         return resp


class AuthorDetail(AppCivistObjectDetail):
    """
    Retrieve or delete an author instance
    """
    queryset = Author
    serializer_class = AuthorSerializer

    def get(self, request, user_id, format=None):
        try:
            author = Author.objects.get(appcivist_id=user_id)
            self.assembly = author.assembly
            self.api_method = 'get_author_info'
            self.api_method_params = {'uid': user_id}
            self.create_obj = cru_author
            return super(AuthorDetail, self).get(request, user_id)
        except Author.DoesNotExist, e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp
    def delete(self, request, author_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)


class Comments(AppCivistObject):
    """
    Return the list of comments or create a new one.
    """

    def get_assembly(self, assembly_id):
        try:
            return Assembly.objects.get(appcivist_id=assembly_id)
        except Assembly.DoesNotExist:
            return Http404

    def get(self, request, assembly_id, format=None):
        self.api_method = 'get_all_comments'
        self.client_attr = 'last_comment'
        self.pag_params = {'page_number': self.PAGE_NUMBER, 'page_size': self.PAGE_SIZE}
        self.iterate = False
        self.create_obj = cru_comment
        self.queryset = Comment
        self.serializer_class = CommentSerializer
        self.filters = {'sync': False}
        assembly = self.get_assembly(assembly_id)
        self.api_method_params = {"aid" : assembly.appcivist_id}
        return super(Comments,self).get(request, assembly)

    def post(self, request, assembly_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)


class CommentsProposal(AppCivistObject):
    """
    Return the list of comments of an idea
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def get(self, request, proposal_id, format=None):
        try:
            proposal = Proposal.objects.get(appcivist_id=proposal_id)
            assembly = proposal.campaign.assembly
            self.api_method = 'get_comments_of_proposal'
            self.api_method_params = {'sid': proposal.resource_space_id}
            self.client_attr = 'last_comment_idea'
            self.create_obj = cru_comment
            self.queryset = Comment
            self.serializer_class = CommentSerializer
            self.filters = {'sync':False, 'parent_proposal': proposal}
            return super(CommentsProposal,self).get(request, assembly)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, proposal_id, format=None):
        try:
            proposal = Proposal.objects.get(appcivist_id=proposal_id)
            assembly = proposal.campaign.assembly
            comment_details = {"status": "PUBLISHED", "text": request.data["text"], "type": "DISCUSSION", "campaigns":[request.data['campaign_id']]}
            self.api_method = 'comment_proposal'
            self.api_method_params = {"sid": proposal.resource_space_id, "discussion": comment_details}
            self.create_obj = cru_comment
            self.serializer_class = CommentSerializer
            self.filters = {'sync':True}
            return super(CommentsProposal,self).post(request, assembly)
        except Proposal.DoesNotExist:
            return Response('Error: Idea with id {} does not exist'.format(proposal_id), status=status.HTTP_400_BAD_REQUEST)


class CommentsComment(AppCivistObject):
    """
    Return the list of comments of a comment
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_assembly(self, comment):
        if comment.parent_type == 'proposal':
            return comment.parent_proposal.campaign.assembly
        else:
            return self.get_assembly(comment.parent_comment)

    def get(self, request, comment_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, comment_id, format=None):
        try:
            comment = Comment.objects.get(appcivist_id=comment_id)
            assembly = self.get_assembly(comment)
            comment_details = {"status": "PUBLISHED", "text": request.data["text"], "type": "COMMENT", "campaigns":[request.data['campaign_id']]}
            self.api_method_params = {"sid": comment.resource_space_id, "comment": comment_details}
            self.create_obj = cru_comment
            self.serializer_class = CommentSerializer
            self.filters = {'sync':True}
            return super(CommentsComment,self).post(request, assembly)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp


class CommentDetail(AppCivistObjectDetail):
    """
    Retrieve or delete an idea instance
    """
    queryset = Comment
    serializer_class = CommentSerializer

    def get_assembly(self, comment):
        if comment.parent_type == 'proposal':
            return comment.parent_proposal.campaign.assembly
        else:
            return self.get_assembly(comment.parent_comment)

    def get(self, request, comment_id, format=None):
        try:
            comment = Comment.objects.get(appcivist_id=comment_id)
            self.assembly = self.get_assembly(comment)
            self.api_method = 'get_comment_details'
            self.api_method_params = {"aid": self.assembly.appcivist_id,'coid': comment_id}
            self.create_obj = cru_comment
            return super(CommentDetail, self).get(request, comment_id)
        except Comment.DoesNotExist, e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp
    def delete(self, request, comment_id, format=None):
        try:
            comment = Comment.objects.get(appcivist_id=comment_id)
            assembly = self.get_assembly(comment)
            api = get_api_obj(assembly)
            api.delete_comment(aid=assembly.appcivist_id, coid=comment.appcivist_id)
            return super(CommentDetail, self).delete(request, comment_id)
        except Exception as e:
            return Response('Error: {}'.format(e.reason), status=status.HTTP_400_BAD_REQUEST)


class FeedbacksProposals(AppCivistObject):
    """
    Return the list of all votes of all ideas.
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, assembly_id, format=None):
        try:
            self.api_method = 'get_feedbacks_of_all_proposals'
            self.client_attr = 'last_vote'
            self.create_obj = cru_feedback
            self.queryset = Feedback
            self.serializer_class = FeedbackSerializer
            self.filters = {'sync': False}
            assembly = Assembly.objects.get(appcivist_id=assembly_id)
            self.api_method_params = {"aid": assembly.appcivist_id}
            return super(FeedbacksProposals,self).get(request, assembly)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, assembly_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)


class FeedbacksComments(AppCivistObject):
    """
    Return the list of all votes of all comments.
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, assembly_id, format=None):
        try:
            self.api_method = 'get_feedbacks_of_all_comments'
            self.client_attr = 'last_vote'
            self.create_obj = cru_feedback
            self.queryset = Feedback
            self.serializer_class = FeedbackSerializer
            self.filters = {'sync': False}
            assembly = Assembly.objects.get(appcivist_id=assembly_id)
            self.api_method_params = {"aid": assembly.appcivist_id}
            return super(FeedbacksComments,self).get(request, assembly)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, assembly_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)


class FeedbacksProposal(AppCivistObject):
    """
    Return the list of votes related to a particular idea.
    """

    def get(self, request, proposal_id, format=None):
        try:
            proposal = Proposal.objects.get(appcivist_id=proposal_id)
            assembly = proposal.campaign.assembly
            self.api_method = 'get_feedbacks_of_proposal'
            self.client_attr = 'last_vote_idea'
            self.api_method_params = {"aid":assembly.appcivist_id , "coid":proposal.appcivist_id}
            self.create_obj = cru_feedback
            self.queryset = Feedback
            self.serializer_class = FeedbackSerializer
            self.filters = {'sync':False}
            return super(FeedbacksProposal, self).get(request, assembly)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, proposal_id, format=None):
        try:
            proposal = Proposal.objects.get(appcivist_id=proposal_id)
            assembly = proposal.campaign.assembly
            if request.data['value'] > 0:
                self.api_method = 'vote_up_proposal'
            else:
                self.api_method = 'vote_down_proposal'
            self.api_method_params = {"caid": assembly.campaign.appcivist_id, "coid": proposal.appcivist_id}
            self.create_obj = cru_feedback
            self.serializer_class = FeedbackSerializer
            self.filters = {'sync':True}
            return super(FeedbacksProposal,self).post(request, assembly)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp



class FeedbacksComment(AppCivistObject):
    """
    Return the list of votes related to a comment idea.
    """

    def get_assembly(self, comment):
        if comment.parent_type == 'proposal':
            return comment.parent_proposal.campaign.assembly
        else:
            return self.get_assembly(comment.parent_comment)

    def get(self, request, comment_id, format=None):
        try:
            comment = Comment.objects.get(appcivist_id=comment_id)
            self.api_method = 'get_feedbacks_of_comment'
            self.client_attr = 'last_vote_comment'
            self.create_obj = cru_feedback
            self.queryset = Feedback
            self.serializer_class = FeedbackSerializer
            self.filters = {'sync': False}
            assembly = self.get_assembly(comment)
            self.api_method_params = {"aid": assembly.appcivist_id, "coid": comment.appcivist_id}
            return super(FeedbacksComment, self).get(request, assembly)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp
    def post(self, request, assembly_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)


class FeedbackDetail(AppCivistObjectDetail):
    """
    Retrieve or delete a vote instance
    """
    queryset = Feedback
    serializer_class = FeedbackSerializer

    def delete(self, request, vote_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)


def index(request):
    return HttpResponse('Welcome to Appcivist client API.')




