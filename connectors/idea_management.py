import abc
import app.models
import logging

from ideascaly.auth import AuthNonSSO
from ideascaly.api import API



logger = logging.getLogger(__name__)

# ---------------------------
# Abstract class from where all idea management
# platform connectors must inherent from
# ----------------------------

class IdeaMgmt():
    __metaclass__ = abc.ABCMeta

    @staticmethod
    @abc.abstractmethod
    def get_campaigns(url):
        """Get campaigns associated with the initiative run in url"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def get_ideas(campaign_id):
        """Get ideas within the campaign_id"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def get_idea(idea_id):
        """Get details about idea_id"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def post_idea(title, text, campaign_id=None, tags=None):
        """Publish a new post"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def edit_idea(idea_id):
        """Edit the idea identified by idea_id"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def delete_idea(idea_id):
        """Delete the post identified by idea_id"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def vote_idea(idea_id, type_vote=None):
        """Vote up/down (type_vote) idea identified by idea_id. Up vote is type_vote is None"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def comment_idea(idea_id, text):
        """Comment the idea identified by idea_id"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def delete_comment(comment_id):
        """Remove comment (comment_id)"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def create_user(name, email):
        """Create a new user"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def get_user(user_id):
        """Get information about a particular user"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def delete_user(user_id):
        """Delete user identified with user_id"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def attach_file_idea(idea_id, filename):
        """Attach file identified with filename to the idea identified with idea_id"""
        raise NotImplementedError


class IdeaScale(IdeaMgmt):

    @staticmethod
    def get_campaigns(initiative_id):
        ini = app.models.Initiative.objects.get(pk=initiative_id)
        auth = AuthNonSSO(ini.token_idea_mgmt_platform)
        api = API(auth)
        api.community_url = ini.url_idea_mgmt_platform
        return api.get_campaigns()

    @staticmethod
    def get_ideas(campaign_id):
        """Get ideas within the campaign_id"""
        raise NotImplementedError

    @staticmethod
    def get_idea(idea_id):
        """Get details about idea_id"""
        raise NotImplementedError

    @staticmethod
    def post_idea(title, text, campaign_id=None, tags=None):
        """Publish a new post"""
        raise NotImplementedError

    @staticmethod
    def edit_idea(idea_id):
        """Edit the idea identified by idea_id"""
        raise NotImplementedError

    @staticmethod
    def delete_idea(idea_id):
        """Delete the post identified by idea_id"""
        raise NotImplementedError

    @staticmethod
    def vote_idea(idea_id, type_vote=None):
        """Vote up/down (type_vote) idea identified by idea_id. Up vote is type_vote is None"""
        raise NotImplementedError

    @staticmethod
    def comment_idea(idea_id, text):
        """Comment the idea identified by idea_id"""
        raise NotImplementedError

    @staticmethod
    def delete_comment(comment_id):
        """Remove comment (comment_id)"""
        raise NotImplementedError

    @staticmethod
    def create_user(name, email):
        """Create a new user"""
        raise NotImplementedError

    @staticmethod
    def get_user(user_id):
        """Get information about a particular user"""
        raise NotImplementedError

    @staticmethod
    def delete_user(user_id):
        """Delete user identified with user_id"""
        raise NotImplementedError

    @staticmethod
    def attach_file_idea(idea_id, filename):
        """Attach file identified with filename to the idea identified with idea_id"""
        raise NotImplementedError