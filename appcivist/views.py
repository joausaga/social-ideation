from django.shortcuts import render

from dateutil.parser import parse

from django.http import HttpResponse, Http404
from django.utils import timezone

from ideascaly.auth import AuthNonSSO
from ideascaly.error import IdeaScalyError
from ideascaly.api import API

from appcivist.models import Assembly, Author, Campaign, Proposal, Comment, Feedback
from appcivist.serializers import AssemblySerializer, CampaignSerializer, AuthorSerializer, ContributionSerializer, CommentSerializer, FeedbackSerializer

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
# TODO s:
# 1- [x] el modelo initiative originalmente no tiene el atributo ideascale_id, puesto que no se requiere en las llamadas a la api
# en cambio, para appcivist, necesito que el modelo assembly si lo tenga, le agregue de hecho, pero necesito que esa sea su clave primaria
# y tambien necesito que cuando se busque un assembly, sea por appcivist_id, y no por id nomas como esta ahora
# 2- [x] Tengo que agregar los social_ideation headers al request
# 3- Tengo que crear las instancias de los modelos solamente cuando el artibuto removed == False
# 4- [x] Tengo que implementar los detele en el appcivist_client.py
# 5- tengo que ver si uso punto o [] en los obj
# 6- el nombre del id del obj_raw no necesariamente es id, sino que puede ser por ej id, o contributionId


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
    # auth = AuthNonSSO(initiative.token)
    # api = API(auth)
    # api.community_url = initiative.url

    api = appcivist_api()
    api.base_url = assembly.url
    api.session_key = assembly.session_key

    return api


# def get_ideascale_data(initiative, api_method, method_params=None, pag_params=None):
#     api = get_api_obj(initiative)
#     if not method_params and not pag_params:
#         objs = getattr(api, api_method)()
#     elif method_params:
#         if pag_params:
#             method_params.update(pag_params)
#         objs = getattr(api, api_method)(**method_params)
#     else:
#         objs = getattr(api, api_method)(**pag_params)
#     return objs

def get_appcivist_data(assembly, api_method, method_params=None, pag_params=None):
    api = get_api_obj(assembly)
    if not method_params:
        objs = getattr(api, api_method)()
    elif method_params:
        objs = getattr(api, api_method)(**method_params)
    return objs
    
    #     if pag_params:
    #         method_params.update(pag_params)
    #     objs = getattr(api, api_method)(**method_params)
    # else:
    #     objs = getattr(api, api_method)(**pag_params)
    # aca tengo que retornar la lista de objetos, sea cual fere lo que me trae

    # return objs

def cru_author(author_id, assembly, author_info=None):
    try:
        author = Author.objects.get(appcivist_id=author_id)
        if author_info:
            # Update obj before returning
            author.name = author_info.name
            if hasattr(author_info, "email"):
                author.email = author_info.email
            author.save()
        return author
    except Author.DoesNotExist:
        if not author_info:
            author_info = get_appcivist_data(assembly, 'get_author_info', {'uid': author_id})
        if hasattr(author_info, "email"):
            author = Author(appcivist_id=author_info.userId, name=author_info.name, email=author_info.email,
                            assembly=assembly)
        else:
            author = Author(appcivist_id=author_info.userId, name=author_info.name, assembly=assembly)
        author.save()
        return author


def cu_campaigns(assembly):
    campaigns_raw = get_appcivist_data(assembly, 'get_campaigns', {'aid': assembly.appcivist_id})
    for campaign_raw in campaigns_raw:
        try:
            campaign = Campaign.objects.get(appcivist_id=campaign_raw.id)
            campaign.name = campaign_raw.name
            campaign.save()
        except Campaign.DoesNotExist:
            campaign = Campaign(appcivist_id=campaign_raw.campaignId, appcivist_uuid=campaign.raw.uuid, name=campaign_raw.title, assembly=assembly, resource_space_id=campaign_raw.resourceSpaceId, forum_resource_space_id=campaign.forumResourceSpaceId)
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


# def cru_location(location_obj):
#     if location_obj['country'] and location_obj['city']:
#         country_utf8 = convert_to_utf8_str(location_obj['country'])
#         city_utf8 = convert_to_utf8_str(location_obj['city'])
#         code = '{}_{}'.format(country_utf8.strip().lower(), city_utf8.strip().lower())
#         try:
#             location = Location.objects.get(code=code)
#             if location_obj['longitude'] and location_obj['latitude']:
#                 location.longitude,  location.latitude = location_obj['longitude'], location_obj['latitude']
#                 location.save()
#             return location
#         except Location.DoesNotExist:
#             if location_obj['longitude'] and location_obj['latitude']:
#                 location = Location(country=location_obj['country'], city=location_obj['city'], code=code,
#                                     longitude=location_obj['longitude'], latitude=location_obj['latitude'])
#             else:
#                 location = Location(country=location_obj['country'], city=location_obj['city'], code=code)
#             location.save()
#             return location
#     else:
#         return None


def cru_proposal(proposal_id, assembly, proposal_obj=None):
    try:
        proposal = Proposal.objects.get(appcivist_id=proposal_id)
        if proposal_obj:
            proposal.title = proposal_obj.title
            proposal.text = proposal_obj.text
            proposal.positive_votes = proposal_obj.stats['ups']
            proposal.negative_votes = proposal_obj.stats['downs']
            proposal.comments = proposal_obj.commentCount
            proposal.campaign = cru_campaign(proposal_obj.campaignIds[0], assembly)
        proposal.sync = False
        proposal.save()
        return proposal
    except Proposal.DoesNotExist:
        if not proposal_obj:
            proposal_obj = get_appcivist_data(assembly, 'get_proposal_details', {'coid': proposal_id, 'aid': assembly.appcivist_id})
        author = cru_author(proposal_obj.firstAuthor['userId'], assembly, proposal_obj.firstAuthor)
        #location = cru_location(proposal_obj.locationInfo) if hasattr(proposal_obj, 'locationInfo') else None
        campaign_proposal = cru_campaign(proposal_obj.campaignIds[0], assembly)
        positive_votes = proposal_obj.stats['ups']
        negative_votes = proposal_obj.stats['downs']
        comments = proposal_obj.commentCount
        url = ""
        proposal_ac_dt = parse(proposal_obj.creation)
        proposal_dt = _get_timezone_aware_datetime(proposal_ac_dt) if timezone.is_naive(proposal_ac_dt) else proposal_ac_dt
        proposal = Proposal(appcivist_id=proposal_obj.contributionId, appcivist_uuid=proposal_obj.uuidAsString ,title=proposal_obj.title, text=proposal_obj.text,
                    datetime=proposal_dt, positive_votes=positive_votes, negative_votes=negative_votes, comments=comments,
                    campaign=campaign_proposal, url=url, user=author, sync=False)
        proposal.save()
        return proposal


# def get_parent_comment(comment, assembly):
#     if comment.parentType == 'proposal':
#         try:
#             return Proposal.objects.get(appcivist_id=comment.parentId)
#         except Idea.DoesNotExist:
#             return cru_idea(comment.parentId, assembly)
#     else:
#         try:
#             return Comment.objects.get(ideascale_id=comment.parentId)
#         except Comment.DoesNotExist:
#             return cru_comment(comment.parentId, assembly)

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
            comment.text = comment_obj.text
            comment.positive_votes = comment_obj.stats['ups']
            comment.negative_votes = comment_obj.stats['downs']
            comment.comments = comment_obj.commentCount
        comment.sync = False
        comment.save()
        return comment
    except Comment.DoesNotExist:
        if not comment_obj:
            comment_obj = get_appcivist_data(assembly, 'get_comment_details', {'coid': comment_id, 'aid': assembly.appcivist_id})
        author = cru_author(comment_obj.firstAuthor['userId'], assembly, comment_obj.firstAuthor)
        # location = cru_location(comment_obj.locationInfo) if hasattr(comment_obj, 'locationInfo') else None
        positive_votes = comment_obj.stats['ups']
        negative_votes = comment_obj.stats['downs']
        comments = comment_obj.commentCount
        url = ""
        if comment_obj.type == "DISCUSSION":
            parent_type = "proposal"
        else:
            parent_type = "comment"
        comment_ac_dt = parse(comment_obj.creation)
        comment_dt = _get_timezone_aware_datetime(comment_ac_dt) if timezone.is_naive(comment_ac_dt) else comment_ac_dt
        comment = Comment(appcivist_id=comment_obj.contributionId, appcivist_uuid=comment_obj.uuidAsString, text=comment_obj.text,
                          datetime=comment_dt, positive_votes=positive_votes, negative_votes=negative_votes,
                          comments=comments, url=url, user=author,
                          parent_type=parent_type, sync=False)
        # parent = get_parent_comment(comment_obj, assembly)
        parent_id = comment_obj.containingContributionsIds[0]
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
            if feedback_obj.up:
                feedback.value = 1
            elif feedback_obj.down:
                feedback.value = -1
            # if hasattr(vote_obj, 'voteValue'):
            #     feedback.value = feedback_obj.voteValue
            # elif hasattr(vote_obj, 'myVote'):
            #     feedback.value = vote_obj.myVote
            # if hasattr(vote_obj, 'ideaType'):
            #     feedback.parent_type = vote_obj.ideaType
        feedback.sync = False
        feedback.save()
        return feedback
    except Feedback.DoesNotExist:
        # author_id = vote_obj.authorId if hasattr(vote_obj, 'authorId') else vote_obj.memberId
        author_id = feedback_obj.userId
        author = cru_author(author_id, assembly)
        feedback_ac_dt = parse(vote_obj.creation)
        feedback_dt = _get_timezone_aware_datetime(feedback_ac_dt) if timezone.is_naive(feedback_ac_dt) else feedback_ac_dt
        # vote_parent_type = vote_obj.ideaType if hasattr(vote_obj, 'ideaType') else 'idea'
        # vote_value = vote_obj.voteValue if hasattr(vote_obj, 'voteValue') else vote_obj.myVote
        # vote_parent_id = vote_obj.ideaId if hasattr(vote_obj, 'ideaId') else vote_obj.id
        
        if feedback_obj.up:
            feedback_value = 1
        elif feedback_obj.down:
            feedback_value = -1
        feedback_parent_type = feedback_obj.parentType
        feedback_parent_id = feedback_obj.contributionId
        feedback = Feedback(appcivist_id=feedback_obj.id, value=feedback_value, datetime=feedback_dt, author=author, sync=False,
                    parent_type=feedback_parent_type)
        if feedback_parent_type == 'proposal':
            feedback.parent_proposal = cru_proposal(feedback_parent_id, assembly)
        else:
            feedback.parent_comment = cru_comment(feedback_parent_id, proposal)
        feedback.save()
        return feedback


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

    def get(self, request, assembly, format=None):
        call_api = True
        try:
            self.queryset.objects.all().update(sync=True)
            while call_api:
                objs_raw = get_appcivist_data(assembly, self.api_method, self.api_method_params, self.pag_params)
                if len(objs_raw) > 0:
                    for obj_raw in objs_raw:
                        self.create_obj(obj_raw.id, assembly, obj_raw)
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
        # except IdeaScalyError as e:
        #     resp = Response(status=status.HTTP_400_BAD_REQUEST)
        #     resp.content = 'Error: {}'.format(e.reason)
        #     return resp
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, assembly, format=None):
        try:
            api = get_api_obj(assembly)

            # TODO aca deberian venir como parte del request estos headers de social ideation
            api.ignore_admin_user = True
            api.social_ideation_source = reques.source # indicates the name of the providerId (e.g., social_ideation_facebook)
            api.social_ideation_source_url= request.source_url # source to the original post
            api.social_ideation_user_source_url= request.user_url # link to the user
            api.social_ideation_user_source_id= request.user_id # email or id of the user in the source social network

            new_obj_raw = getattr(api, self.api_method)(**self.api_method_params)
            new_obj= self.create_obj(new_obj_raw.id, assembly, new_obj_raw)
            serializer = self.serializer_class(new_obj)
            if self.filters:
                new_obj.sync = True
                new_obj.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        # except IdeaScalyError as e:
        #     resp = Response(status=status.HTTP_400_BAD_REQUEST)
        #     resp.content = 'Error: {}'.format(e.reason)
        #     return resp
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
    assembly = None
    create_obj = None
    queryset = None
    serializer_class = None

    def get(self, request, obj_id, format=None):
        try:
            api = get_api_obj(self.assembly)
            obj_raw = getattr(api, self.api_method)(**self.api_method_params)
            obj = self.create_obj(obj_raw.id, self.assembly, obj_raw)
            serializer = self.serializer_class(obj)
            return Response(serializer.data)
        # except IdeaScalyError as e:
        #     resp = Response(status=status.HTTP_400_BAD_REQUEST)
        #     resp.content = 'Error: {}'.format(e.reason)
        #     return resp
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
    """
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
            assembly = Assembly.objects.get(id=assembly_id)
            campaigns = cru_campaign(-100, assembly)
            serializer = CampaignSerializer(campaigns, many=True)
            return Response(serializer.data)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

class Proposals(ISObject):
    """
    Return the list of ideas or create a new one.
    """

    def get(self, request, assembly_id, format=None):
        try:
            self.api_method = 'get_all_proposals'
            self.pag_params = {'page_number': self.PAGE_NUMBER, 'page_size': self.PAGE_SIZE}
            self.iterate = True
            self.create_obj = cru_proposal
            self.queryset = Proposal
            self.serializer_class = ProposalSerializer
            self.filters = {'sync': False}
            self.client_attr = 'last_idea'
            assembly = Assembly.objects.get(id=assembly_id)
            self.api_method_params = {"aid" : assembly.appcivist_id}
            return super(Proposals, self).get(request, assembly)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, assembly_id, format=None):
        try:
            # new_proposal = {"status": "PUBLISHED", "title" : "MARCE'S PROPOSAL", "text" : "marce's proposal", "type": "PROPOSAL", "campaigns": [1]}
            # idea_details = {'title': request.data['title'], 'text': request.data['text'], 'campaignId': request.data['campaign_id']}
            proposal_details = {"status": "PUBLISHED", "titel": request.data["title"], "text": request.data["text"], "type": "PROPOSAL", "campaigns":[request.data['campaign_id']]}
            campaign = Campaign.objects.get(appcivist_id=request.data["campaign_id"])
            if 'tags' in request.data.keys():
                tags = [tag.strip() for tag in proposal_details['tags'].split(',')]
                proposal_details['tags'] = tags
            # self.api_method_params = idea_details
            self.api_method_params = {"sid": campaign.resource_space_id, "proposal": proposal_details}
            self.api_method = 'create_proposal'
            self.create_obj = cru_proposal
            self.serializer_class = ProposalSerializer
            self.filters = {}
            assembly = Assembly.objects.get(id=assembly_id)
            return super(Proposals,self).post(request, assembly)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp


class ProposalDetail(ISObjectDetail):
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
            self.api_method_params = {"aid": assembly.appcivist_id, "coid": proposal_id}
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
            # api.delete_idea(proposal_id)
            api.delete_proposal(aid=proposal.campaign.assembly.appcivist_id, coid=proposal.appcivist_id)
            return super(ProposalDetail, self).delete(request, proposal_id)
        except Exception as e:
            return Response('Error: {}'.format(e.reason), status=status.HTTP_400_BAD_REQUEST)

# ESTE CREO QUE NO VOY A USAR
# class IdeaAttachFile(APIView):
#     """
#     Attach a file to an idea
#     """
#     authentication_classes = (TokenAuthentication,)
#     permission_classes = (IsAuthenticated,)

#     def get(self, request, idea_id, format=None):
#         return Response(status=status.HTTP_400_BAD_REQUEST)

#     def post(self, request, idea_id, format=None):
#         try:
#             file_name = request.data['file_str']
#             file_path = str(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
#                                          'static/{}'.format(file_name)))
#             idea = Idea.objects.get(ideascale_id=idea_id)
#             api = get_api_obj(idea.campaign.initiative)
#             api.attach_file_to_idea(filename=file_path, ideaId=idea_id)
#             return HttpResponse('OK', status=status.HTTP_200_OK)
#         except IdeaScalyError as e:
#             return Response('Error: {}'.format(e.reason), status=status.HTTP_400_BAD_REQUEST)


class Authors(ISObject):
    """
    Return the list of users or create a new one.
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, assembly_id, format=None):
        try:
            self.api_method = 'get_all_authors'
            self.pag_params = {'page_number': self.PAGE_NUMBER, 'page_size': self.PAGE_SIZE}
            self.iterate = True
            self.create_obj = cru_author
            self.queryset = Author
            self.serializer_class = AuthorSerializer
            assembly = Assembly.objects.get(appcivist_id=assembly_id)
            self.method_params = {"aid" : assembly.appcivist_id}
            return super(Authors,self).get(request, assembly)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp
    # TODO. este parece que no voy a usar. Por ahora no toque. Mejor comentar
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


class AuthorDetail(ISObjectDetail):
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


class Comments(ISObject):
    """
    Return the list of comments or create a new one.
    """

    def get_assembly(self, assembly_id):
        try:
            return Assembly.objects.get(id=assembly_id)
        except Assembly.DoesNotExist:
            return Http404

    def get(self, request, assembly_id, format=None):
        self.api_method = 'get_all_comments'
        self.client_attr = 'last_comment'
        self.pag_params = {'page_number': self.PAGE_NUMBER, 'page_size': self.PAGE_SIZE}
        self.iterate = True
        self.create_obj = cru_comment
        self.queryset = Comment
        self.serializer_class = CommentSerializer
        self.filters = {'sync': False}
        assembly = self.get_assembly(assembly_id)
        self.method_params = {"aid", assembly.appcivist_id}
        return super(Comments,self).get(request, assembly)

    def post(self, request, assembly_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)


class CommentsProposal(ISObject):
    """
    Return the list of comments of an idea
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def get(self, request, proposal_id, format=None):
        try:
            proposal = Proposal.objects.get(appcivist_id=idea_id)
            assembly = proposal.campaign.assembly
            self.api_method = 'get_comments_of_proposal'
            self.api_method_params = {'sid': proposal.resource_space_id}
            self.client_attr = 'last_comment_idea'
            self.create_obj = cru_comment
            self.queryset = Comment
            self.serializer_class = CommentSerializer
            self.filters = {'sync':False, 'parent_idea': proposal}
            return super(CommentsIdea,self).get(request, assembly)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, proposal_id, format=None):
        try:
            proposal = Proposal.objects.get(appcivist_id=proposal_id)
            assembly = proposal.campaign.assembly
            # new_proposal = {"status": "NEW", "title" : "prueba marce 2 con campaigns", "text" : "this is a test without location", "type": "PROPOSAL", "campaigns": [1]}
            # comment_details = {'text': request.data['text'], 'ideaId': idea_id}
            comment_details = {"status": "PUBLISHED", "text": request.data["text"], "type": "DISCUSSION", "campaigns":[request.data['campaign_id']]}
            self.api_method = 'comment_proposal'
            self.api_method_params = {"sid": proposal.resource_space_id, "discussion": comment_details}
            self.create_obj = cru_comment
            self.serializer_class = CommentSerializer
            self.filters = {'sync':True}
            return super(CommentsProposal,self).post(request, assembly)
        except Proposal.DoesNotExist:
            return Response('Error: Idea with id {} does not exist'.format(proposal_id), status=status.HTTP_400_BAD_REQUEST)


class CommentsComment(ISObject):
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
            # comment_details = {'text': request.data['text'], 'commentId': comment_id}
            comment_details = {"status": "PUBLISHED", "text": request.data["text"], "type": "COMMENT", "campaigns":[request.data['campaign_id']]}
            self.api_method_params = {"sid": comment.resource_space_id, "comment": comment_details}
            # self.api_method_params = comment_details
            self.create_obj = cru_comment
            self.serializer_class = CommentSerializer
            self.filters = {'sync':True}
            return super(CommentsComment,self).post(request, assembly)
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
            # api.delete_comment(comment_id)
            api.delete_comment(aid=assembly.appcivist_id, coid=comment.appcivist_id)
            return super(CommentDetail, self).delete(request, comment_id)
        except Exception as e:
            return Response('Error: {}'.format(e.reason), status=status.HTTP_400_BAD_REQUEST)


class FeedbacksProposals(ISObject):
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
            assembly = Assembly.objects.get(id=assembly_id)
            return super(FeedbacksProposals,self).get(request, assembly)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, assembly_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)


class FeedbacksComments(ISObject):
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
            assembly = Assembly.objects.get(id=assembly_id)
            return super(FeedbacksComments,self).get(request, assembly)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp

    def post(self, request, assembly_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)


class FeedbacksProposal(ISObject):
    """
    Return the list of votes related to a particular idea.
    """

    def get(self, request, proposal_id, format=None):
        try:
            proposal = Proposal.objects.get(appcivist_id=proposal_id)
            assembly = proposal.campaign.assembly
            self.api_method = 'get_feedbacks_of_proposal'
            self.client_attr = 'last_vote_idea'
            # self.api_method_params = {'ideaId': proposal_id}
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
            # votes_details = {'myVote': request.data['value'], 'ideaId': idea.appcivist_id}
            # self.api_method_params = votes_details
            self.api_method_params = {"caid": assembly.campaign.appcivist_id, "coid": proposal.appcivist_id}
            self.create_obj = cru_feedback
            self.serializer_class = FeedbackSerializer
            self.filters = {'sync':True}
            return super(FeedbacksProposal,self).post(request, assembly)
        except Exception as e:
            resp = Response(status=status.HTTP_400_BAD_REQUEST)
            resp.content = e
            return resp



class FeedbacksComment(ISObject):
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
            # self.api_method_params = {'commentId': comment_id}
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
    # TODO que acaso este no tiene que ser para poder votar los comments en el consultation platform?
    def post(self, request, assembly_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)


class FeedbackDetail(ISObjectDetail):
    """
    Retrieve or delete a vote instance
    """
    queryset = Feedback
    serializer_class = FeedbackSerializer

    def delete(self, request, vote_id, format=None):
        return Response(status=status.HTTP_400_BAD_REQUEST)


def index(request):
    return HttpResponse('Welcome to Appcivist client API.')




