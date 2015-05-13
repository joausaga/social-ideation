import connectors.models

from django.db import models


class SocialNetwork(models.Model):
    name = models.CharField(max_length=50)
    url = models.URLField(null=True, blank=True)
    connector = models.OneToOneField(connectors.models.SocialNetworkConnector)

    def __unicode__(self):
        return self.name


class ConsultationPlatform(models.Model):
    name = models.CharField(max_length=50)
    url = models.URLField(null=True, blank=True)
    connector = models.OneToOneField(connectors.models.Connector)

    def __unicode__(self):
        return self.name


class Initiatve(models.Model):
    name = models.CharField(max_length=50)
    platform = models.OneToOneField(ConsultationPlatform)
    social_network = models.ManyToManyField(SocialNetwork, blank=True)
    hashtag = models.CharField(unique=True, max_length=14, null=True,
                               help_text="Max length 14 characters (do not include '#')")
    url = models.URLField(editable=False, default=None)
    users = models.IntegerField(editable=False, default=0)
    ideas = models.IntegerField(editable=False, default=0)
    votes = models.IntegerField(editable=False, default=0)
    comments = models.IntegerField(editable=False, default=0)

    def __unicode__(self):
        return self.name


class Campaign(models.Model):
    name = models.CharField(max_length=100)
    initiative = models.ForeignKey(Initiatve)
    hashtag = models.CharField(unique=True, max_length=14, null=True,
                               help_text="Max length 14 characters (do not include '#')")

    def __unicode__(self):
        return self.name

