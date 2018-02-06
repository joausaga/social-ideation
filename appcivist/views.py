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

from appcivist.models import Campaign, Author, Theme, Idea, Comment, Feedback
from appcivist.serializers import CampaignSerializer, ThemeSerializer,\
      AuthorSerializer, IdeaSerializer, CommentSerializer, FeedbackSerializer

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

def get_api_obj(campaign):

    api = appcivist_api()
    api.base_url = campaign.url
    api.session_key = campaign.admin_session_key

    return api

def get_appcivist_data(campaign, api_method, method_params=None, pag_params=None):
    api = get_api_obj(campaign)
    if not method_params:
        objs = getattr(api, api_method)()
    elif method_params:
        objs = getattr(api, api_method)(**method_params)
    return objs


def cru_author(author_id, campaign, author_info=None):
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
            author_info = get_appcivist_data(campaign, 'get_author_info', {'uid': author_id})
        if "email" in author_info.keys():
            author = Author(appcivist_id=author_info["userId"], name=author_info["name"], email=author_info["email"],
                            campaign=campaign, appcivist_uuid=author_info["uuid"])
        else:
            author = Author(appcivist_id=author_info["userId"], name=author_info["name"], campaign=campaign,
                            appcivist_uuid=author_info["uuid"])
        author.save()
        return author


def cu_themes(campaign):
    themes_raw = get_appcivist_data(campaign, 'get_themes_of_campaign', 
                                    {'sid': campaign.resource_space_id})
    for theme_raw in themes_raw:
        try:
            theme = Theme.objects.get(appcivist_id=theme_raw["themeId"])
            theme.title = theme_raw["title"]
            theme.description = theme_raw["description"]
            theme.theme_type = theme_raw["type"]
            campaign.save()
        except Theme.DoesNotExist:
            theme = Theme(appcivist_id=theme_raw["themeId"], appcivist_uuid=theme_raw["uuid"], 
                       title=theme_raw["title"], description=theme_raw["description"],
                       theme_type=theme_raw["type"], campaign=campaign)
            campaign.save()

def cru_theme(theme_id, campaign):
    if theme_id > 0:
        try:
            return Theme.objects.get(appcivist_id=theme_id)
        except Theme.DoesNotExist:
            cu_themes(campaign)
    else:
        cu_themes(campaign)
        return Theme.objects.filter(campaign=campaign)


def get_theme_id_from_raw_idea(raw_themes):
    for raw_theme in raw_themes:
        if raw_theme["type"] == "OFFICIAL_PRE_DEFINED":
            return int(raw_theme["themeId"])
    return 0

# TODO ver como asignarle el theme (en las 2 partes)
def cru_idea(idea_id, campaign, idea_obj=None):
    try:
        idea = Idea.objects.get(appcivist_id=idea_id)
        if idea_obj:
            if 'title' in idea_obj.keys() and 'plainText' in idea_obj.keys():
                idea.title = idea_obj["title"]
                idea.text = idea_obj["plainText"]
            else:
                idea.text = idea_obj["title"]
            idea.positive_votes = idea_obj["stats"]['ups']
            idea.negative_votes = idea_obj["stats"]['downs']
            idea.comments = idea_obj["commentCount"]
            theme_id = get_theme_id_from_raw_idea(idea_obj["themes"])
            idea.theme = cru_theme(theme_id, campaign)
        idea.sync = False
        idea.save()
        return idea
    except Idea.DoesNotExist:
        if not idea_obj:
            idea_obj = get_appcivist_data(campaign, 'get_idea_details', 
                       {'coid': idea_id, 'aid': campaign.assembly_id})
        if 'firstAuthor' not in idea_obj.keys():
            if 'nonMemberAuthor' in idea_obj.keys():
                author_info = {'userId': 0 , 'name': 'Anonymous', 'uuid': '0'}
        else:
            author_info = idea_obj['firstAuthor']
        author = cru_author(author_info['userId'], campaign, author_info)
        theme_id = get_theme_id_from_raw_idea(idea_obj["themes"])
        theme = cru_theme(theme_id, campaign)
        positive_votes = idea_obj["stats"]['ups']
        negative_votes = idea_obj["stats"]['downs']
        comments = idea_obj["commentCount"]
        url = ""
        idea_ac_dt = datetime.strptime(idea_obj["creation"].replace(" GMT", ""), "%Y-%m-%d %H:%M %p")
        idea_dt = _get_timezone_aware_datetime(idea_ac_dt) if timezone.is_naive(idea_ac_dt) else idea_ac_dt
        # We use the 'title' attribute of the response as the 'text' attribute of the instance
        # because that's where appcivist's ideas store the text
        if 'title' in idea_obj.keys() and 'plainText' in idea_obj.keys():
            title = idea_obj["title"]
            text = idea_obj["plainText"]
        else:
            title = ""
            text = idea_obj["title"]
        idea = Idea(appcivist_id=idea_obj["contributionId"], appcivist_uuid=idea_obj["uuidAsString"],
                    title=title, text=text, datetime=idea_dt, positive_votes=positive_votes, 
                    negative_votes=negative_votes, comments=comments, theme=theme, 
                    url=url, user=author, sync=False, resource_space_id=idea_obj["resourceSpaceId"],
                    forum_resource_space_id=idea_obj["forumResourceSpaceId"])
        idea.save()
        return idea

def get_parent_comment(parent_type, parent_id, campaign):
    if parent_type == 'idea':
        try:
            return Idea.objects.get(appcivist_id=parent_id)
        except Idea.DoesNotExist:
            return cru_idea(parent_id, campaign)
    else:
        try:
            return Comment.objects.get(appcivist_id=parent_id)
        except Comment.DoesNotExist:
            return cru_comment(parent_id, campaign)

def cru_comment(comment_id, campaign, comment_obj=None):
    try:
        comment = Comment.objects.get(appcivist_id=comment_id)
        if comment_obj:
            comment.text = comment_obj["plainText"]
            comment.positive_votes = comment_obj["stats"]['ups']
            comment.negative_votes = comment_obj["stats"]['downs']
            comment.comments = comment_obj["commentCount"]
        comment.sync = False
        comment.save()
        return comment
    except Comment.DoesNotExist:
        if not comment_obj:
            comment_obj = get_appcivist_data(campaign, 'get_comment_details', {'coid': comment_id,
                                                                      'aid': campaign.assembly_id})
        if 'firstAuthor' not in comment_obj.keys():
            if 'nonMemberAuthor' in comment_obj.keys():
                author_info = {'userId': 0 , 'name': 'Anonymous', 'uuid': '0'}
        else:
            author_info = comment_obj['firstAuthor']
        author = cru_author(author_info['userId'], campaign, author_info)
        positive_votes = comment_obj["stats"]['ups']
        negative_votes = comment_obj["stats"]['downs']
        comments = comment_obj["commentCount"]
        url = ""
        if comment_obj["type"] == "DISCUSSION":
            parent_type = "idea"
        else:
            parent_type = "comment"
        #comment_ac_dt = parse(comment_obj["creation"])
        comment_ac_dt = datetime.strptime(comment_obj["creation"].replace(" GMT", ""), "%Y-%m-%d %H:%M %p")
        comment_dt = _get_timezone_aware_datetime(comment_ac_dt) if timezone.is_naive(comment_ac_dt) else comment_ac_dt
        comment = Comment(appcivist_id=comment_obj["contributionId"], appcivist_uuid=comment_obj["uuidAsString"],
                          text=comment_obj["plainText"], datetime=comment_dt, positive_votes=positive_votes, 
                          negative_votes=negative_votes, comments=comments, url=url, user=author, 
                          parent_type=parent_type, sync=False, resource_space_id=comment_obj["resourceSpaceId"],
                          forum_resource_space_id=comment_obj["forumResourceSpaceId"])
        parent_id = comment_obj["containingContributionsIds"][0]
        parent = get_parent_comment(parent_type, parent_id, campaign)
        if parent_type == 'idea':
            comment.parent_idea = parent
        else:
            comment.parent_comment = parent
        comment.save()
        return comment

def get_parent_feedback(parent_type, parent_id, campaign):
    get_parent_comment(parent_type, parent_id, campaign)

def cru_feedback(feedback_id, campaign, feedback_obj):
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
        author = cru_author(author_id, campaign)
        #feedback_ac_dt = parse(feedback_obj["creation"])
        feedback_ac_dt = datetime.strptime(feedback_obj["creation"].replace(" GMT", ""), "%Y-%m-%d %H:%M %p")
        feedback_dt = _get_timezone_aware_datetime(feedback_ac_dt) if timezone.is_naive(feedback_ac_dt) else feedback_ac_dt
        
        if feedback_obj["up"]:
            feedback_value = 1
        elif feedback_obj["down"]:
            feedback_value = -1
        feedback_parent_type = feedback_obj["parentType"].lower()
        feedback_parent_id = feedback_obj["contributionId"]
        feedback = Feedback(appcivist_id=feedback_obj["id"], value=feedback_value, datetime=feedback_dt, 
                            author=author, sync=False, parent_type=feedback_parent_type)
        if feedback_parent_type == 'idea':
            feedback.parent_idea = cru_idea(feedback_parent_id, campaign)
        else:
            feedback.parent_comment = cru_comment(feedback_parent_id, campaign)
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
    elif "themeId" in obj_raw.keys():
        return int(obj_raw["themeId"])

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

    def get(self, request, campaign, format=None):
        call_api = True
        try:
            self.queryset.objects.all().update(sync=True)
            while call_api:
                objs_raw = get_appcivist_data(campaign, self.api_method, self.api_method_params, self.pag_params)
                if len(objs_raw) > 0:
                    for obj_raw in objs_raw:
                        # TODO, aca no necesariamente se va a llamar id, puede ser id, o contributionId o CampaignId
                        obj_id = find_obj_id(obj_raw)
                        self.create_obj(obj_id, campaign, obj_raw)
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

    def post(self, request, campaign, format=None):
        respmsg = "inicio"
        try:
            api = get_api_obj(campaign)

            api.ignore_admin_user = "true"
            api.social_ideation_source = request.data['source'] # indicates the name of the providerId (e.g., social_ideation_facebook)
            api.social_ideation_source_url = request.data['source_url'] # source to the original post
            api.social_ideation_user_source_url = request.data['user_url'] # link to the user
            api.social_ideation_user_source_id = request.data['user_external_id'] # email or id of the user in the source social network
            api.social_ideation_user_name = request.data['user_name'] # the name of the author in the social network
            api.assembly_id = campaign.assembly_id
            new_obj_raw = getattr(api, self.api_method)(**self.api_method_params)
            new_obj_id = find_obj_id(new_obj_raw)
            new_obj= self.create_obj(new_obj_id, campaign, new_obj_raw)
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
    campaign = None
    create_obj = None
    queryset = None
    serializer_class = None

    def get(self, request, obj_id, format=None):
        try:
            api = get_api_obj(self.campaign)
            obj_raw = getattr(api, self.api_method)(**self.api_method_params)
            obj = self.create_obj(find_obj_id(obj_raw), self.campaign, obj_raw)
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


class Campaigns(APIView):
    """
    Return the list of compaigns
    # """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        try:
            campaigns = Campaign.objects.all()
            serializer = CampaignSerializer(campaigns, many=True)
            return Response(serializer.data)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

class Themes(APIView):
    """
    Return the list of themes
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, initiative_id, format=None):
        campaign_id = initiative_id
        try:
            campaign = Campaign.objects.get(appcivist_id=assembly_id)
            themes = cru_theme(-100, campaign)
            serializer = ThemeSerializer(themes, many=True)
            return Response(serializer.data)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

# cambiando TODO agregar aca las tematicas
class Ideas(AppCivistObject):
    """
    Return the list of ideas or create a new one.
    """

    def get(self, request, initiative_id, format=None):
        campaign_id = initiative_id
        try:
            self.api_method = 'get_ideas_of_campaign'
            self.pag_params = {'page_number': self.PAGE_NUMBER, 'page_size': self.PAGE_SIZE}
            self.iterate = False
            self.create_obj = cru_idea
            self.queryset = Idea
            self.serializer_class = IdeaSerializer
            self.filters = {'sync': False}
            self.client_attr = 'last_idea'
            campaign = Campaign.objects.get(appcivist_id=campaign_id)
            self.api_method_params = {"aid" : campaign.assembly_id, 
                                      "cid" : campaign.appcivist_id}
            return super(Ideas, self).get(request, campaign)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, initiative_id, format=None):
        campaign_id = initiative_id #AC campaign = SI initiative
        theme_id = request.data["campaign_id"] #AC theme = SI campaign
        try:
            campaign = Campaign.objects.get(appcivist_id=campaign_id)
            idea_details = {"status": "PUBLISHED", "title": request.data["title"], 
                            "text": request.data["text"], "type": "IDEA", 
                            "campaigns":[campaign.appcivist_id],
                            "themes": [{"themeId": theme_id, "type": "OFFICIAL_PRE_DEFINED"}]
            self.api_method_params = {"sid": campaign.resource_space_id, 
                                      "idea": idea_details}
            self.api_method = 'create_idea'
            self.create_obj = cru_idea
            self.serializer_class = IdeaSerializer
            self.filters = {}
            return super(Ideas,self).post(request, campaign)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

class IdeaDetail(AppCivistObjectDetail):
    """
    Retrieve or delete an idea instance
    """
    queryset = Idea
    serializer_class = IdeaSerializer

    def get(self, request, idea_id, format=None):
        try:
            idea = Idea.objects.get(appcivist_id=idea_id)
            self.campaign = idea.theme.campaign
            self.api_method = 'get_idea_details'
            self.api_method_params = {"aid": self.campaign.assembly_id,
                                      "coid": idea_id}
            self.create_obj = cru_idea
            return super(IdeaDetail, self).get(request, idea_id)
        except Idea.DoesNotExist, e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp
    def delete(self, request, idea_id, format=None):
        try:
            idea = Idea.objects.get(appcivist_id=idea_id)
            api = get_api_obj(idea.theme.campaign)
            api.delete_idea(aid=idea.theme.campaign.assembly_id, 
                            coid=idea.appcivist_id)
            return super(IdeaDetail, self).delete(request, idea_id)
        except Exception as e:
            return Response('Error: {}'.format(e.reason), status=status.HTTP_400_BAD_REQUEST)


class Authors(AppCivistObject):
    """
    Return the list of users or create a new one.
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, initiative_id, format=None):
        campaign_id = initiative_id
        try:
            self.api_method = 'get_all_authors'
            self.pag_params = {'page_number': self.PAGE_NUMBER, 'page_size': self.PAGE_SIZE}
            self.iterate = False
            self.create_obj = cru_author
            self.queryset = Author
            self.serializer_class = AuthorSerializer
            campaign = Campaign.objects.get(appcivist_id=campaign_id)
            self.api_method_params = {"aid" : campaign.assembly_id}
            return super(Authors,self).get(request, campaign)
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
            self.campaign = author.campaign
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

    def get(self, request, initiative_id, format=None):
        campaign_id = initiative_id
        self.api_method = 'get_comments_of_campaign'
        self.client_attr = 'last_comment'
        self.pag_params = {'page_number': self.PAGE_NUMBER, 'page_size': self.PAGE_SIZE}
        self.iterate = False
        self.create_obj = cru_comment
        self.queryset = Comment
        self.serializer_class = CommentSerializer
        self.filters = {'sync': False}
        campaign = Campaign.objects.get(appcivist_id=campaign_id)
        self.api_method_params = {"aid" : campaign.assembly_id,
                                  "cid" : campaign.appcivist_id}
        return super(Comments,self).get(request, campaign)

    def post(self, request, initiative_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)

class CommentsIdea(AppCivistObject):
    """
    Return the list of comments of an idea
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def get(self, request, idea_id, format=None):
        try:
            idea = Idea.objects.get(appcivist_id=idea_id)
            campaign = idea.theme.campaign
            self.api_method = 'get_comments_of_idea'
            self.api_method_params = {'sid': idea.resource_space_id}
            self.client_attr = 'last_comment_idea'
            self.create_obj = cru_comment
            self.queryset = Comment
            self.serializer_class = CommentSerializer
            self.filters = {'sync':False, 'parent_idea': idea}
            return super(CommentsIdea,self).get(request, campaign)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, idea_id, format=None):
        try:
            idea = Idea.objects.get(appcivist_id=idea_id)
            campaign = idea.theme.campaign
            comment_details = {"status": "PUBLISHED", "title": request.data['text'][:10],
                               "text": request.data["text"], "type": "DISCUSSION"}
            self.api_method = 'comment_idea'
            self.api_method_params = {"sid": idea.resource_space_id, 
                                      "discussion": comment_details}
            self.create_obj = cru_comment
            self.serializer_class = CommentSerializer
            self.filters = {'sync':True}
            return super(CommentsIdea,self).post(request, campaign)
        except Idea.DoesNotExist:
            return Response('Error: Idea with id {} does not exist'.format(idea_id), \
                             status=status.HTTP_400_BAD_REQUEST)

# ya esta cambiado
class CommentsComment(AppCivistObject):
    """
    Return the list of comments of a comment
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_campaign(self, comment):
        if comment.parent_type == 'idea':
            return comment.parent_idea.theme.campaign
        else:
            return self.get_campaign(comment.parent_comment)

    def get(self, request, comment_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, comment_id, format=None):
        try:
            comment = Comment.objects.get(appcivist_id=comment_id)
            campaign = self.get_campaign(comment)
            comment_details = {"status": "PUBLISHED", "title": request.data["text"][:10],
                               "text": request.data["text"], "type": "COMMENT"}
            self.api_method = "comment_discussion"
            self.api_method_params = {"sid": comment.resource_space_id, 
                                      "comment": comment_details}
            self.create_obj = cru_comment
            self.serializer_class = CommentSerializer
            self.filters = {'sync':True}
            return super(CommentsComment,self).post(request, campaign)
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

    def get_campaign(self, comment):
        if comment.parent_type == 'idea':
            return comment.parent_idea.theme.campaign
        else:
            return self.get_campaign(comment.parent_comment)

    def get(self, request, comment_id, format=None):
        try:
            comment = Comment.objects.get(appcivist_id=comment_id)
            self.campaign = self.get_campaign(comment)
            self.api_method = 'get_comment_details'
            self.api_method_params = {"aid": self.campaign.assembly_id,
                                      'coid': comment_id}
            self.create_obj = cru_comment
            return super(CommentDetail, self).get(request, comment_id)
        except Comment.DoesNotExist, e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp
    def delete(self, request, comment_id, format=None):
        try:
            comment = Comment.objects.get(appcivist_id=comment_id)
            campaign = self.get_campaign(comment)
            api = get_api_obj(campaign)
            api.delete_comment(aid=campaign.assembly_id, coid=comment.appcivist_id)
            return super(CommentDetail, self).delete(request, comment_id)
        except Exception as e:
            return Response('Error: {}'.format(e.reason), status=status.HTTP_400_BAD_REQUEST)

class FeedbacksIdeas(AppCivistObject):
    """
    Return the list of all votes of all ideas.
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, initiative_id, format=None):
        campaign_id = initiative_id
        try:
            self.api_method = 'get_feedbacks_of_capaign_ideas'
            self.client_attr = 'last_vote'
            self.create_obj = cru_feedback
            self.queryset = Feedback
            self.serializer_class = FeedbackSerializer
            self.filters = {'sync': False}
            campaign = Campaign.objects.get(appcivist_id=campaign_id)
            self.api_method_params = {"aid": campaign.assembly_id,
                                      "cid": campaign.appcivist_id}
            return super(FeedbacksIdeas,self).get(request, campaign)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, initiative_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)

class FeedbacksComments(AppCivistObject):
    """
    Return the list of all votes of all comments.
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, initiative_id, format=None):
        campaign_id = initiative_id
        try:
            self.api_method = 'get_feedbacks_of_campaign_comments'
            self.client_attr = 'last_vote'
            self.create_obj = cru_feedback
            self.queryset = Feedback
            self.serializer_class = FeedbackSerializer
            self.filters = {'sync': False}
            campaign = Campaign.objects.get(appcivist_id=campaign_id)
            self.api_method_params = {"aid": campaign.assembly_id,
                                      "cid": campaign.appcivist_id}
            return super(FeedbacksComments,self).get(request, campaign)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, initiative_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)

class FeedbacksIdea(AppCivistObject):
    """
    Return the list of votes related to a particular idea.
    """

    def get(self, request, idea_id, format=None):
        try:
            idea = Idea.objects.get(appcivist_id=idea_id)
            campaign = idea.theme.campaign
            self.api_method = 'get_feedbacks_of_idea'
            self.client_attr = 'last_vote_idea'
            self.api_method_params = {"aid": campaign.assembly_id , 
                                      "coid":idea.appcivist_id}
            self.create_obj = cru_feedback
            self.queryset = Feedback
            self.serializer_class = FeedbackSerializer
            self.filters = {'sync':False}
            return super(FeedbacksIdea, self).get(request, campaign)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, idea_id, format=None):
        try:
            idea = Idea.objects.get(appcivist_id=idea_id)
             campaign = idea.theme.campaign
            if request.data['value'] > 0:
                self.api_method = 'vote_up_idea'
            else:
                self.api_method = 'vote_down_idea'
            self.api_method_params = {"aid": campaign.assembly_id,
                                      "caid": campaign.appcivist_id, 
                                      "coid": idea.appcivist_id}
            self.create_obj = cru_feedback
            self.serializer_class = FeedbackSerializer
            self.filters = {'sync':True}
            return super(FeedbacksIdea,self).post(request, campaign)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp


class FeedbacksComment(AppCivistObject):
    """
    Return the list of votes related to a comment idea.
    """

    def get_campaign(self, comment):
        if comment.parent_type == 'idea':
            return comment.parent_idea.theme.campaign
        else:
            return self.get_campaign(comment.parent_comment)

    def get(self, request, comment_id, format=None):
        try:
            comment = Comment.objects.get(appcivist_id=comment_id)
            self.api_method = 'get_feedbacks_of_comment'
            self.client_attr = 'last_vote_comment'
            self.create_obj = cru_feedback
            self.queryset = Feedback
            self.serializer_class = FeedbackSerializer
            self.filters = {'sync': False}
            campaign = self.get_campaign(comment)
            self.api_method_params = {"aid": campaign.assembly_id, 
                                      "coid": comment.appcivist_id}
            return super(FeedbacksComment, self).get(request, campaign)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp
    def post(self, request, initiative_id, format=None):
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




