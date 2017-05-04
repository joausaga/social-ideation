from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from rest_framework.authtoken.models import Token


class Initiative(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    token = models.CharField(max_length=255)
    community = models.IntegerField()

    def __unicode__(self):
        return self.name


class Campaign(models.Model):
    ideascale_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=100)
    initiative = models.ForeignKey(Initiative)

    def __unicode__(self):
        return self.name


class Author(models.Model):
    ideascale_id = models.PositiveIntegerField()
    name = models.CharField(max_length=100)
    email = models.EmailField(null=True)
    initiative = models.ForeignKey(Initiative)
    sync = models.BooleanField(default=False)
    source = models.CharField(max_length=100, null=True)

    def __unicode__(self):
        return self.name


class Location(models.Model):
    country = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    code = models.CharField(max_length=100, unique=True, null=True)

    def __unicode__(self):
        return self.country + ', ' + self.city


class Idea(models.Model):
    ideascale_id = models.PositiveIntegerField(unique=True)
    title = models.CharField(max_length=100)
    text = models.TextField()
    datetime = models.DateTimeField()
    positive_votes = models.PositiveIntegerField(null=True)
    negative_votes = models.PositiveIntegerField(null=True)
    comments = models.PositiveIntegerField(null=True)
    campaign = models.ForeignKey(Campaign)
    url = models.URLField()
    user = models.ForeignKey(Author)
    location = models.ForeignKey(Location, null=True)
    sync = models.BooleanField(default=False)

    def __unicode__(self):
        return self.url


class Comment(models.Model):
    ideascale_id = models.PositiveIntegerField(unique=True)
    text = models.TextField()
    datetime = models.DateTimeField()
    positive_votes = models.PositiveIntegerField()
    negative_votes = models.PositiveIntegerField(null=True)
    comments = models.PositiveIntegerField(null=True)
    parent_type = models.CharField(max_length=50)
    parent_idea = models.ForeignKey(Idea, null=True)
    parent_comment = models.ForeignKey('Comment', null=True)
    url = models.URLField()
    user = models.ForeignKey(Author)
    location = models.ForeignKey(Location, null=True)
    sync = models.BooleanField(default=False)

    def __unicode__(self):
        return self.url

    def parent_id(self):
        if self.parent_idea:
            return self.parent_idea.ideascale_id
        elif self.parent_comment:
            return self.parent_comment.ideascale_id


class Vote(models.Model):
    ideascale_id = models.PositiveIntegerField(unique=True)
    value = models.IntegerField()
    datetime = models.DateTimeField()
    parent_type = models.CharField(max_length=50)
    parent_idea = models.ForeignKey(Idea, null=True)
    parent_comment = models.ForeignKey(Comment, null=True)
    author = models.ForeignKey(Author)
    sync = models.BooleanField(default=False)

    def __unicode__(self):
        if self.parent_idea:
            return 'Vote {} on idea {}'.format(self.value, self.parent_idea.title)
        elif self.parent_comment:
            return 'Vote {} on comment {}'.format(self.value, self.parent_comment.text)

    def parent_id(self):
        if self.parent_idea:
            return self.parent_idea.ideascale_id
        elif self.parent_comment:
            return self.parent_comment.ideascale_id

    def user_id(self):
        return self.author.ideascale_id


class Client(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    last_idea = models.ForeignKey(Idea, null=True, related_name='+')
    last_comment_idea = models.ForeignKey(Comment, null=True, related_name='+')
    last_vote_idea = models.ForeignKey(Vote, null=True, related_name='+')
    last_comment = models.ForeignKey(Comment, null=True, related_name='+')
    last_vote_comment = models.ForeignKey(Vote, null=True, related_name='+')
    last_vote = models.ForeignKey(Vote, null=True, related_name='+')

    def __unicode__(self):
        return self.user.username

class TestingParameter(models.Model):
    key = models.CharField(max_length=50)
    raw_value = models.CharField(max_length=100)
    TYPES = (
        ('int', 'Integer'),
        ('str', 'String'),
        ('bool', 'Boolean'),
    )
    type = models.CharField(choices=TYPES, max_length=10)

    def value(self):
        if self.type == 'str':
            return self.raw_value
        elif self.type == 'int':
            return int(self.raw_value)
        else:
            return bool(self.raw_value)

    def tuple(self):
        return {self.key: self.value()}

    @classmethod
    def get_params(cls):
        params = {}
        for param in TestingParameter.objects.all():
            params.update(param.tuple())
        return params


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_client(sender, instance=None, created=False, **kwargs):
    if created:
        Client.objects.create(user=instance)
