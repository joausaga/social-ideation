# -*- coding: UTF-8 -*-
import connectors.models

from django.db import models


class SocialNetworkAppUser(models.Model):
    external_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100, null=True)
    url = models.URLField(null=True, blank=True)
    email = models.EmailField()
    snapp = models.ForeignKey('SocialNetworkApp')
    access_token = models.CharField(max_length=300)
    access_token_exp = models.DateTimeField(editable=False)
    read_permissions = models.BooleanField(default=False, editable=False)
    write_permissions = models.BooleanField(default=False, editable=False)
    registration_timestamp = models.DateTimeField(auto_now_add=True, editable=True)
    welcome_msg_sent = models.BooleanField(default=False)

    def __unicode__(self):
        if self.name:
            return self.name
        else:
            return self.external_id


class SocialNetworkAppCommunity(models.Model):
    external_id = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    token = models.CharField(max_length=300, null=True, editable=False)
    type = models.CharField(max_length=5, default='en', choices=(('page', 'Page'), ('group', 'Group'),
                                                                 ('user_account', 'User Account'),))
    url = models.URLField(default=None)
    members = models.ManyToManyField(SocialNetworkAppUser, editable=False)
    admins = models.ManyToManyField(SocialNetworkAppUser, related_name='SocialNetworkAppAdmin')

    def __unicode__(self):
        return self.name


class SocialNetworkApp(models.Model):
    name = models.CharField(max_length=50)
    url = models.URLField(null=True, blank=True)
    connector = models.ForeignKey(connectors.models.SocialNetworkConnector)
    blocked = models.DateTimeField(null=True, editable=False, default=None)
    app_id = models.CharField(max_length=50)
    app_secret = models.CharField(max_length=50, null=True, blank=True)
    redirect_uri = models.URLField(null=True, blank=True)
    community = models.ForeignKey(SocialNetworkAppCommunity, null=True, blank=True)
    app_access_token = models.CharField(max_length=300, null=True, blank=True)
    callback_real_time_updates = models.URLField(null=True, blank=True)
    object_real_time_updates = models.CharField(max_length=100, null=True, blank=True, default='page')
    field_real_time_updates = models.CharField(max_length=50, null=True, blank=True, default='feed')
    token_real_time_updates = models.CharField(max_length=100, null=True, editable=False)
    subscribed_read_time_updates = models.BooleanField(default=False, editable=False)
    last_real_time_update_sig = models.CharField(max_length=100, null=True, editable=False)
    batch_requests = models.BooleanField(default=False)
    max_batch_requests = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return self.name


class ConsultationPlatform(models.Model):
    name = models.CharField(max_length=50)
    url = models.URLField(null=True, blank=True)
    connector = models.OneToOneField(connectors.models.Connector)

    def __unicode__(self):
        return self.name


class Initiative(models.Model):
    external_id = models.IntegerField(editable=False)
    community_id = models.IntegerField(editable=True)
    name = models.CharField(max_length=50, editable=False)
    platform = models.ForeignKey(ConsultationPlatform, editable=True)
    social_network = models.ManyToManyField(SocialNetworkApp, blank=True)
    hashtag = models.CharField(unique=True, max_length=14, null=True,
                               help_text="Max length 14 characters (do not include '#')")
    url = models.URLField(editable=False)
    site_url = models.URLField(editable=True, default=None, null=True, blank=True)
    survey_url = models.URLField(editable=True, default=None, null=True, blank=True)
    users = models.IntegerField(editable=False, default=0)
    ideas = models.IntegerField(editable=False, default=0)
    votes = models.IntegerField(editable=False, default=0)
    comments = models.IntegerField(editable=False, default=0)
    active = models.BooleanField(default=False)
    language = models.CharField(max_length=5, default='en', choices=(('en', 'English'), ('es', 'Spanish'),
                                                                     ('it', 'Italian'),))
    notification_emails = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name


class Campaign(models.Model):
    external_id = models.IntegerField(editable=False)
    name = models.CharField(max_length=100)
    initiative = models.ForeignKey(Initiative)
    hashtag = models.CharField(max_length=20, null=True, help_text="Max length 20 characters "
                                                                   "(do not include '#')")
    notified = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name


class Location(models.Model):
    country = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)

    def __unicode__(self):
        return self.country + ', ' + self.city


class Author(models.Model):
    external_id = models.CharField(max_length=50)
    screen_name = models.CharField(max_length=100)
    name = models.CharField(max_length=100, null=True)
    bio = models.TextField(null=True)
    language = models.CharField(max_length=10, null=True)
    location = models.ForeignKey(Location, null=True)
    zipcode = models.CharField(max_length=10, null=True, blank=True)
    national_id = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(max_length=254, null=True, blank=True)
    friends = models.IntegerField(editable=False, default=0)
    followers = models.IntegerField(editable=False, default=0)
    groups = models.IntegerField(editable=False, default=0)
    posts_count = models.IntegerField(editable=False, default=0)
    url = models.URLField(null=True, blank=True)
    channel = models.CharField(max_length=50, choices=(('consultation_platform', 'Consultation Platform'),
                                                       ('social_network', 'Social Network'),))
    social_network = models.ForeignKey(SocialNetworkApp, null=True)
    consultation_platform = models.ForeignKey(ConsultationPlatform, null=True)
    # Property to save any other information
    payload = models.TextField(null=True, editable=False)

    def __unicode__(self):
        return self.screen_name


class BaseContent(models.Model):
    # Id Fields (after the idea is synchronized in both platforms it will have two ids)
    sn_id = models.CharField(max_length=100, null=True)
    cp_id = models.CharField(max_length=100, null=True)
    # Common Properties
    datetime = models.DateTimeField(null=True)
    author = models.ForeignKey(Author)
    # Context
    initiative = models.ForeignKey(Initiative)
    campaign = models.ForeignKey(Campaign)
    # Original Source
    source = models.CharField(max_length=50, choices=(('consultation_platform', 'Consultation Platform'),
                                                      ('social_network', 'Social Network'),))
    source_consultation = models.ForeignKey(ConsultationPlatform, null=True)
    source_social = models.ForeignKey(SocialNetworkApp, null=True)
    # Property to save any other information
    payload = models.TextField(null=True, editable=False)
    # Flags
    is_new = models.BooleanField(default=True)
    has_changed = models.BooleanField(default=False)
    exist_cp = models.BooleanField(default=False)
    exist_sn = models.BooleanField(default=False)
    sync = models.BooleanField(default=False)
    # Extra datetime field used when the author deactivates its account.
    deactivation_time = models.DateTimeField(null=True)

    class Meta:
        abstract = True


class Idea(BaseContent):
    title = models.CharField(max_length=255, null=True)
    text = models.TextField()
    url = models.URLField(null=True)
    location = models.ForeignKey(Location, null=True)
    # Social Network Metrics
    re_posts = models.IntegerField(default=0)       # e.g. Share in Facebook, RT in Twitter
    bookmarks = models.IntegerField(default=0)      # e.g. Favourite in Twitter
    # Additional Metric
    positive_votes = models.IntegerField(default=0)
    negative_votes = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)


class Comment(BaseContent):
    text = models.TextField()
    url = models.URLField(null=True)
    location = models.ForeignKey(Location, null=True)
    parent = models.CharField(max_length=10, choices=(('idea','Idea'),('comment','Comment'),))
    parent_idea = models.ForeignKey(Idea, null=True)
    parent_comment = models.ForeignKey('Comment', null=True)
    # Additional Metric
    positive_votes = models.IntegerField(default=0)
    negative_votes = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)


class Vote(BaseContent):
    value = models.IntegerField(choices=((1,'Positive'), (-1,'Negative'),), default=1)
    parent = models.CharField(max_length=10, choices=(('idea','Idea'),('comment','Comment'),))
    parent_idea = models.ForeignKey(Idea, null=True)
    parent_comment = models.ForeignKey(Comment, null=True)


class AutoComment(models.Model):
    sn_id = models.CharField(max_length=100)
    author = models.ForeignKey(SocialNetworkAppUser)
    parent_idea = models.CharField(max_length=100)
    exist = models.BooleanField(default=True)