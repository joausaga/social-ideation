import connectors.models

from django.db import models


class SocialNetwork(models.Model):
    name = models.CharField(max_length=50)
    url = models.URLField(null=True, blank=True)
    connector = models.OneToOneField(connectors.models.SocialNetworkConnector)

    def __unicode__(self):
        return self.name


class IdeationPlatform(models.Model):
    name = models.CharField(max_length=50)
    url = models.URLField(null=True, blank=True)
    connector = models.OneToOneField(connectors.models.Connector)

    def __unicode__(self):
        return self.name


class IdeationInitiatve(models.Model):
    name = models.CharField(max_length=50)
    organizer = models.CharField(max_length=50)
    LANGUAGES = (
        ('en', 'English'),
        ('es', 'Spanish'),
        ('it', 'Italian'),
    )
    language = models.CharField(max_length=3, choices=LANGUAGES)
    url = models.URLField()
    platform = models.OneToOneField(IdeationPlatform)
    users = models.IntegerField(editable=False, default=0)
    ideas = models.IntegerField(editable=False, default=0)
    votes = models.IntegerField(editable=False, default=0)
    comments = models.IntegerField(editable=False, default=0)

    def __unicode__(self):
        return self.name


class IdeationCampaign(models.Model):
    name = models.CharField(max_length=50)
    ideation_initiative = models.ForeignKey(IdeationInitiatve)


class Initiative(models.Model):
    social_network = models.ForeignKey(SocialNetwork)
    hashtag = models.CharField(unique=True, max_length=14, help_text="Max length 14 characters (do not include '#')")
    ideation_initiative = models.ForeignKey(IdeationInitiatve)

    def __unicode__(self):
        return self.name


class Campaign(models.Model):
    name = models.CharField(max_length=100)
    initiative = models.ForeignKey(Initiative)
    hashtag = models.CharField(max_length=14, help_text="Max length 14 characters (do not include '#')")

    def __unicode__(self):
        return self.name