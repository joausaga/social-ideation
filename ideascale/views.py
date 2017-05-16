import logging
import os
import six
import sys

from ideascale.models import Idea, Initiative, TestingParameter, Campaign, Client, Author, Location, Comment, Vote
from ideascale.serializers import IdeaSerializer, InitiativeSerializer, CampaignSerializer, AuthorSerializer, \
                                  CommentSerializer, VoteSerializer

from dateutil.parser import parse

from django.http import HttpResponse, Http404
from django.utils import timezone

from ideascaly.auth import AuthNonSSO
from ideascaly.error import IdeaScalyError
from ideascaly.api import API

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer

logger = logging.getLogger(__name__)

# ---
# General methods and classes
# ---


def convert_to_utf8_str(arg):
    # written by Michael Norton (http://docondev.blogspot.com/)
    if isinstance(arg, six.text_type):
        arg = arg.encode('utf-8')
    elif not isinstance(arg, bytes):
        arg = six.text_type(arg).encode('utf-8')
    elif isinstance(arg, bytes):
        arg = arg.decode('utf-8')
    return arg


def _get_timezone_aware_datetime(datetime):
    return timezone.make_aware(datetime, timezone.get_default_timezone())


def get_api_obj(initiative):
    auth = AuthNonSSO(initiative.token)
    api = API(auth)
    api.community_url = initiative.url
    return api


def get_ideascale_data(initiative, api_method, method_params=None, pag_params=None):
    api = get_api_obj(initiative)
    if not method_params and not pag_params:
        objs = getattr(api, api_method)()
    elif method_params:
        if pag_params:
            method_params.update(pag_params)
        objs = getattr(api, api_method)(**method_params)
    else:
        objs = getattr(api, api_method)(**pag_params)
    return objs


def cru_author(author_id, initiative, author_info=None):
    try:
        author = Author.objects.get(ideascale_id=author_id)
        if author_info:
            # Update obj before returning
            author.name = author_info.name
            if hasattr(author_info, "email"):
                author.email = author_info.email
            author.save()
        return author
    except Author.DoesNotExist:
        if not author_info:
            author_info = get_ideascale_data(initiative, 'get_member_info_by_id', {'memberId': author_id})
        if hasattr(author_info, "email"):
            author = Author(ideascale_id=author_info.id, name=author_info.name, email=author_info.email,
                            initiative=initiative)
        else:
            author = Author(ideascale_id=author_info.id, name=author_info.name, initiative=initiative)
        author.save()
        return author


def cu_campaigns(initiative):
    campaigns_raw = get_ideascale_data(initiative, 'get_campaigns')
    for campaign_raw in campaigns_raw:
        try:
            campaign = Campaign.objects.get(ideascale_id=campaign_raw.id)
            campaign.name = campaign_raw.name
            campaign.save()
        except Campaign.DoesNotExist:
            campaign = Campaign(ideascale_id=campaign_raw.id, name=campaign_raw.name, initiative=initiative)
            campaign.save()


def cru_campaign(campaign_id, initiative):
    if campaign_id > 0:
        try:
            return Campaign.objects.get(ideascale_id=campaign_id)
        except Campaign.DoesNotExist:
            cu_campaigns(initiative)
    else:
        cu_campaigns(initiative)
        return Campaign.objects.filter(initiative=initiative)


def cru_location(location_obj):
    if location_obj['country'] and location_obj['city']:
        country_utf8 = convert_to_utf8_str(location_obj['country'])
        city_utf8 = convert_to_utf8_str(location_obj['city'])
        code = '{}_{}'.format(country_utf8.strip().lower(), city_utf8.strip().lower())
        try:
            location = Location.objects.get(code=code)
            if location_obj['longitude'] and location_obj['latitude']:
                location.longitude,  location.latitude = location_obj['longitude'], location_obj['latitude']
                location.save()
            return location
        except Location.DoesNotExist:
            if location_obj['longitude'] and location_obj['latitude']:
                location = Location(country=location_obj['country'], city=location_obj['city'], code=code,
                                    longitude=location_obj['longitude'], latitude=location_obj['latitude'])
            else:
                location = Location(country=location_obj['country'], city=location_obj['city'], code=code)
            location.save()
            return location
    else:
        return None


def cru_idea(idea_id, initiative, idea_obj=None):
    try:
        idea = Idea.objects.get(ideascale_id=idea_id)
        if idea_obj:
            idea.title = idea_obj.title
            idea.text = idea_obj.text
            idea.positive_votes = idea_obj.upVoteCount if idea_obj.upVoteCount > 0 else 0
            idea.negative_votes = idea_obj.downVoteCount if idea_obj.downVoteCount > 0 else 0
            idea.comments = idea_obj.commentCount if idea_obj.commentCount > 0 else 0
            idea.campaign = cru_campaign(idea_obj.campaignId, initiative)
        idea.sync = False
        idea.save()
        return idea
    except Idea.DoesNotExist:
        if not idea_obj:
            idea_obj = get_ideascale_data(initiative, 'get_idea_details', {'ideaId': idea_id})
        author = cru_author(idea_obj.authorId, initiative, idea_obj.authorInfo)
        location = cru_location(idea_obj.locationInfo) if hasattr(idea_obj, 'locationInfo') else None
        campaign_idea = cru_campaign(idea_obj.campaignId, initiative)
        positive_votes = idea_obj.upVoteCount if idea_obj.upVoteCount > 0 else 0
        negative_votes = idea_obj.downVoteCount if idea_obj.downVoteCount > 0 else 0
        comments = idea_obj.commentCount if idea_obj.commentCount > 0 else 0
        idea_is_dt = parse(idea_obj.creationDateTime)
        idea_dt = _get_timezone_aware_datetime(idea_is_dt) if timezone.is_naive(idea_is_dt) else idea_is_dt
        idea = Idea(ideascale_id=idea_obj.id, title=idea_obj.title, text=idea_obj.text,
                    datetime=idea_dt, positive_votes=positive_votes, negative_votes=negative_votes, comments=comments,
                    campaign=campaign_idea, url=idea_obj.url, user=author, location=location, sync=False)
        idea.save()
        return idea


def get_parent_comment(comment, initiative):
    if comment.parentType == 'idea':
        try:
            return Idea.objects.get(ideascale_id=comment.parentId)
        except Idea.DoesNotExist:
            return cru_idea(comment.parentId, initiative)
    else:
        try:
            return Comment.objects.get(ideascale_id=comment.parentId)
        except Comment.DoesNotExist:
            return cru_comment(comment.parentId, initiative)


def cru_comment(comment_id, initiative, comment_obj=None):
    try:
        comment = Comment.objects.get(ideascale_id=comment_id)
        if comment_obj:
            comment.text = comment_obj.text
            comment.positive_votes = comment_obj.upVoteCount if comment_obj.upVoteCount > 0 else 0
            comment.negative_votes = comment_obj.downVoteCount if comment_obj.downVoteCount > 0 else 0
            comment.comments = comment_obj.commentCount if comment_obj.commentCount > 0 else 0
        comment.sync = False
        comment.save()
        return comment
    except Comment.DoesNotExist:
        if not comment_obj:
            comment_obj = get_ideascale_data(initiative, 'get_comment', {'commentId': comment_id})
        author = cru_author(comment_obj.authorId, initiative, comment_obj.authorInfo)
        location = cru_location(comment_obj.locationInfo) if hasattr(comment_obj, 'locationInfo') else None
        positive_votes = comment_obj.upVoteCount if comment_obj.upVoteCount > 0 else 0
        negative_votes = comment_obj.downVoteCount if comment_obj.downVoteCount > 0 else 0
        comments = comment_obj.commentCount if comment_obj.commentCount > 0 else 0
        comment_is_dt = parse(comment_obj.creationDateTime)
        comment_dt = _get_timezone_aware_datetime(comment_is_dt) if timezone.is_naive(comment_is_dt) else comment_is_dt
        comment = Comment(ideascale_id=comment_obj.id, text=comment_obj.text,
                          datetime=comment_dt, positive_votes=positive_votes, negative_votes=negative_votes,
                          comments=comments, url=comment_obj.url, user=author, location=location,
                          parent_type=comment_obj.parentType, sync=False)
        parent_comment = get_parent_comment(comment_obj, initiative)
        if comment_obj.parentType == 'idea':
            comment.parent_idea = parent_comment
        else:
            comment.parent_comment = parent_comment
        comment.save()
        return comment


def cru_vote(vote_id, initiative, vote_obj):
    try:
        vote = Vote.objects.get(ideascale_id=vote_id)
        if vote_obj:
            if hasattr(vote_obj, 'voteValue'):
                vote.value = vote_obj.voteValue
            elif hasattr(vote_obj, 'myVote'):
                vote.value = vote_obj.myVote
            if hasattr(vote_obj, 'ideaType'):
                vote.parent_type = vote_obj.ideaType
        vote.sync = False
        vote.save()
        return vote
    except Vote.DoesNotExist:
        author_id = vote_obj.authorId if hasattr(vote_obj, 'authorId') else vote_obj.memberId
        author = cru_author(author_id, initiative)
        vote_is_dt = parse(vote_obj.creationDateTime) if hasattr(vote_obj, 'creationDateTime') else parse(vote_obj.creationDate)
        vote_dt = _get_timezone_aware_datetime(vote_is_dt) if timezone.is_naive(vote_is_dt) else vote_is_dt
        vote_parent_type = vote_obj.ideaType if hasattr(vote_obj, 'ideaType') else 'idea'
        vote_value = vote_obj.voteValue if hasattr(vote_obj, 'voteValue') else vote_obj.myVote
        vote_parent_id = vote_obj.ideaId if hasattr(vote_obj, 'ideaId') else vote_obj.id
        vote = Vote(ideascale_id=vote_obj.id, value=vote_value, datetime=vote_dt, author=author, sync=False,
                    parent_type=vote_parent_type)
        if vote_parent_type == 'idea':
            vote.parent_idea = cru_idea(vote_parent_id, initiative)
        else:
            vote.parent_comment = cru_comment(vote_parent_id, initiative)
        vote.save()
        return vote


# ---
# API Meta Classes
# ---

class ISObject(APIView):
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

    def get(self, request, initiative, format=None):
        call_api = True
        try:
            self.queryset.objects.all().update(sync=True)
            while call_api:
                objs_raw = get_ideascale_data(initiative, self.api_method, self.api_method_params, self.pag_params)
                if len(objs_raw) > 0:
                    for obj_raw in objs_raw:
                        self.create_obj(obj_raw.id, initiative, obj_raw)
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
            if self.client_attr:
                try:
                    client = Client.objects.get(user=request.user)
                    setattr(client, self.client_attr, objs.order_by('-datetime').first())
                    client.save()
                except Client.DoesNotExist:
                    pass
            serialized_data = serializer.data
            return Response(serialized_data)
        except IdeaScalyError as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = 'Error: {}'.format(e.reason)
            return resp
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, initiative, format=None):
        try:
            api = get_api_obj(initiative)
            new_obj_raw = getattr(api, self.api_method)(**self.api_method_params)
            new_obj= self.create_obj(new_obj_raw.id, initiative, new_obj_raw)
            serializer = self.serializer_class(new_obj)
            if self.filters:
                new_obj.sync = True
                new_obj.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IdeaScalyError as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = 'Error: {}'.format(e.reason)
            return resp
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp


class ISObjectDetail(APIView):
    """
    Retrieve or delete an object instance
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    api_method = ''
    api_method_params = None
    initiative = None
    create_obj = None
    queryset = None
    serializer_class = None

    def get(self, request, obj_id, format=None):
        try:
            api = get_api_obj(self.initiative)
            obj_raw = getattr(api, self.api_method)(**self.api_method_params)
            obj = self.create_obj(obj_raw.id, self.initiative, obj_raw)
            serializer = self.serializer_class(obj)
            return Response(serializer.data)
        except IdeaScalyError as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = 'Error: {}'.format(e.reason)
            return resp
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def delete(self, request, obj_id, format=None):
        try:
            obj = self.queryset.objects.get(ideascale_id=obj_id)
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


class Initiatives(APIView):
    """
    Return the list of initiatives
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        try:
            initiatives = Initiative.objects.all()
            serializer = InitiativeSerializer(initiatives, many=True)
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

    def get(self, request, initiative_id, format=None):
        try:
            initiative = Initiative.objects.get(id=initiative_id)
            campaigns = cru_campaign(-100, initiative)
            serializer = CampaignSerializer(campaigns, many=True)
            return Response(serializer.data)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp


class Ideas(ISObject):
    """
    Return the list of ideas or create a new one.
    """

    def get(self, request, initiative_id, format=None):
        try:
            self.api_method = 'get_all_ideas'
            self.pag_params = {'page_number': self.PAGE_NUMBER, 'page_size': self.PAGE_SIZE}
            self.iterate = True
            self.create_obj = cru_idea
            self.queryset = Idea
            self.serializer_class = IdeaSerializer
            self.filters = {'sync': False}
            self.client_attr = 'last_idea'
            initiative = Initiative.objects.get(id=initiative_id)
            return super(Ideas, self).get(request, initiative)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, initiative_id, format=None):
        try:
            idea_details = {'title': request.data['title'], 'text': request.data['text'],
                            'campaignId': request.data['campaign_id']}
            if 'tags' in request.data.keys():
                tags = [tag.strip() for tag in idea_details['tags'].split(',')]
                idea_details['tags'] = tags
            self.api_method_params = idea_details
            self.api_method = 'create_idea'
            self.create_obj = cru_idea
            self.serializer_class = IdeaSerializer
            self.filters = {}
            initiative = Initiative.objects.get(id=initiative_id)
            return super(Ideas,self).post(request, initiative)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp


class IdeaDetail(ISObjectDetail):
    """
    Retrieve or delete an idea instance
    """
    queryset = Idea
    serializer_class = IdeaSerializer

    def get(self, request, idea_id, format=None):
        try:
            idea = Idea.objects.get(ideascale_id=idea_id)
            self.initiative = idea.campaign.initiative
            self.api_method = 'get_idea_details'
            self.api_method_params = {'ideaId': idea_id}
            self.create_obj = cru_idea
            return super(IdeaDetail, self).get(request, idea_id)
        except Idea.DoesNotExist, e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def delete(self, request, idea_id, format=None):
        try:
            idea = Idea.objects.get(ideascale_id=idea_id)
            api = get_api_obj(idea.campaign.initiative)
            api.delete_idea(idea_id)
            return super(IdeaDetail, self).delete(request, idea_id)
        except IdeaScalyError as e:
            return Response('Error: {}'.format(e.reason), status=status.HTTP_400_BAD_REQUEST)


class IdeaAttachFile(APIView):
    """
    Attach a file to an idea
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, idea_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, idea_id, format=None):
        try:
            file_name = request.data['file_str']
            file_path = str(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                                         'static/{}'.format(file_name)))
            idea = Idea.objects.get(ideascale_id=idea_id)
            api = get_api_obj(idea.campaign.initiative)
            api.attach_file_to_idea(filename=file_path, ideaId=idea_id)
            return HttpResponse('OK', status=status.HTTP_200_OK)
        except IdeaScalyError as e:
            return Response('Error: {}'.format(e.reason), status=status.HTTP_400_BAD_REQUEST)


class Authors(ISObject):
    """
    Return the list of users or create a new one.
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, initiative_id, format=None):
        try:
            self.api_method = 'get_all_members'
            self.pag_params = {'page_number': self.PAGE_NUMBER, 'page_size': self.PAGE_SIZE}
            self.iterate = True
            self.create_obj = cru_author
            self.queryset = Author
            self.serializer_class = AuthorSerializer
            initiative = Initiative.objects.get(id=initiative_id)
            return super(Authors,self).get(request, initiative)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, initiative_id, format=None):
        try:
            author_details = {'name': request.data['name'], 'email': request.data['email']}
            author_details.update({'silent': False}) # by Marce: previously True. 
            self.api_method_params = author_details
            self.api_method = 'create_new_member'
            self.create_obj = cru_author
            self.serializer_class = AuthorSerializer
            initiative = Initiative.objects.get(id=initiative_id)
            return super(Authors,self).post(request, initiative)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp


class AuthorDetail(ISObjectDetail):
    """
    Retrieve or delete an author instance
    """
    queryset = Author
    serializer_class = AuthorSerializer

    def get(self, request, user_id, format=None):
        try:
            author = Author.objects.get(ideascale_id=user_id)
            self.initiative = author.initiative
            self.api_method = 'get_member_info_by_id'
            self.api_method_params = {'memberId': user_id}
            self.create_obj = cru_author
            return super(AuthorDetail, self).get(request, user_id)
        except Author.DoesNotExist, e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def delete(self, request, author_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)


class Comments(ISObject):
    """
    Return the list of comments or create a new one.
    """

    def get_initiative(self, initiative_id):
        try:
            return Initiative.objects.get(id=initiative_id)
        except Initiative.DoesNotExist:
            return Http404

    def get(self, request, initiative_id, format=None):
        self.api_method = 'get_all_comments'
        self.client_attr = 'last_comment'
        self.pag_params = {'page_number': self.PAGE_NUMBER, 'page_size': self.PAGE_SIZE}
        self.iterate = True
        self.create_obj = cru_comment
        self.queryset = Comment
        self.serializer_class = CommentSerializer
        self.filters = {'sync': False}
        initiative = self.get_initiative(initiative_id)
        return super(Comments,self).get(request, initiative)

    def post(self, request, initiative_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)


class CommentsIdea(ISObject):
    """
    Return the list of comments of an idea
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def get(self, request, idea_id, format=None):
        try:
            idea = Idea.objects.get(ideascale_id=idea_id)
            initiative = idea.campaign.initiative
            self.api_method = 'get_comments_idea'
            self.api_method_params = {'ideaId': idea_id}
            self.client_attr = 'last_comment_idea'
            self.create_obj = cru_comment
            self.queryset = Comment
            self.serializer_class = CommentSerializer
            self.filters = {'sync':False, 'parent_idea': idea}
            return super(CommentsIdea,self).get(request, initiative)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, idea_id, format=None):
        try:
            idea = Idea.objects.get(ideascale_id=idea_id)
            initiative = idea.campaign.initiative
            comment_details = {'text': request.data['text'], 'ideaId': idea_id}
            self.api_method = 'comment_idea'
            self.api_method_params = comment_details
            self.create_obj = cru_comment
            self.serializer_class = CommentSerializer
            self.filters = {'sync':True}
            return super(CommentsIdea,self).post(request, initiative)
        except Idea.DoesNotExist:
            return Response('Error: Idea with id {} does not exist'.format(idea_id), status=status.HTTP_400_BAD_REQUEST)


class CommentsComment(ISObject):
    """
    Return the list of comments of a comment
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_initiative(self, comment):
        if comment.parent_type == 'idea':
            return comment.parent_idea.campaign.initiative
        else:
            return self.get_initiative(comment.parent_comment)

    def get(self, request, comment_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, comment_id, format=None):
        try:
            comment = Comment.objects.get(ideascale_id=comment_id)
            initiative = self.get_initiative(comment)
            comment_details = {'text': request.data['text'], 'commentId': comment_id}
            self.api_method = 'comment_comment'
            self.api_method_params = comment_details
            self.create_obj = cru_comment
            self.serializer_class = CommentSerializer
            self.filters = {'sync':True}
            return super(CommentsComment,self).post(request, initiative)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp


class CommentDetail(ISObjectDetail):
    """
    Retrieve or delete an idea instance
    """
    queryset = Comment
    serializer_class = CommentSerializer

    def get_initiative(self, comment):
        if comment.parent_type == 'idea':
            return comment.parent_idea.campaign.initiative
        else:
            return self.get_initiative(comment.parent_comment)

    def get(self, request, comment_id, format=None):
        try:
            comment = Comment.objects.get(ideascale_id=comment_id)
            self.initiative = self.get_initiative(comment)
            self.api_method = 'get_comment'
            self.api_method_params = {'commentId': comment_id}
            self.create_obj = cru_comment
            return super(CommentDetail, self).get(request, comment_id)
        except Comment.DoesNotExist, e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def delete(self, request, comment_id, format=None):
        try:
            comment = Comment.objects.get(ideascale_id=comment_id)
            initiative = self.get_initiative(comment)
            api = get_api_obj(initiative)
            api.delete_comment(comment_id)
            return super(CommentDetail, self).delete(request, comment_id)
        except (Comment.DoesNotExist, IdeaScalyError) as e:
            return Response('Error: {}'.format(e.reason), status=status.HTTP_400_BAD_REQUEST)


class VotesIdeas(ISObject):
    """
    Return the list of all votes of all ideas.
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, initiative_id, format=None):
        try:
            self.api_method = 'get_all_votes_ideas'
            self.client_attr = 'last_vote'
            self.create_obj = cru_vote
            self.queryset = Vote
            self.serializer_class = VoteSerializer
            self.filters = {'sync': False}
            initiative = Initiative.objects.get(id=initiative_id)
            return super(VotesIdeas,self).get(request, initiative)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, initiative_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)


class VotesComments(ISObject):
    """
    Return the list of all votes of all comments.
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, initiative_id, format=None):
        try:
            self.api_method = 'get_all_votes_comments'
            self.client_attr = 'last_vote'
            self.create_obj = cru_vote
            self.queryset = Vote
            self.serializer_class = VoteSerializer
            self.filters = {'sync': False}
            initiative = Initiative.objects.get(id=initiative_id)
            return super(VotesComments,self).get(request, initiative)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, initiative_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)


class VotesIdea(ISObject):
    """
    Return the list of votes related to a particular idea.
    """

    def get(self, request, idea_id, format=None):
        try:
            idea = Idea.objects.get(ideascale_id=idea_id)
            initiative = idea.campaign.initiative
            self.api_method = 'get_votes_idea'
            self.client_attr = 'last_vote_idea'
            self.api_method_params = {'ideaId': idea_id}
            self.create_obj = cru_vote
            self.queryset = Vote
            self.serializer_class = VoteSerializer
            self.filters = {'sync':False}
            return super(VotesIdea, self).get(request, initiative)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, idea_id, format=None):
        try:
            idea = Idea.objects.get(ideascale_id=idea_id)
            initiative = idea.campaign.initiative
            if request.data['value'] > 0:
                self.api_method = 'vote_up_idea'
            else:
                self.api_method = 'vote_down_idea'
            votes_details = {'myVote': request.data['value'], 'ideaId': idea.ideascale_id}
            self.api_method_params = votes_details
            self.create_obj = cru_vote
            self.serializer_class = VoteSerializer
            self.filters = {'sync':True}
            return super(VotesIdea,self).post(request, initiative)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp



class VotesComment(ISObject):
    """
    Return the list of votes related to a comment idea.
    """

    def get_initiative(self, comment):
        if comment.parent_type == 'idea':
            return comment.parent_idea.campaign.initiative
        else:
            return self.get_initiative(comment.parent_comment)

    def get(self, request, comment_id, format=None):
        try:
            comment = Comment.objects.get(ideascale_id=comment_id)
            self.api_method = 'get_votes_comment'
            self.client_attr = 'last_vote_comment'
            self.api_method_params = {'commentId': comment_id}
            self.create_obj = cru_vote
            self.queryset = Vote
            self.serializer_class = VoteSerializer
            self.filters = {'sync': False}
            initiative = self.get_initiative(comment)
            return super(VotesComment, self).get(request, initiative)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, initiative_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)


class VoteDetail(ISObjectDetail):
    """
    Retrieve or delete a vote instance
    """
    queryset = Vote
    serializer_class = VoteSerializer

    def delete(self, request, vote_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)


def index(request):
    return HttpResponse('Welcome to Ideascale client API.')






