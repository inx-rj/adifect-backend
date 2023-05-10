from django.db import transaction
from rest_framework import serializers

from community.models import Story, Community, Tag, CommunityChannel, CommunitySetting, Channel, Program, CopyCode, \
    CreativeCode, Category, StoryTag


class ChannelRetrieveUpdateDestroySerializer(serializers.ModelSerializer):
    """
    Serializer to View Channel and Update Channel
    """

    class Meta:
        model = Channel
        fields = ['id', 'name', 'is_active']


class CommunityChannelSerializer(serializers.ModelSerializer):
    channel_data = serializers.SerializerMethodField()
    channel = serializers.PrimaryKeyRelatedField(queryset=Channel.objects.filter(is_trashed=False),
                                                 required=True, write_only=True)

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


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer to get tag data.
    """

    class Meta:
        model = Category
        fields = '__all__'


class StorySerializer(serializers.ModelSerializer):
    """
    Serializer to get story data.
    """

    community = CommunitySerializer()
    tag = TagSerializer(many=True)
    community_tags = serializers.SerializerMethodField()
    category = CategorySerializer(many=True)
    image = serializers.SerializerMethodField()
    community_channels = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = '__all__'

    def get_community_tags(self, obj):
        return TagSerializer(obj.community.tag_community.all(), many=True).data

    def get_community_channels(self, obj):
        if obj.community.community_setting_community:
            return CommunityChannelSerializer(
                obj.community.community_setting_community.first().community_channel_community.all(),
                many=True).data
        return []

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
    community = serializers.PrimaryKeyRelatedField(required=True, queryset=Community.objects.filter(is_trashed=False))

    class Meta:
        model = Tag
        fields = ['community', 'title']


class CommunitySettingsSerializer(serializers.ModelSerializer):
    """
    Community settings serializer to validate and create data.
    """
    community_id = serializers.PrimaryKeyRelatedField(queryset=Community.objects.filter(is_trashed=False),
                                                      required=True, write_only=True)
    channel = CommunityChannelSerializer(many=True, write_only=True)

    class Meta:
        model = CommunitySetting
        fields = ('id', 'community_id', 'channel', 'is_active')

    def validate_community_id(self, value):
        if self.context.get('id'):
            if CommunitySetting.objects.exclude(id=self.context.get('id')).filter(is_trashed=False, community=value).exists():
                raise serializers.ValidationError("Community Setting for this community already exists.")
        elif CommunitySetting.objects.filter(is_trashed=False, community=value).exists():
            raise serializers.ValidationError("Community Setting for this community already exists.")
        return value

    def create(self, validated_data):
        channel_data = validated_data.pop("channel", [])
        community = validated_data.pop("community_id")
        with transaction.atomic():
            instance = CommunitySetting.objects.create(**validated_data, community=community)

            for channel in channel_data:
                if not channel.get('channel'):
                    raise serializers.ValidationError({"channel": ["This field is required!"]})
                channel_obj = Channel.objects.get(id=channel.get('channel').id)
                CommunityChannel.objects.create(community_setting=instance, channel=channel_obj, url=channel.get('url'),
                                                api_key=channel.get('api_key'))
        return instance

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.community = validated_data.get("community_id")
            instance.save(update_fields=["community"])

            for channel in validated_data.get("channel", []):
                if not channel.get('channel'):
                    raise serializers.ValidationError({"channel": ["This field is required!"]})
                channel_obj = Channel.objects.get(id=channel.get('channel').id)
                CommunityChannel.objects.create(community_setting=instance, channel=channel_obj, url=channel.get('url'),
                                                api_key=channel.get('api_key'))
        return instance

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
    community = serializers.PrimaryKeyRelatedField(queryset=Community.objects.filter(is_trashed=False), required=True)

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


class CreativeCodeSerializer(serializers.ModelSerializer):
    """
    Serializer to retrieve, add and update creative code
    """

    class Meta:
        model = CreativeCode
        fields = ['id', 'title', 'file_name', 'format', 'creative_theme', 'horizontal_pixel', 'vertical_pixel',
                  'duration', 'link', 'notes']


class AddStoryTagsSerializer(serializers.Serializer):
    story = serializers.PrimaryKeyRelatedField(queryset=Story.objects.filter(is_trashed=False), required=True)
    title = serializers.CharField(required=True)

    def create(self, validated_data):
        try:
            if StoryTag.objects.filter(story_id=validated_data.get("story"),
                                       tag_id=int(validated_data.get("title"))).exists():
                raise serializers.ValidationError("Tag already exists in the story.")
            if not Tag.objects.filter(id=validated_data.get('title')).first():
                raise serializers.ValidationError(
                    {"story": [f"Invalid pk \"{validated_data.get('title')}\" - object does not exist."]})

            story_tag_obj = StoryTag.objects.create(story=validated_data.get("story"),
                                                    tag_id=validated_data.get("title"))

        except (ValueError, TypeError):
            community_obj = validated_data.get('story').community
            if Tag.objects.filter(title__iexact=validated_data.get("title")).exists():
                raise serializers.ValidationError("Tag already exists in the list.")

            tag_obj = Tag.objects.create(community=community_obj, title=validated_data.get("title"))

            story_tag_obj = StoryTag.objects.create(story=validated_data.get("story"), tag=tag_obj)

        return story_tag_obj


class StoryTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = StoryTag
        fields = "__all__"
