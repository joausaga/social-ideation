from django.test import TestCase

from app.models import Idea, Author, Location, ConsultationPlatform, Initiative, SocialNetwork
from app.tasks import pull_data, push_data, delete_data
from utils import build_request_url, do_request, get_url_cb, get_json_or_error, build_request_body


class AppTestCase(TestCase):
    fixtures = ['initial_data.json']
    cp_connector = None
    testing_initiative = Initiative.objects.get(url='http://fiveheads.ideascale.com')
    sn_api = None
    consultation_platform = None
    consultation_platform_url = 'http://www.ideascale.com'
    social_network = None
    social_network_url = 'http://www.facebook.com'
    num_initial_ideas_fb = 0
    num_initial_comments_fb = 0
    num_initial_ideas_ideascale = 0
    num_initial_comments_ideascale = 0

    def setUp(self):
        self.consultation_platform = ConsultationPlatform.objects.get(url=self.consultation_platform_url)
        self.cp_connector = self.consultation_platform.connector
        self.social_network = SocialNetwork.objects.get(url=self.social_network_url)
        fb_connector = self.social_network.connector
        sn_class = fb_connector.connector_class.title()
        sn_module = fb_connector.connector_module.lower()
        self.sn_api = getattr(__import__(sn_module, fromlist=[sn_class]), sn_class)
        self.sn_api.authenticate()
        self._clean_up_facebook_page()
        self._clean_up_ideascale_community()
        self._set_ideascale_counters()
        self._set_facebook_counters()

    def _exist_platform_name_in_text(self, platform_name, text):
        return platform_name.lower() in text.lower()

    def _clean_up_facebook_page(self):
        posts = self.sn_api.get_posts()
        for post in posts:
            if 'comments_array' in post.keys():
                for comment in post['comments_array']:
                    if 'comments_array' in comment.keys():
                        for reply in comment['comments_array']:
                            if self._exist_platform_name_in_text(self.consultation_platform.name, reply['text']):
                                self.sn_api.delete_comment(reply['id'])
                    if self._exist_platform_name_in_text(self.consultation_platform.name, comment['text']):
                        self.sn_api.delete_comment(comment['id'])
            if self._exist_platform_name_in_text(self.consultation_platform.name, post['text']):
                self.sn_api.delete_post(post['id'])

    def _clean_up_ideascale_community(self):
        connector = self.cp_connector
        url_cb = get_url_cb(connector, 'get_comments_cb')
        url = build_request_url(url_cb.url, url_cb.callback, {'initiative_id': self.testing_initiative.external_id})
        resp = do_request(connector, url, url_cb.callback.method)
        comments = get_json_or_error(connector.name, url_cb.callback, resp)
        delayed_comments = []
        # First delete replies to comments
        for comment in comments:
            if self._exist_platform_name_in_text(self.social_network.name, comment['text']):
                if comment['parent_type'] == 'idea':
                    delayed_comments.append(comment)
                else:
                    url_cb = get_url_cb(connector, 'delete_comment_cb')
                    url = build_request_url(url_cb.url, url_cb.callback, {'comment_id': comment['id']})
                    do_request(connector, url, url_cb.callback.method)
        # Second delete comments to ideas
        for delayed_comment in delayed_comments:
            url_cb = get_url_cb(connector, 'delete_comment_cb')
            url = build_request_url(url_cb.url, url_cb.callback, {'comment_id': delayed_comment['id']})
            do_request(connector, url, url_cb.callback.method)
        # Finally delete ideas
        url_cb = get_url_cb(connector, 'get_ideas_cb')
        url = build_request_url(url_cb.url, url_cb.callback, {'initiative_id': self.testing_initiative.external_id})
        resp = do_request(connector, url, url_cb.callback.method)
        ideas = get_json_or_error(connector.name, url_cb.callback, resp)
        for idea in ideas:
            if self._exist_platform_name_in_text(self.social_network.name, idea['text']):
                url_cb = get_url_cb(connector, 'delete_idea_cb')
                url = build_request_url(url_cb.url, url_cb.callback, {'idea_id': idea['id']})
                do_request(connector, url, url_cb.callback.method)

    def _clean_up_db(self):
        Idea.objects.all().delete()
        Author.objects.all().delete()
        Location.objects.all().delete()

    def _set_ideascale_counters(self):
        connector = self.cp_connector
        url_cb = get_url_cb(connector, 'get_ideas_cb')
        url = build_request_url(url_cb.url, url_cb.callback, {'initiative_id': self.testing_initiative.external_id})
        resp = do_request(connector, url, url_cb.callback.method)
        ideas = get_json_or_error(connector.name, url_cb.callback, resp)
        self.num_initial_ideas_ideascale = len(ideas)
        url_cb = get_url_cb(connector, 'get_comments_cb')
        url = build_request_url(url_cb.url, url_cb.callback, {'initiative_id': self.testing_initiative.external_id})
        resp = do_request(connector, url, url_cb.callback.method)
        comments = get_json_or_error(connector.name, url_cb.callback, resp)
        self.num_initial_comments_ideascale = len(comments)

    def _set_facebook_counters(self):
        posts = self.sn_api.get_posts()
        self.num_initial_ideas_fb = len(posts)
        for post in posts:
            if 'comments_array' in post.keys():
                self.num_initial_comments_fb += len(post['comments_array'])
                for comment in post['comments_array']:
                    if 'comments_array' in comment.keys():
                        self.num_initial_comments_fb += len(comment['comments_array'])


class TestAppBehavior(AppTestCase):

    def _initial(self):
        pull_data()
        push_data()
        connector = self.cp_connector
        url_cb = get_url_cb(connector, 'get_ideas_cb')
        url = build_request_url(url_cb.url, url_cb.callback, {'initiative_id': self.testing_initiative.external_id})
        resp = do_request(connector, url, url_cb.callback.method)
        ideas = get_json_or_error(connector.name, url_cb.callback, resp)
        replicated_ideas = 0
        for idea in ideas:
            if self._exist_platform_name_in_text(self.social_network.name, idea['text']):
                replicated_ideas += 1
        self.assertEqual(replicated_ideas, self.num_initial_ideas_fb)
        url_cb = get_url_cb(connector, 'get_comments_cb')
        url = build_request_url(url_cb.url, url_cb.callback, {'initiative_id': self.testing_initiative.external_id})
        resp = do_request(connector, url, url_cb.callback.method)
        comments = get_json_or_error(connector.name, url_cb.callback, resp)
        replicated_comments = 0
        for comment in comments:
            if self._exist_platform_name_in_text(self.social_network.name, comment['text']):
                replicated_comments += 1
        self.assertEqual(replicated_comments, self.num_initial_comments_fb)
        posts = self.sn_api.get_posts()
        replicated_ideas = 0
        replicated_comments = 0
        for post in posts:
            if self._exist_platform_name_in_text(self.consultation_platform.name, post['text']):
                replicated_ideas += 1
            if 'comments_array' in post.keys():
                for comment in post['comments_array']:
                    if self._exist_platform_name_in_text(self.consultation_platform.name, comment['text']):
                        replicated_comments += 1
                    if 'comments_array' in comment.keys():
                        for reply in comment['comments_array']:
                            if self._exist_platform_name_in_text(self.consultation_platform.name, reply['text']):
                                replicated_comments += 1
        self.assertEqual(replicated_ideas, self.num_initial_ideas_ideascale)
        self.assertEqual(replicated_comments, self.num_initial_comments_ideascale)

    def _modifications(self):
        # 1. Add new comment to a facebook idea
        idea = Idea.objects.get(text='Terere Machine')
        idea_mod_1 = idea
        url_cb = get_url_cb(self.cp_connector, 'create_comment_idea_cb')
        url = build_request_url(url_cb.url, url_cb.callback, {'idea_id': idea.cp_id})
        params = {'text': 'Testing comment!'}
        body_param = build_request_body(self.cp_connector, url_cb.callback, params)
        resp = do_request(self.cp_connector, url, url_cb.callback.method, body_param)
        new_comment_is = get_json_or_error(self.cp_connector.name, url_cb.callback, resp)

        # 2. Add new comment to an ideascale idea
        idea = Idea.objects.get(cp_id='721262')
        idea_mod_2 = idea
        url_cb = get_url_cb(self.cp_connector, 'create_comment_idea_cb')
        url = build_request_url(url_cb.url, url_cb.callback, {'idea_id': idea.cp_id})
        params = {'text': 'Testing comment 2!'}
        body_param = build_request_body(self.cp_connector, url_cb.callback, params)
        do_request(self.cp_connector, url, url_cb.callback.method, body_param)

        # 3. Vote on an idea
        idea = Idea.objects.get(cp_id='718882')
        idea_mod_3 = idea
        if idea.positive_votes > 0:
            idea_vote_value = -1
        else:
            idea_vote_value = 1
        url_cb = get_url_cb(self.cp_connector, 'vote_idea_cb')
        url = build_request_url(url_cb.url, url_cb.callback, {'idea_id': idea.cp_id})
        params = {'value': idea_vote_value}
        body_param = build_request_body(self.cp_connector, url_cb.callback, params)
        do_request(self.cp_connector, url, url_cb.callback.method, body_param)

        # 4. Add new comment to a facebook idea
        idea = Idea.objects.get(sn_id='437938162969648_817265021703625')
        idea_mod_4 = idea
        new_comment_fb = self.sn_api.comment_post(idea.sn_id, 'Testing comment 3!')

        # 5. Add new comment to an ideascale idea
        idea = Idea.objects.get(title='Testing param')
        idea_mod_5 = idea
        self.sn_api.comment_post(idea.sn_id, 'Testing comment 4!')

        # 6. Create new idea on facebook
        new_idea_fb = self.sn_api.publish_post('Testing Idea!')

        # 7. Create new idea on ideascale
        url_cb = get_url_cb(self.cp_connector, 'create_idea_cb')
        url = build_request_url(url_cb.url, url_cb.callback, {'initiative_id': self.testing_initiative.external_id})
        params = {'title': 'Testing Idea to be deleted', 'text': 'Testing Idea to be deleted',
                  'campaign_id': self.testing_initiative.campaign_set.all()[0].external_id}
        body_param = build_request_body(self.cp_connector, url_cb.callback, params)
        resp = do_request(self.cp_connector, url, url_cb.callback.method, body_param)
        new_idea_is = get_json_or_error(self.cp_connector.name, url_cb.callback, resp)

        # Sync modifications
        pull_data()
        push_data()

        # Check if modification 1) was replicated on facebook
        idea = Idea.objects.get(text='Terere Machine')
        post = self.sn_api.get_post(idea.sn_id)
        self.assertEqual(len(post['comments_array']), idea_mod_1.comments+1)

        # Check if modification 2) was replicated on facebook
        idea = Idea.objects.get(cp_id='721262')
        post = self.sn_api.get_post(idea.sn_id)
        self.assertEqual(len(post['comments_array']), idea_mod_2.comments+1)

        # Check if modification 3) was replicated on facebook
        idea = Idea.objects.get(cp_id='718882')
        post = self.sn_api.get_post(idea.sn_id)
        if idea_vote_value == 1:
            self.assertEqual(post['positive_votes'], idea_mod_3.positive_votes+1)
        else:
            self.assertEqual(post['positive_votes'], idea_mod_3.positive_votes-1)

        # Check if modification 4) was replicated on ideascale
        idea = Idea.objects.get(sn_id='437938162969648_817265021703625')
        url_cb = get_url_cb(self.cp_connector, 'get_idea_cb')
        url = build_request_url(url_cb.url, url_cb.callback, {'idea_id': idea.cp_id})
        resp = do_request(self.cp_connector, url, url_cb.callback.method)
        idea_is = get_json_or_error(self.cp_connector.name, url_cb.callback, resp)
        self.assertEqual(idea_is['comments'], idea_mod_4.comments+1)

        # Check if modification 5) was replicated on ideascale
        idea = Idea.objects.get(title='Testing param')
        url = build_request_url(url_cb.url, url_cb.callback, {'idea_id': idea.cp_id})
        resp = do_request(self.cp_connector, url, url_cb.callback.method)
        idea_is = get_json_or_error(self.cp_connector.name, url_cb.callback, resp)
        self.assertEqual(idea_is['comments'], idea_mod_5.comments+1)

        return {'id_fb_new_idea': new_idea_fb['id'], 'id_fb_idea': idea_mod_4.sn_id,
                'id_fb_comment': new_comment_fb['id'], 'id_is_new_idea': new_idea_is['id'],
                'id_is_idea': idea_mod_4.cp_id, 'id_is_comment': new_comment_is['id']}

    def _deletes(self, content_to_del):
        # 1. Delete idea created on ideascale
        url_cb = get_url_cb(self.cp_connector, 'delete_idea_cb')
        url = build_request_url(url_cb.url, url_cb.callback, {'idea_id': content_to_del['id_is_new_idea']})
        do_request(self.cp_connector, url, url_cb.callback.method)
        # 2. Delete idea created on facebook
        self.sn_api.delete_post(content_to_del['id_fb_new_idea'])
        # 3. Delete comment created on ideascale
        url_cb = get_url_cb(self.cp_connector, 'delete_comment_cb')
        url = build_request_url(url_cb.url, url_cb.callback, {'comment_id': content_to_del['id_is_comment']})
        do_request(self.cp_connector, url, url_cb.callback.method)
        # 4. Delete comment created on facebook
        self.sn_api.delete_comment(content_to_del['id_fb_comment'])
        # Sync modifications
        pull_data()
        delete_data()
        # Check if the deletion of the idea created on ideascale was replicated (1)
        url_cb = get_url_cb(self.cp_connector, 'get_idea_cb')
        url = build_request_url(url_cb.url, url_cb.callback, {'idea_id':content_to_del['id_is_new_idea']})
        resp = do_request(self.cp_connector, url, url_cb.callback.method)
        self.assertEqual(resp.status_code, 400)
        # Check if the deletion of the idea created on facebook was replicated (2)
        del_post = self.sn_api.get_post(content_to_del['id_fb_new_idea'])
        self.assertIsNone(del_post)
        # Check if the deletion of the comment created on ideascale was replicated (3)
        url_cb = get_url_cb(self.cp_connector, 'get_comment_cb')
        url = build_request_url(url_cb.url, url_cb.callback, {'comment_id':content_to_del['id_is_comment']})
        resp = do_request(self.cp_connector, url, url_cb.callback.method)
        self.assertEqual(resp.status_code, 400)
        # Check if the deletion of the comment created on facebook was replicated (4)
        del_comment = self.sn_api.get_post(content_to_del['id_fb_comment'])
        self.assertIsNone(del_comment)

    def test_synchronization(self):
        self._initial()
        id_comments_created = self._modifications()
        self._deletes(id_comments_created)