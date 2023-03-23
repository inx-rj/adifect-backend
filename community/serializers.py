from rest_framework import serializers

from community.models import Story, Community, Tag


class CommunitySerializer(serializers.ModelSerializer):
    """
    Serializer to get community data.
    """

    class Meta:
        model = Community
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer to get tag data.
    """

    class Meta:
        model = Tag
        fields = '__all__'


class StorySerializer(serializers.ModelSerializer):
    """
    Serializer to get story data.
    """

    community = CommunitySerializer()
    tag = TagSerializer(many=True)

    class Meta:
        model = Story
        fields = '__all__'

