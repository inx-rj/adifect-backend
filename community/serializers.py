from rest_framework import serializers

from community.models import Story, Community, Tag, CommunityChannel, Channel


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = '__all__'


class CommunitySerializer(serializers.ModelSerializer):
    """
    Serializer to get community data.
    """
    channel = ChannelSerializer(many=True)

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


class CommunityTagsSerializer(serializers.ModelSerializer):
    """
    Serializer to get community tags data.
    """

    tags = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = ('id', 'community_id', 'name', 'client_company_id', 'state', 'is_active', 'community_metadata', 'tags')

    def get_tags(self, obj):
        return TagSerializer(obj.tag_community, many=True).data


class TagCreateSerializer(serializers.ModelSerializer):
    """
    Serializer to add tag data.
    """
    community = serializers.PrimaryKeyRelatedField(required=True, queryset=Community.objects.all())

    class Meta:
        model = Tag
        fields = ['community', 'title', 'description']


class CommunitySettingsSerializer(serializers.ModelSerializer):
    """
    Community settings serializer to validate and create data.
    """

    class Meta:
        model = CommunityChannel
        fields = '__all__'

# class CommunityListSerializer(serializers.ModelSerializer):
#     """
#     Serializer to list community data.
#     """
#
#     class Meta:
#         model = Community
#         fields = ['name']
#
#
# class StatusListSerializer(serializers.ModelSerializer):
#     """
#     Serializer to list community status data.
#     """
#
#     class Meta:
#         model = Story
#         fields = ['status']
#
#
# class TagListSerializer(serializers.ModelSerializer):
#     """
#     Serializer to list tag data.
#     """
#
#     class Meta:
#         model = Tag
#         fields = ['title']
