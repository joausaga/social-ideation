from rest_framework import serializers
from appcivist.models import Assembly, Author, Campaign, Proposal, Comment, Feedback

class AssemblySerializer(serializers.ModelSerializer):
    class Meta:
        model = Assembly

class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author

class ProposalSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='appcivist_id', read_only=True)
    user_info = AuthorSerializer(source='user', read_only=True)
    #location_info = LocationSerializer(source='location', read_only=True)
    campaign_info = CampaignSerializer(source='campaign', read_only=True)

    class Meta:
        model = Idea
        exclude = ('appcivist_id', 'sync', 'user', 'campaign')

class CommentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='appcivist_id', read_only=True)
    user_info = AuthorSerializer(source='user', read_only=True)
    #location_info = LocationSerializer(source='location', read_only=True)
    parent_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Comment
        exclude = ('appcivist_id', 'user', 'parent_proposal', 'parent_comment', 'sync')

class FeedbackSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='appcivist_id', read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    parent_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Vote
        exclude = ('appcivist_id', 'sync', 'author', 'parent_proposal', 'parent_comment')