from rest_framework import serializers
from appcivist.models import Assembly, Author, Campaign, Idea, Comment, Feedback

class AssemblySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='appcivist_id', read_only=True)
    community = serializers.IntegerField(source='appcivist_id', read_only=True)
    class Meta:
        model = Assembly
        exclude = ('appcivist_id', 'appcivist_uuid', 'resource_space_id', 'forum_resource_space_id', 'admin_session_key')


class CampaignSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='appcivist_id', read_only=True)

    class Meta:
        model = Campaign
        exclude = ('appcivist_uuid', 'resource_space_id', 'forum_resource_space_id', 'assembly')


class AuthorSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='appcivist_id', read_only=True)

    class Meta:
        model = Author
        exclude = ('appcivist_id', 'appcivist_uuid', 'sync', 'assembly', 'source')


class IdeaSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='appcivist_id', read_only=True)
    user_info = AuthorSerializer(source='user', read_only=True)
    #location_info = LocationSerializer(source='location', read_only=True)
    campaign_info = CampaignSerializer(source='campaign', read_only=True)

    class Meta:
        model = Idea
        exclude = ('appcivist_id', 'sync', 'user', 'campaign', 'appcivist_uuid', 'resource_space_id', 'forum_resource_space_id')


class CommentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='appcivist_id', read_only=True)
    user_info = AuthorSerializer(source='user', read_only=True)
    #location_info = LocationSerializer(source='location', read_only=True)
    parent_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Comment
        exclude = ('appcivist_id', 'user', 'parent_idea', 'parent_comment', 'sync', 'resource_space_id', 'forum_resource_space_id')


class FeedbackSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='appcivist_id', read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    parent_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Feedback
        exclude = ('appcivist_id', 'sync', 'author', 'parent_idea', 'parent_comment')