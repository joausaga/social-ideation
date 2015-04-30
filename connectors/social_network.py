import abc

# Abstract class from where
# all social network connectors must
# inherent from

class SocialNetwork():
    __metaclass__ = abc.ABCMeta

    @staticmethod
    @abc.abstractmethod
    def authenticate():
        """Authenticate to the channel"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def search_posts(accounts, hashtags):
        """Search for posts containing the hashtags"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def publish_post(text):
        """Publish a new post"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def edit_post(id_post):
        """Edit the post identified by id_post"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def delete_post(id_post):
        """Delete the post identified by id_post"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def get_post(id_post):
        """Get the post identified by id_post"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def vote_post(id_post, type_vote):
        """Vote up/down (type_vote) post identified by id_post"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def delete_vote_post(id_post, id_vote):
        """Remove vote (id_vote) placed for the post identified by id_post"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def comment_post(id_post, text):
        """Comment the post identified by id_post"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def delete_comment_post(id_post, id_comment):
        """Remove comment (id_comment) placed for the post identified by id_post"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def get_info_user(id_user):
        """Get information about a particular user"""
        raise NotImplementedError


class Facebook(SocialNetwork):
    pass