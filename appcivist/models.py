from django.db import models

# Create your models here.
class Assembly (models.Model):
    # TODO en el ideascale app, el initiative tiene solo id, no ideascale id, tendria que hacer que el appcivist_id sea el PK de la clase
    # appcivist_id = models.PositiveIntegerField(primary_key=True)
    appcivist_id = models.PositiveIntegerField(unique=True)
    appcivist_uuid = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    url = models.URLField()
    #assembly_id = models.IntegerField()
    resource_space_id = models.IntegerField()
    forum_resource_space_id = models.IntegerField()
    admin_session_key = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

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
    assembly = models.ForeignKey(Assembly) #VER SI ES QUE NO QUITAMOS ESTO
    sync = models.BooleanField(default=False)
    source = models.CharField(max_length=100, null=True) #VER SI NO QUITAMOS ESTO

    def __unicode__(self):
        return self.name

class Proposal(models.Model):
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
    #location = models.ForeignKey(Location, null=True)
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
    parent_proposal = models.ForeignKey(Proposal, null=True)
    parent_comment = models.ForeignKey('Comment', null=True)
    url = models.URLField()
    user = models.ForeignKey(Author)
    #location = models.ForeignKey(Location, null=True)
    sync = models.BooleanField(default=False)

    def __unicode__(self):
        return self.url

    def parent_id(self):
        if self.parent_proposal:
            return self.parent_proposal.appcivist_id
        elif self.parent_comment:
            return self.parent_comment.appcivist_id

class Feedback(models.Model):
    appcivist_id = models.PositiveIntegerField(unique=True)
    # appcivist_uuid = models.CharField(max_length=100)
    value = models.IntegerField()
    datetime = models.DateTimeField()
    parent_type = models.CharField(max_length=50)
    parent_proposal = models.ForeignKey(Proposal, null=True)
    parent_comment = models.ForeignKey(Comment, null=True)
    author = models.ForeignKey(Author)
    sync = models.BooleanField(default=False)

    def __unicode__(self):
        if self.parent_proposal:
            return 'Vote {} on proposal {}'.format(self.value, self.parent_proposal.title)
        elif self.parent_comment:
            return 'Vote {} on comment {}'.format(self.value, self.parent_comment.text)

    def parent_id(self):
        if self.parent_proposal:
            return self.parent_proposal.appcivist_id
        elif self.parent_comment:
            return self.parent_comment.appcivist_id

    def user_id(self):
        return self.author.appcivist_id