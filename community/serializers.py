from rest_framework import serializers

from community.models import Story, Community, Tag, CommunityChannel, CommunitySetting, Channel, Program, CopyCode


class ChannelRetrieveUpdateDestroySerializer(serializers.ModelSerializer):
    """
    Serializer to View Channel and Update Channel
    """

    class Meta:
        model = Channel
        fields = ['id', 'name', 'is_active']


class CommunityChannelSerializer(serializers.ModelSerializer):
    channel_data = serializers.SerializerMethodField()

    class Meta:
        model = CommunityChannel
        fields = ('community_setting', 'channel', 'url', 'api_key', 'channel_data')

    def get_channel_data(self, obj):
        return ChannelRetrieveUpdateDestroySerializer(instance=obj.channel).data

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
    image = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = '__all__'

    def get_image(self, obj):
        return obj.get_image()


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
        model = CommunitySetting
        fields = ('id', 'community', 'is_active')


    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['community'] = CommunitySerializer(instance.community).data
        representation['community_channels'] = CommunityChannelSerializer(instance.community_channel_community.all(),
                                                                          many=True, read_only=True).data
        return representation


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


class ChannelListCreateSerializer(serializers.ModelSerializer):
    """
    Serializer to View List of Channel and add Channel
    """

    class Meta:
        model = Channel
        fields = ['id', 'name', 'is_active']


class ProgramSerializer(serializers.ModelSerializer):
    """
    Serializer to retrieve, add and update program
    """
    community = serializers.PrimaryKeyRelatedField(queryset=Community.objects.all(), required=True)

    class Meta:
        model = Program
        fields = ['id', 'title', 'community']

    def to_representation(self, instance):
        """function to add custom response of community"""
        representation = super(ProgramSerializer, self).to_representation(instance)
        representation['community'] = CommunitySerializer(instance.community).data
        return representation


class CopyCodeSerializer(serializers.ModelSerializer):
    """
    Serializer to retrieve, add and update copy code
    """

    class Meta:
        model = CopyCode
        fields = ['id', 'title', 'subject_line', 'body', 'notes']
