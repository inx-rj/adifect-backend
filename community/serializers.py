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


class CommunityTagsSerializers(serializers.ModelSerializer):
    """
    Serializer to get community tags data.
    """

    tags = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = ('community_id', 'name', 'client_company_id', 'state', 'is_active', 'community_metadata', 'tags')

    def get_tags(self, obj):
        return TagSerializer(obj.tag_community, many=True).data

