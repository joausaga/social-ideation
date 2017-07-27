import requests
import json

#example function
def doUpdateSessionkey(url, email, password):
    params =  {"email": email, "password": password}
    headers = {"content-type": "application/json; charset=utf8"}
    r = requests.post(url, headers=headers, json=params)
    if r.status_code == 200:
        response = r.json()
        return response["sessionKey"]
    else:
        return None

def doRequest(url, method="get", body=None, params=None, headers=None):
    if method == "get":
        if params == None:
            r = requests.get(url, headers=headers)
        else:
            r = requests.get(url, headers=headers, params=params)

    elif method == "post":
        r = requests.post(url, headers=headers, json=body)

    elif method == "put":
        if body == None:
            r = requests.put(url, headers=headers)
        else:
            r = requests.put(url, headers=headers, json=body)

    if r.status_code == 200:
        return r.json()
    else:
        r.raise_for_status()


class appcivist_api():
    base_url = ""
    session_key = ""

    ignore_admin_user =""
    social_ideation_source=""
    social_ideation_source_url=""
    social_ideation_user_source_url=""
    social_ideation_user_source_id=""

    def set_headers(self):
        headers = {"SESSION_KEY": self.session_key, "IGNORE_ADMIN_USER": self.ignore_admin_user, "SOCIAL_IDEATION_SOURCE": self.social_ideation_source, "SOCIAL_IDEATION_SOURCE_URL": self.social_ideation_source_url, "SOCIAL_IDEATION_USER_SOURC_ID": self.social_ideation_user_source_id, "SOCIAL_IDEATION_USER_SOURCE_URL": self.social_ideation_user_source_url}
        return headers


    # return list of all memebers of the assembly
    # GET /api/assembly/:id/membership/:status
    # implemented by using the get_all_authors method
    # TESTED
    def get_users(self, aid):
        return self.get_all_authors(aid)


    # return info about a single member
    # GET /api/user/:uid 
    # GET /api/user/:uid/profile
    # implemented by using the get_author_detail method
    # TESTED
    def get_user_details(self, uid):
        return self.get_author_info(uid)

    # tengo que diferenciar entre author y user despues
    # GET /api/assembly/:id/membership/:status
    # una vez que tenga los ids de los miembros debo llamar a get_author_detail
    # for each item in response, append item['user']
    # TESTED
    def get_all_authors(self, aid):
        list_of_users = []
        url = self.base_url + "/api/assembly/" + str(aid) + "/membership/ACCEPTED"
        headers = {"SESSION_KEY": self.session_key}
        # headers = {"SESSION_KEY": self.session_key, "IGNORE_ADMIN_USER": self.ignore_admin_user, "SOCIAL_IDEATION_SOURCE": self.social_ideation_source, "SOCIAL_IDEATION_SOURCE_URL": self.social_ideation_source_url, "SOCIAL_IDEATION_USER_SOURC_ID": self.social_ideation_user_source_id, "SOCIAL_IDEATION_USER_SOURCE_URL": self.social_ideation_user_source_url}
        response = doRequest(url=url, method="get", headers=headers)
        for membership in response:
            list_of_users.append(membership["user"])
        return list_of_users
        # return response

    # tengo que diferenciar entre author y user despues
    # GET /api/user/:uid (Get a user by id) (to check if user info is updated)
    # GET /api/user/:uid/profile   
    # TESTED 
    def get_author_info(self, uid):
        url = self.base_url + "/api/user/" + str(uid)
        headers = {"SESSION_KEY": self.session_key}
        response = doRequest(url=url, method="get", headers=headers)
        return response

    # return the list of capaigns of an assembly
    # GET /api/assembly/:aid/campaign (List campaigns of an Assembly)
    # TESTED
    def get_campaigns(self, aid):
        url = self.base_url + "/api/assembly/" + str(aid) + "/campaign"
        headers = {"SESSION_KEY": self.session_key}
        response = doRequest(url=url, method="get", headers=headers)
        return response

    # return all the proposals
    # GET /api/assembly/:aid/campaign (List campaigns of an Assembly)
    # GET /api/assembly/:aid/campaign/:cid/contribution (Get contributions in a Campaign)
    # TESTED
    def get_proposals_of_campaign(self, aid, cid):
        # url = self.base_url + "/api/assembly/" + str(aid) + "/contribution"
        url = self.base_url + "/api/assembly/" + str(aid) + "/campaign/" + str(cid) + "/contribution"
        headers = {"SESSION_KEY": self.session_key}
        params = {"type": "proposal"}
        response = doRequest(url=url, method="get", headers=headers, params=params)
        final_list = []
        for proposal in response:
            print proposal.keys()
            if "firstAuthor" in proposal.keys():
                final_list.append(proposal)
        return final_list

    # return info about a single proposal
    # GET /api/assembly/:aid/contribution/:cid
    # TESTED
    def get_proposal_details(self, aid, coid):
        url = self.base_url + "/api/assembly/" + str(aid) + "/contribution/" + str(coid)
        headers = {"SESSION_KEY": self.session_key}
        response = doRequest(url=url, method="get", headers=headers)
        return response

    def get_all_proposals(self, aid):
        list_of_proposals = []
        campaigns = self.get_campaigns(aid)
        for c in campaigns:
            proposals = self.get_proposals_of_campaign(aid, c["campaignId"])
            for p in proposals:
                list_of_proposals.append(p)
        return list_of_proposals        


    # return the list of comments of a proposal
    # GET /api/assembly/:aid/contribution/:cid/comment (no me sirve este. No retorna bien)
    # GET /api/space/:sid/contribution (1st, get the discussion, then, foreach discussion get comments)
    # TESTED
    def get_comments_of_proposal(self, sid):
        list_of_comments = []
        url = self.base_url + "/api/space/" + str(sid) + "/contribution?type=DISCUSSION"
        headers = {"SESSION_KEY": self.session_key}
        response = doRequest(url=url, method="get", headers=headers)
        for item in response["list"]:
            # print item["text"]
            list_of_comments.append(item)
            url = self.base_url + "/api/space/" + str(item["resourceSpaceId"]) + "/contribution?type=COMMENT"
            response2 = doRequest(url=url, method="get", headers=headers)
            for item2 in response2["list"]:
                # print "       > " + item2["text"]
                list_of_comments.append(item2)
        return list_of_comments
        # return response

    # return the list of all comments
    # GET /api/assembly/:aid/contribution  (DIDN'T WORK)
    # implemented by using the get_proposals and get_comment_proposal methods
    # TESTED
    def get_comments_of_campaign(self, aid, cid):
        list_of_comments = []
        proposals = self.get_proposals_of_campaign(aid, cid)
        for p in proposals:
            # print(p.keys())
            p_comments = self.get_comments_of_proposal(p["resourceSpaceId"])
            list_of_comments = list_of_comments + p_comments
        return list_of_comments

    def get_all_comments(self, aid):
        list_of_comments = []
        campaigns = self.get_campaigns(aid)
        for c in campaigns:
            comments = self.get_comments_of_campaign(aid, c["campaignId"])
            for co in comments:
                list_of_comments.append(co)
        return list_of_comments

    # return info about a single comment
    # GET /api/assembly/:aid/contribution/:cid
    # TESTED
    def get_comment_details(self, aid, coid):
        url = self.base_url + "/api/assembly/" + str(aid) + "/contribution/" + str(coid)
        headers = {"SESSION_KEY": self.session_key}
        response = doRequest(url=url, method="get", headers=headers)
        return response

    # return the votes (called feedbacks on appcivist) of a single contribution
    # GET /api/assembly/:aid/contribution/:coid/feedback   
    # GET /api/assembly/:aid/campaign/:cid/contribution/:coid/feedback (It works with both endpoints)
    # def get_feedback_proposal(self, aid, cid, coid):
    #     url = self.base_url + "/api/assembly/" + str(aid) + "/campaign/" + str(cid) + "/contribution/" + str(coid) + "/feedback"
    def get_feedbacks_of_contribution(self, aid, coid):
        url =  self.base_url + "/api/assembly/" + str(aid) + "/contribution/" + str(coid) + "/feedback"
        headers = {"SESSION_KEY": self.session_key}
        response = doRequest(url=url, method="get", headers=headers)
        return response
  
    # return the votes (called feedbacks on appcivist) of a single proposal
    def get_feedbacks_of_proposal(self, aid, coid):
        return self.get_feedbacks_of_contribution(aid, coid)

    # return the votes (called feedbacks on appcivist) of a single comment
    # implemented by using the get_feedback_proposal method since the endpoint is for appcivist's contributions in general (proposals and comments)
    # TESTED
    def get_feedbacks_of_comment(self, aid, coid):
        return self.get_feedbacks_of_contribution(aid, coid)
    
    # return all the votes of all proposals of all campaigns
    # implemen
    # TESTED
    def get_feedbacks_of_all_proposals(self, aid):
        list_of_feedbacks = []
        campaigns = self.get_campaigns(aid)
        for c in campaigns:
            proposals = self.get_proposals_of_campaign(aid, c["campaignId"])
            for p in proposals:
                feedbacks = self.get_feedbacks_of_proposal(aid, p["contributionId"])
                list_of_feedbacks = list_of_feedbacks + feedbacks
        return list_of_feedbacks
        # pass

    # return all the votes of all comments of all campaigns
    # se podria llamar a get_feedback_contribution para todos los comentarios
    # TESTED
    def get_feedbacks_of_all_comments(self, aid):
        list_of_feedbacks = []
        campaigns = self.get_campaigns(aid)
        for c in campaigns:
            comments = self.get_comments_of_campaign(aid, c["campaignId"])
            for c in comments:
                feedbacks = self.get_feedbacks_of_comment(aid, c["contributionId"])
                list_of_feedbacks = list_of_feedbacks + feedbacks
        return list_of_feedbacks
        # pass



    ###### POST METHODS
    # creates a new contribution
    # ex new_proposal = {"status": "NEW", "title" : "prueba marce 2 con campaigns", "text" : "this is a test without location", "type": "PROPOSAL", "campaigns": [1]}
    def create_proposal(self, sid, proposal):
        url = self.base_url + "/api/space/" + str(sid) + "/contribution"
        # headers = {"SESSION_KEY": self.session_key}
        headers = self.set_headers()
        response = doRequest(url=url, method="post", headers=headers, body=proposal)
        return response

    # creates a new user
    # I am not sure if this endpoint is implemented in appcivist platform
    def create_new_author(self):
        pass

    # creates a comment (appcivist's DICUSSION) on an proposal
    def comment_proposal(self, sid, discussion):
        return self.create_proposal(sid, discussion)

    # creates a comment on a Discussion
    def comment_discussion(self, sid, comment):
        return self.create_proposal(sid, comment)

    ###### PUT METHODS
    
    # PUT /api/assembly/:aid/campaign/:caid/contribution/:cid/feedback
    def vote_up_proposal(self, aid, caid, coid):
        url = self.base_url + "/api/assembly/" + str(aid) + "/campaign/" + str(caid) + "/contribution/" + str(coid) + "/feedback"
        # headers = {"SESSION_KEY": self.session_key}
        headers = self.set_headers()
        test_body = {"up": "true", "down": "false", "fav": "false", "flag": "false", "type": "MEMBER", "status": "PUBLIC"}
        response = doRequest(url=url, method="put", headers=headers, body=test_body)
        return response

    # PUT /api/assembly/:aid/campaign/:caid/contribution/:cid/feedback
    def vote_down_proposal(self, aid, caid, coid):
        url = self.base_url + "/api/assembly/" + str(aid) + "/campaign/" + str(caid) + "/contribution/" + str(coid) + "/feedback"
        # headers = {"SESSION_KEY": self.session_key}
        headers = self.set_headers()
        test_body = {"up": "false", "down": "true", "fav": "false", "flag": "false", "type": "MEMBER", "status": "PUBLIC"}
        response = doRequest(url=url, method="put", headers=headers, body=test_body)
        return response

    def vote_up_comment(self, aid, caid, coid):
        return self.vote_up_proposal(aid, caid, coid)

    def vote_down_comment(self, aid, caid, coid):
        return self.vote_down_proposal(aid, caid, coid)

    ##### DELETE METHODS

    # Deletes a contribution
    # PUT       /api/assembly/:aid/contribution/:cid/softremoval
    # DELETE    /api/assembly/:aid/contribution/:cid
    def delete_contribution(self, aid, coid):
        url = self.base_url + "/api/assembly/" + str(aid) + "/contribution/" + str(coid) + "/softremoval"
        # headers = headers = {"SESSION_KEY": self.session_key}
        headers = self.set_headers()
        response = doRequest(url=url, method="put", headers=headers)
        return response

    def delete_proposal(self, aid, coid):
        return delete_contribution(aid, coid)

    def delete_comment(self, aid, coid):
        return delete_contribution(aid, coid)