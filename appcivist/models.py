from django.db import models
from appcivist_client import doUpdateSessionkey
from django.utils import timezone
import datetime

# Create your models here.
class Assembly (models.Model):
    appcivist_id = models.PositiveIntegerField(primary_key=True)
    appcivist_uuid = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    url = models.URLField()
    resource_space_id = models.IntegerField()
    forum_resource_space_id = models.IntegerField()
    admin_session_key = models.CharField(max_length=255)
    admin_email = models.CharField(max_length=25)
    admin_password = models.CharField(max_length=25)
    session_key_last_update = models.DateTimeField(auto_now_add=True, editable=True)
    session_key_longevity_days = models.PositiveIntegerField()
        
    def updateSessionKey(self):
        new_key = doUpdateSessionkey(self.url, self.admin_email, self.admin_password)
        if new_key:
            self.admin_session_key = new_key
            self.session_key_last_update = datetime.datetime.now()
            self.save()
        else:
            return

    def keyAboutToExpire(self):
        diff = timezone.now() - self.session_key_last_update
        if (diff.total_seconds() >= (self.session_key_longevity_days*24*60*60)):
            return True
        else:
            return False

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Assembly"
        verbose_name_plural = "Assemblies"

class Campaign(models.Model):
    appcivist_id = models.PositiveIntegerField(unique=True)
    appcivist_uuid = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    assembly = models.ForeignKey(Assembly)
    resource_space_id = models.IntegerField()
    forum_resource_space_id = models.IntegerField()

    def __unicode__(self):
        return self.name

class Author(models.Model):
    appcivist_id = models.PositiveIntegerField(unique=True)
    appcivist_uuid = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    email = models.EmailField(null=True)
    assembly = models.ForeignKey(Assembly)
    sync = models.BooleanField(default=False)
    source = models.CharField(max_length=100, null=True)

    def __unicode__(self):
        return self.name

class Idea(models.Model):
    appcivist_id = models.PositiveIntegerField(unique=True)
    appcivist_uuid = models.CharField(max_length=100)
    resource_space_id = models.IntegerField()
    forum_resource_space_id = models.IntegerField()
    title = models.CharField(max_length=100)
    text = models.TextField()
    datetime = models.DateTimeField()
    positive_votes = models.PositiveIntegerField(null=True)
    negative_votes = models.PositiveIntegerField(null=True)
    comments = models.PositiveIntegerField(null=True)
    campaign = models.ForeignKey(Campaign)
    url = models.URLField()
    user = models.ForeignKey(Author)
    sync = models.BooleanField(default=False)

    def __unicode__(self):
        return self.url

class Comment(models.Model):
    appcivist_id = models.PositiveIntegerField(unique=True)
    appcivist_uuid = models.CharField(max_length=100)
    resource_space_id = models.IntegerField()
    forum_resource_space_id = models.IntegerField()
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
    sync = models.BooleanField(default=False)

    def __unicode__(self):
        return self.url

    def parent_id(self):
        if self.parent_idea:
            return self.parent_idea.appcivist_id
        elif self.parent_comment:
            return self.parent_comment.appcivist_id

class Feedback(models.Model):
    appcivist_id = models.PositiveIntegerField(unique=True)
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
            return self.parent_idea.appcivist_id
        elif self.parent_comment:
            return self.parent_comment.appcivist_id

    def user_id(self):
        return self.author.appcivist_id
