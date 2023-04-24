from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import custom_handle_exception
from common.pagination import CustomPagination
from common.search import get_query
from community.constants import TAG_CREATED, STORIES_RETRIEVE_SUCCESSFULLY, COMMUNITY_TAGS_RETRIEVE_SUCCESSFULLY, \
    COMMUNITY_TAGS_STATUS_DATA, COMMUNITY_SETTINGS_SUCCESS, COMMUNITY_SETTINGS_RETRIEVE_SUCCESSFULLY, \
    CHANNEL_RETRIEVED_SUCCESSFULLY, CHANNEL_CREATED_SUCCESSFULLY, CHANNEL_UPDATED_SUCCESSFULLY, \
    COMMUNITY_SETTINGS_UPDATE_SUCCESS, SOMETHING_WENT_WRONG, COMMUNITY_ID_NOT_PROVIDED, CHANNEL_ID_NOT_PROVIDED, \
    COMMUNITY_SETTING_RETRIEVE_SUCCESSFULLY, STORY_RETRIEVE_SUCCESSFULLY
from community.filters import StoriesFilter
from community.models import Story, Community, Tag, CommunitySetting, Channel, CommunityChannel
from community.permissions import IsAuthorizedForListCreate
from community.serializers import StorySerializer, CommunityTagsSerializer, \
    TagCreateSerializer, CommunitySettingsSerializer, CommunitySerializer, ChannelListCreateSerializer, ChannelRetrieveUpdateDestroySerializer, CommunityChannelSerializer


class CommunityList(APIView):
    permission_classes = [IsAuthenticated, IsAuthorizedForListCreate]

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    def get(self, request, *args, **kwargs):
        community_data = Community.objects.distinct('id', 'name').filter(is_trashed=False).values('id', 'name').order_by('id')
        tag_data = Tag.objects.filter(is_trashed=False).values('id', name=F('title')).distinct('id', 'name').order_by('id')
        status_data = [
            {
                "id": 1,
                "name": "Published"
            },
            {
                "id": 2,
                "name": "Draft"
            },
            {
                "id": 3,
                "name": "Scheduled"
            }
        ]
        data = {
            "community": community_data,
            "tag": tag_data,
            "status": status_data
        }
        return Response({'data': data, 'message': COMMUNITY_TAGS_STATUS_DATA})


class StoriesList(generics.ListAPIView, generics.RetrieveAPIView):
    """
    Stories List API
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    queryset = Story.objects.filter(is_trashed=False).order_by('-id')
    serializer_class = StorySerializer
    filterset_class = StoriesFilter
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, IsAuthorizedForListCreate]
    lookup_field = 'id'

    def get(self, request, *args, **kwargs):
        if not kwargs.get('id'):
            self.queryset = self.filter_queryset(self.queryset)
            if search := request.GET.get('search'):
                entry_query = get_query(search, ['community__name', 'status'])
                self.queryset = self.queryset.filter(entry_query)
            page = self.paginate_queryset(self.queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                response = self.get_paginated_response(serializer.data)
                return Response({'data': response.data, 'message': STORIES_RETRIEVE_SUCCESSFULLY})

        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data, 'message': STORY_RETRIEVE_SUCCESSFULLY},
                        status=status.HTTP_200_OK)


class CommunityTagsListCreate(generics.ListCreateAPIView):
    """
    Community Tags List API
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    queryset = Community.objects.filter(is_trashed=False).order_by('-id')
    filter_backends = [OrderingFilter]
    ordering_fields = ['name']
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, IsAuthorizedForListCreate]

    def get_serializer_class(self):
        """
        Returns serializer according to request.
        """
        if self.request.method == "GET":
            return CommunityTagsSerializer
        else:
            return TagCreateSerializer

    def get(self, request, *args, **kwargs):
        """
        To retrieve community and it's tags
        """
        self.queryset = self.filter_queryset(self.queryset)
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return Response({'data': response.data, 'message': COMMUNITY_TAGS_RETRIEVE_SUCCESSFULLY})

    def post(self, request, *args, **kwargs):
        """post request to create tags"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': serializer.data, 'message': TAG_CREATED}, status=status.HTTP_201_CREATED)


class CommunitySettingsView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    """
    API to add and list community social media credentials.
    """

    queryset = CommunitySetting.objects.filter(is_trashed=False).order_by('-id')
    serializer_class = CommunitySettingsSerializer
    pagination_class = CustomPagination
    filter_backends = [OrderingFilter, SearchFilter]
    ordering_fields = ['community__name']
    search_fields = ['community__name']
    permission_classes = [IsAuthenticated, IsAuthorizedForListCreate]
    lookup_field = 'id'

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    def get(self, request, *args, **kwargs):
        if not kwargs.get('id'):
            self.queryset = self.filter_queryset(self.queryset)
            page = self.paginate_queryset(self.queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                response = self.get_paginated_response(serializer.data)
                return Response({'data': response.data, 'message': COMMUNITY_SETTINGS_RETRIEVE_SUCCESSFULLY},
                                status=status.HTTP_200_OK)
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data, 'message': COMMUNITY_SETTING_RETRIEVE_SUCCESSFULLY}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        if not request.data.get('community_id'):
            return Response({'data': '', 'message': COMMUNITY_ID_NOT_PROVIDED}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            community_id = request.data.pop('community_id')
            serializer = self.get_serializer(data={'community': community_id})
            serializer.is_valid(raise_exception=True)
            community_setting_obj = serializer.save()

            data_list = []
            for channel in request.data.get("channel"):
                channel["community_setting"] = community_setting_obj.id
                data_list.append(channel)
            serializer = CommunityChannelSerializer(data=data_list, many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response({'data': '', 'message': COMMUNITY_SETTINGS_SUCCESS}, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.data.get('community_id'):
            request.data.pop('community_id')
        CommunityChannel.objects.filter(community_setting=instance).delete()
        data_list = []
        for channel in request.data.get("channel"):
            channel["community_setting"] = instance.id
            data_list.append(channel)
        serializer = CommunityChannelSerializer(data=data_list, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': '', 'message': COMMUNITY_SETTINGS_UPDATE_SUCCESS}, status=status.HTTP_200_OK)


class ChannelListCreateAPIView(generics.ListCreateAPIView):
    """
    View for creating channel and view list of all channels
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    serializer_class = ChannelListCreateSerializer
    queryset = Channel.objects.filter(is_trashed=False).order_by('-id')
    pagination_class = CustomPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'is_active']
    permission_classes = [IsAuthenticated, IsAuthorizedForListCreate]

    def get(self, request, *args, **kwargs):
        """
        API to get list of channels
        """
        self.queryset = self.filter_queryset(self.queryset)
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return Response({'data': response.data, 'message': CHANNEL_RETRIEVED_SUCCESSFULLY})

    def post(self, request, *args, **kwargs):
        """API to create channel"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': serializer.data, 'message': CHANNEL_CREATED_SUCCESSFULLY}, status=status.HTTP_201_CREATED)


class ChannelRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for retrieving, update and delete channel
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    serializer_class = ChannelRetrieveUpdateDestroySerializer
    queryset = Channel.objects.filter(is_trashed=False).order_by('-id')
    lookup_field = 'id'
    permission_classes = [IsAuthenticated, IsAuthorizedForListCreate]

    def get(self, request, *args, **kwargs):
        """API to get channel"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data, 'message': CHANNEL_RETRIEVED_SUCCESSFULLY}, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        """API to update channel"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': serializer.data, 'message': CHANNEL_UPDATED_SUCCESSFULLY}, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """API to inactive channel"""
        instance = get_object_or_404(Channel, pk=kwargs.get('id'), is_trashed=False)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
