from rest_framework import serializers
from .models import Initiative, Author, Campaign, Location, Idea, Comment, Vote


class InitiativeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Initiative
        exclude = ('token',)


class CampaignSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ideascale_id', read_only=True)

    class Meta:
        model = Campaign
        fields = ('id', 'name')


class AuthorSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ideascale_id', read_only=True)

    class Meta:
        model = Author
        exclude = ('ideascale_id', 'initiative')


class LocationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Location
        exclude = ('id', )


class IdeaSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ideascale_id', read_only=True)
    user_info = AuthorSerializer(source='user', read_only=True)
    location_info = LocationSerializer(source='location', read_only=True)
    campaign_info = CampaignSerializer(source='campaign', read_only=True)

    class Meta:
        model = Idea
        exclude = ('ideascale_id', 'sync', 'user', 'location', 'campaign')


class CommentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ideascale_id', read_only=True)
    user_info = AuthorSerializer(source='user', read_only=True)
    location_info = LocationSerializer(source='location', read_only=True)
    parent_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Comment
        exclude = ('ideascale_id', 'user', 'location', 'parent_idea', 'parent_comment', 'sync')


class VoteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ideascale_id', read_only=True)
    author_id = serializers.IntegerField(read_only=True)
    parent_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Vote
        exclude = ('ideascale_id', 'sync', 'author', 'parent_idea', 'parent_comment')