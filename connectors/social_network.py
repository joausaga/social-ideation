from app.utils import calculate_token_expiration_time
from connectors.error import ConnectorError

import abc
import facebook
import logging
import json
import requests
import urllib

logger = logging.getLogger(__name__)

class SocialNetworkBase():
    # Abstract base class from where
    # all social network connectors must
    # inherent from
    __metaclass__ = abc.ABCMeta

    @classmethod
    @abc.abstractmethod
    def authenticate(cls, app):
        """Authenticate to the channel"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_posts(cls, app):
        """Search for posts published to the page"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def publish_post(cls, app, message):
        """Publish a new post"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def edit_post(cls, app, id_post, message):
        """Edit the post identified by id_post"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def delete_post(cls, app, id_post):
        """Delete the post identified by id_post"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_post(cls, app, id_post):
        """Get the post identified by id_post"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def vote_post(cls, app, id_post, type_vote=None):
        """Vote up/down (type_vote) post identified by id_post"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def delete_vote_post(cls, app, id_post, id_vote):
        """Remove vote (id_vote) placed for the post identified by id_post"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def comment_post(cls, app, id_post, message):
        """Comment the post identified by id_post"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def comment_comment(cls, app, id_comment, message):
        """Comment the comment identified by id_comment"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def edit_comment(cls, app, id_comment, message):
        """Edit the comment identified by id_comment"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def delete_comment(cls, app, id_comment):
        """Remove comment (id_comment) placed for the post identified by id_post"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def delete_vote_comment(cls, app, id_comment, id_vote):
        """Remove vote (id_vote) placed for the comment identified by id_comment"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_comment(cls, app, id_comment):
        """Get the comment identified by id_comment"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_info_user(cls, app, id_user):
        """Get information about a particular user"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def error_handler(cls, method, error_obj):
        """Handler request errors"""
        raise NotImplementedError


class Facebook(SocialNetworkBase):
    graph = None
    config_manager = None
    host = 'https://graph.facebook.com'
    ver = 'v2.4'
    api_real_time_subscription = host + '/' + ver + '/{}/' + 'subscriptions'
    api_app_page_subscription = host + '/' + ver + '/{}/' + 'subscribed_apps'

    @classmethod
    def get_long_lived_access_token(cls, app_id, app_secret, access_token):
        url = cls.host + \
              '/oauth/access_token?client_id={}&client_secret={}&grant_type=fb_exchange_token&fb_exchange_token={}'
        resp = requests.get(url=url.format(app_id,app_secret,access_token))
        if resp.status_code and not 200 <= resp.status_code < 300:
            raise ConnectorError('Error when trying to get long-lived access token')
        else:
            json_resp = json.loads(resp.text)
            return {'access_token': json_resp['access_token'], 'expiration': json_resp['expires_in']}


    @classmethod
    def get_long_lived_page_token(cls, app_id, app_secret, access_token, page_id):
        access_token = cls.get_long_lived_access_token(app_id, app_secret, access_token)['access_token']
        graph = facebook.GraphAPI(access_token)
        # Get page token to post as the page
        resp = graph.get_object('me/accounts')
        for page in resp['data']:
            if page['id'] == page_id:
                return page['access_token']
        raise ConnectorError('Couldn\'t get page long-lived token')

    @classmethod
    def get_code(cls, app_id, app_secret, app_redirect_uri, access_token):
        url = cls.host + \
             '/oauth/client_code?access_token={}&client_secret={}&redirect_uri={}&client_id={}'
        resp = requests.get(url=url.format(access_token, app_secret, app_redirect_uri, app_id))
        if resp.status_code and not 200 <= resp.status_code < 300:
            raise ConnectorError('Error when trying to get the code')
        else:
            json_resp = json.loads(resp.text)
            return json_resp['code']

    @classmethod
    def authenticate(cls, app, type_auth=None, app_user=None):
        if app.community.type == 'page':
            if not app.community.token:
                token = cls.get_long_lived_page_token(app.app_id, app.app_secret,
                                                      app.app_access_token,
                                                      app.community.external_id)
                app.community.token = token
                app.community.save()
            else:
                token = app.community.token
        else:  # community type = group
            if type_auth == 'write':  # User access_token
                code = cls.get_code(app.app_id, app.app_secret, app.redirect_uri, app_user.access_token)
                graph = facebook.GraphAPI(app_user.access_token)
                access_token_info = graph.get_access_token_from_code(code, app.redirect_uri,
                                                                        app.app_id, app.app_secret)
                token = access_token_info['access_token']
                app_user.access_token = token
                app_user.access_token_exp = calculate_token_expiration_time(access_token_info['expires_in'])
                app_user.save()
            else:
                if app.app_access_token:
                    token = app.app_access_token
                else:
                    token = facebook.get_app_access_token(app.app_id, app.app_secret)
                    app.app_access_token = token
                    app.save()
        cls.graph = facebook.GraphAPI(token)

    @classmethod
    def build_post_dict(cls, post_raw):
        if not 'message' in post_raw.keys() or not post_raw['message'].strip():
            # Posts without text are ignored
            return None
        post_dict = {'id': post_raw['id'], 'text': post_raw['message'], 'title': '',
                     'user_info': {'name': post_raw['from']['name'], 'id': post_raw['from']['id']},
                     'url': post_raw['actions'][0]['link'], 'datetime': post_raw['created_time'],
                     'positive_votes': 0, 'negative_votes': 0, 'comments': 0}
        if 'story' in post_raw.keys():
            post_dict.update({'story': True})
        return post_dict

    @classmethod
    def build_comment_dict(cls, comment_raw, parent_type=None, parent_id=None):
        if not comment_raw['message'].strip():
            # Comments without text are ignored
            return None
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
    def get_elements(cls, elements, type_elements, parent_type=None, parent_id=None):
        elements_array = []
        while True:
            try:
                for element in elements['data']:
                    if type_elements == 'posts':
                        post_dict = cls.get_element(element, 'post')
                        if post_dict: elements_array.append(post_dict)
                    elif type_elements == 'comments':
                        comment_dict = cls.get_element(element, 'comment', parent_type, parent_id)
                        if comment_dict: elements_array.append(comment_dict)
                    else:
                        like_dict = cls.get_element(element, 'like', parent_type, parent_id)
                        elements_array.append(like_dict)
                # Attempt to make a request to the next page of data, if it exists
                elements = requests.get(elements['paging']['next']).json()
            except KeyError:
                # When there are no more pages (['paging']['next']), break from the loop
                return elements_array

    @classmethod
    def get_element(cls, element, type_element, parent_type=None, parent_id=None):
        if type_element == 'post':
            post_dict = cls.build_post_dict(element)
            if post_dict:
                if 'comments' in element.keys():
                    comments_array = cls.get_elements(element['comments'], 'comments', 'post', element['id'])
                    post_dict.update({'comments_array': comments_array})
                    post_dict.update({'comments': len(comments_array)})
                if 'likes' in element.keys():
                    likes_array = cls.get_elements(element['likes'], 'likes', 'post', element['id'])
                    post_dict.update({'positive_votes': len(likes_array)})
                    post_dict.update({'votes_array': likes_array})
            return post_dict
        elif type_element == 'comment':
            comment_dict = cls.build_comment_dict(element, parent_type, parent_id)
            if comment_dict:
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
            return comment_dict
        else:
            like_dict = cls.build_like_dict(element, parent_type, parent_id)
            return like_dict

    @classmethod
    def get_posts(cls, app):
        cls.authenticate(app)
        posts = cls.graph.get_connections(app.community.external_id, 'feed')
        posts_array = cls.get_elements(posts, 'posts')
        return posts_array

    @classmethod
    def publish_post(cls, app, message, msg_attachment=None, app_user=None):
        cls.authenticate(app, 'write', app_user)
        if msg_attachment:
            return cls.graph.put_object(app.community.external_id, 'feed', message,
                                        attachment=msg_attachment)
        else:
            return cls.graph.put_object(app.community.external_id, 'feed', message)

    @classmethod
    def edit_post(cls, app, id_post, new_message, app_user=None):
        cls.authenticate(app, 'write', app_user)
        return cls.graph.request(cls.graph.version + '/' + id_post,
                                 post_args={'message': new_message},
                                 method='POST')
        #  cls.graph.edit_message_post(post_id=id_post, message=new_message)

    @classmethod
    def delete_post(cls, app, id_post, app_user=None):
        cls.authenticate(app, 'write', app_user)
        cls.graph.delete_object(id=id_post)

    @classmethod
    def get_post(cls, app, id_post):
        try:
            cls.authenticate(app)
            raw_post = cls.graph.get_object(id=id_post)
            return cls.get_element(raw_post, 'post')
        except facebook.GraphAPIError as e:
            return None

    @classmethod
    def vote_post(cls, app, id_post, type_vote=None, app_user=None):
        cls.authenticate(app, 'write', app_user)
        cls.graph.put_like(object_id=id_post)

    @classmethod
    def delete_vote_post(cls, app, id_post, id_vote, app_user=None):
        cls.authenticate(app, 'write', app_user)
        cls.graph.request(cls.graph.version + '/' + id_post + '/likes', method='DELETE')
        # cls.graph.delete_like(id_post)

    @classmethod
    def comment_post(cls, app, id_post, message, app_user=None):
        cls.authenticate(app, 'write', app_user)
        return cls.graph.put_comment(object_id=id_post, message=message)

    @classmethod
    def edit_comment(cls, app, id_comment, message, app_user=None):
        cls.authenticate(app, 'write', app_user)
        return cls.graph.request(cls.graph.version + '/' + id_comment,
                                 post_args={'message': message}, method='POST')

    @classmethod
    def delete_comment(cls, app, id_comment, app_user=None):
        cls.authenticate(app, 'write', app_user)
        cls.graph.delete_object(id=id_comment)

    @classmethod
    def delete_vote_comment(cls, app, id_comment, id_vote, app_user=None):
        cls.authenticate(app, 'write', app_user)
        cls.graph.request(cls.graph.version + '/' + id_comment + '/likes',
                          method='DELETE')
        # cls.graph.delete_like(id_comment)

    @classmethod
    def get_comment(cls, app, id_comment):
        try:
            cls.authenticate(app)
            raw_comment = cls.graph.get_object(id=id_comment)
            return cls.get_element(raw_comment, 'comment')
        except facebook.GraphAPIError as e:
            return None

    @classmethod
    def get_info_user(cls, app, id_user, access_token=None):
        if access_token:
            cls.graph = facebook.GraphAPI(access_token)
        else:
            cls.authenticate(app)
        raw_user = cls.graph.get_object(id_user)
        user = {'id': raw_user['id'], 'name': raw_user['name']}
        if 'link' in raw_user.keys():
            user.update({'url': raw_user['link']})
        if 'email' in raw_user.keys():
            user.update({'email': raw_user['email']})
        return user

    @classmethod
    def error_handler(cls, method, error_obj, params=None):
        logger.warning('Error when trying to call the method {}. Reason: {}'.format(method, error_obj))
        if 'Error validating access token' in error_obj:
            # TODO: There is a problem with the access token, notify the user.
            # User's email is saved in params
            pass
        else:
            raise ConnectorError(error_obj)

    @classmethod
    def _get_req_error_msg(cls, resp_text):
        err_msg = 'Error when trying to make the subscription to receive real time updates'
        if 'error' in resp_text.keys() and 'message' in resp_text['error'].keys():
            return '{}. Message: {}'.format(err_msg, resp_text['error']['message'])
        else:
            return err_msg

    @classmethod
    def subscribe_real_time_updates(cls, app, data):
        cls.authenticate(app)
        url = cls.api_app_page_subscription.format(app.community.external_id)
        data_token = ({'access_token': app.community.token})
        resp = requests.post(url=url, data=data_token)
        resp_text = json.loads(resp.text)
        if resp.status_code and not 200 <= resp.status_code < 300:
            raise ConnectorError(cls._get_req_error_msg(resp_text))
        else:
            if not app.app_access_token:
                access_token = facebook.get_app_access_token(app.app_id, app.app_secret)
            else:
                access_token = app.app_access_token
            data.update({'access_token': access_token})
            url = cls.api_real_time_subscription.format(app.app_id)
            resp = requests.post(url=url, data=data)
            resp_text = json.loads(resp.text)
            if resp.status_code and not 200 <= resp.status_code < 300:
                raise ConnectorError(cls._get_req_error_msg(resp_text))
            else:
                return resp_text

    @classmethod
    def delete_subscription_real_time_updates(cls, app, data):
        if not app.app_access_token:
            access_token = facebook.get_app_access_token(app.app_id, app.app_secret)
        else:
            access_token = app.app_access_token
        data.update({'access_token': access_token})
        url = cls.api_real_time_subscription.format(app.app_id)
        resp = requests.delete(url=url, data=data)
        resp_text = json.loads(resp.text)
        if resp.status_code and not 200 <= resp.status_code < 300:
            raise ConnectorError(cls._get_req_error_msg(resp_text))
        else:
            return resp_text

    @classmethod
    def create_batch_request(cls, msg, uri, msg_attachment=None, access_token=None):
        if access_token:
            req_uri = uri + '?access_token={}'.format(access_token)
        else:
            req_uri = uri
        if msg_attachment:
            body = msg_attachment
            body.update({'message': msg})
        else:
            body = {'message': msg}
        return {'method': 'POST', 'relative_url': req_uri,
                'body': urllib.urlencode(body),
                'omit_response_on_success': False}

    @classmethod
    def make_batch_request(cls, app, batch):
        if not app.app_access_token:
            access_token = facebook.get_app_access_token(app.app_id, app.app_secret)
        else:
            access_token = app.app_access_token
        ret = cls.graph.request(cls.graph.version + "/",
                                post_args={'batch': json.dumps(batch),
                                           'access_token': access_token,
                                           'include_headers': 'false'},
                                method='POST')
        return ret

    @classmethod
    def get_community_member_list(cls, app, group_id):
        cls.authenticate(app)
        members_email = []
        member_list = cls.graph.get_connections(group_id, 'members')
        #print member_list
        #for member in member_list['data']:
        #    members_email.append(member['id'])
        #return members_email
        while (True):
            for member in member_list['data']:
                members_email.append(member['id'])
            try:    
                member_list = requests.get(member_list['paging']['next']).json()
            except:
                break

        return members_email

    @classmethod
    def get_user_permissions(cls, app, user_id):
        cls.authenticate(app)
        return cls.graph.get_connections(user_id, 'permissions')

#if __name__ == "__main__":
#Facebook.authenticate()
#print Facebook.get_posts()
#Facebook.publish_post('Hello from social_network.py!')
#print Facebook.get_info_user('435131070002704')