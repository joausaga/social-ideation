from connectors.error import ConnectorError

import abc
import ConfigParser
import facebook
import os
import requests

class SocialNetworkBase():
    # Abstract base class from where
    # all social network connectors must
    # inherent from
    __metaclass__ = abc.ABCMeta

    @classmethod
    @abc.abstractmethod
    def authenticate(cls):
        """Authenticate to the channel"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_posts(cls):
        """Search for posts published to the page"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def publish_post(cls, message):
        """Publish a new post"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def edit_post(cls, id_post, message):
        """Edit the post identified by id_post"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def delete_post(cls, id_post):
        """Delete the post identified by id_post"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_post(cls, id_post):
        """Get the post identified by id_post"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def vote_post(cls, id_post, type_vote=None):
        """Vote up/down (type_vote) post identified by id_post"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def delete_vote_post(cls, id_post, id_vote):
        """Remove vote (id_vote) placed for the post identified by id_post"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def comment_post(cls, id_post, message):
        """Comment the post identified by id_post"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def comment_comment(cls, id_comment, message):
        """Comment the comment identified by id_comment"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def edit_comment(cls, id_comment, message):
        """Edit the comment identified by id_comment"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def delete_comment(cls, id_comment):
        """Remove comment (id_comment) placed for the post identified by id_post"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def delete_vote_comment(cls, id_comment, id_vote):
        """Remove vote (id_vote) placed for the comment identified by id_comment"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_info_user(cls, id_user):
        """Get information about a particular user"""
        raise NotImplementedError


class Facebook(SocialNetworkBase):
    graph = None
    config_manager = None

    @classmethod
    def get_long_lived_access_token(cls):
        access_token = cls.config_manager.get('facebook', 'access_token')
        app_id = cls.config_manager.get('facebook', 'app_id')
        app_secret = cls.config_manager.get('facebook', 'app_secret')
        url = 'https://graph.facebook.com/oauth/access_token?client_id={}&client_secret={}&grant_type=fb_exchange_token&fb_exchange_token={}'
        resp = requests.get(url=url.format(app_id,app_secret,access_token))
        if resp.status_code and not 200 <= resp.status_code < 300:
            raise ConnectorError('Error when trying to get long-lived access token')
        else:
            str_resp = resp.text
            return str_resp.split('&')[0].split('=')[1]

    @classmethod
    def get_long_lived_page_token(cls):
        access_token = cls.get_long_lived_access_token()
        graph = facebook.GraphAPI(access_token)
        # Get page token to post as the page
        resp = graph.get_object('me/accounts')
        for page in resp['data']:
            if page['id'] == cls.config_manager.get('facebook', 'page_id'):
                print page['access_token']
                return page['access_token']
        raise ConnectorError('Couldn\'t get long-lived page token')

    @classmethod
    def authenticate(cls):
        config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'connectors/config')
        try:
            cls.config_manager = ConfigParser.ConfigParser()
            cls.config_manager.read(config_file)
            long_lived_page_token = cls.config_manager.get('facebook', 'page_token')
        except ConfigParser.NoOptionError:
            long_lived_page_token = cls.get_long_lived_page_token()
            cls.config_manager.set('facebook', 'page_token', long_lived_page_token)
            # Save long-lived page token --which doesn't expire-- to use later
            with open(config_file, 'wb') as configfile:
                cls.config_manager.write(configfile)
        cls.graph = facebook.GraphAPI(long_lived_page_token)

    @classmethod
    def build_post_dict(cls, post_raw):
        post_dict = {'id': post_raw['id'], 'text': post_raw['message'], 'title': '',
                     'user_info': {'name': post_raw['from']['name'], 'id': post_raw['from']['id']},
                     'url': post_raw['actions'][0]['link'], 'datetime': post_raw['created_time'],
                     'positive_votes': 0, 'negative_votes': 0, 'comments': 0}
        return post_dict

    @classmethod
    def build_comment_dict(cls, comment_raw, parent_type, parent_id):
        comment_dict = {'id': comment_raw['id'], 'text': comment_raw['message'],
                        'user_info': {'name': comment_raw['from']['name'], 'id': comment_raw['from']['id']},
                        'datetime': comment_raw['created_time'], 'positive_votes': 0, 'negative_votes': 0, 'url': None,
                        'parent_type': parent_type, 'parent_id': parent_id, 'comments': 0}
        return comment_dict

    @classmethod
    def build_like_dict(cls, like_raw, parent_type, parent_id):
        like_dict = {'id': parent_id+'_'+like_raw['id'], 'user_info': {'id': like_raw['id'], 'name': like_raw['name']},
                     'parent_type': parent_type, 'parent_id': parent_id, 'value': 1}
        return like_dict

    @classmethod
    def get_elements(cls, elements, type_element, parent_type=None, parent_id=None):
        elements_array = []
        while True:
            try:
                for element in elements['data']:
                    if type_element == 'posts':
                        post_dict = cls.build_post_dict(element)
                        if 'comments' in element.keys():
                            comments_array = cls.get_elements(element['comments'], 'comments', 'post', element['id'])
                            post_dict.update({'comments_array': comments_array})
                            post_dict.update({'comments': len(comments_array)})
                        if 'likes' in element.keys():
                            likes_array = cls.get_elements(element['likes'], 'likes', 'post', element['id'])
                            post_dict.update({'positive_votes': len(likes_array)})
                            post_dict.update({'votes_array': likes_array})
                        elements_array.append(post_dict)
                    elif type_element == 'comments':
                        comment_dict = cls.build_comment_dict(element, parent_type, parent_id)
                        replies = cls.graph.get_connections(element['id'], 'comments')
                        if len(replies['data']) > 0:
                            reply_array = cls.get_elements(replies, 'comments', 'comment', element['id'])
                            comment_dict.update({'comments': len(reply_array)})
                            comment_dict.update({'comments_array': reply_array})
                        likes = cls.graph.get_connections(element['id'], 'likes')
                        if len(likes['data']) > 0:
                            likes_array = cls.get_elements(likes, 'likes', 'comment', element['id'])
                            comment_dict.update({'positive_votes': len(likes_array)})
                            comment_dict.update({'votes_array': likes_array})
                        elements_array.append(comment_dict)
                    else:
                        like_dict = cls.build_like_dict(element, parent_type, parent_id)
                        elements_array.append(like_dict)
                # Attempt to make a request to the next page of data, if it exists
                elements = requests.get(elements['paging']['next']).json()
            except KeyError:
                # When there are no more pages (['paging']['next']), break from the loop
                return elements_array

    @classmethod
    def get_posts(cls):
        posts = cls.graph.get_connections(cls.config_manager.get('facebook', 'page_id'), 'feed')
        posts_array = cls.get_elements(posts, 'posts')
        return posts_array

    @classmethod
    def publish_post(cls, message):
        return cls.graph.put_wall_post(message)

    @classmethod
    def edit_post(cls, id_post, new_message):
        return cls.graph.request(cls.graph.version + "/" + id_post, post_args={'message': new_message}, method="POST")
        #  cls.graph.edit_message_post(post_id=id_post, message=new_message)

    @classmethod
    def delete_post(cls, id_post):
        cls.graph.delete_object(id=id_post)

    @classmethod
    def get_post(cls, id_post):
        return cls.build_post_dict(cls.graph.get_object(id=id_post))

    @classmethod
    def vote_post(cls, id_post, type_vote=None):
        cls.graph.put_like(object_id=id_post)

    @classmethod
    def delete_vote_post(cls, id_post, id_vote):
        cls.graph.request(cls.graph.version + "/" + id_post + "/likes", method="DELETE")
        # cls.graph.delete_like(id_post)

    @classmethod
    def comment_post(cls, id_post, message):
        return cls.graph.put_comment(object_id=id_post, message=message)

    @classmethod
    def edit_comment(cls, id_comment, message):
        return cls.graph.request(cls.graph.version + "/" + id_comment, post_args={'message': message}, method="POST")

    @classmethod
    def delete_comment(cls, id_comment):
        cls.graph.delete_object(id=id_comment)

    @classmethod
    def delete_vote_comment(cls, id_comment, id_vote):
        cls.graph.request(cls.graph.version + "/" + id_comment + "/likes", method="DELETE")
        # cls.graph.delete_like(id_comment)

    @classmethod
    def get_info_user(cls, id_user):
        raw_user = cls.graph.get_object(id_user)
        return {'id': raw_user['id'], 'name': raw_user['name'], 'url': raw_user['link']}

if __name__ == "__main__":
    Facebook.authenticate()
    #print Facebook.get_posts()
    #Facebook.publish_post('Hello from social_network.py!')
    #print Facebook.get_info_user('435131070002704')