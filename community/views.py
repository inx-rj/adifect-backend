from rest_framework import generics, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import custom_handle_exception
from common.pagination import CustomPagination
from common.search import get_query
from community.constants import TAG_CREATED, STORIES_RETRIEVE_SUCCESSFULLY, COMMUNITY_TAGS_RETRIEVE_SUCCESSFULLY, \
    COMMUNITY_TAGS_STATUS_DATA, COMMUNITY_SETTINGS_SUCCESS, COMMUNITY_SETTINGS_RETRIEVE_SUCCESSFULLY
from community.filters import StoriesFilter
from community.models import Story, Community, Tag
from community.permissions import IsAuthorizedForListCreate
from community.serializers import StorySerializer, CommunityTagsSerializer, \
    TagCreateSerializer, CommunitySettingsSerializer, CommunitySerializer


class CommunityList(APIView):
    permission_classes = [IsAuthenticated, IsAuthorizedForListCreate]

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    def get(self, request, *args, **kwargs):
        community_data = Community.objects.distinct('name').filter(is_trashed=False).values_list('name', flat=True)
        tag_data = Tag.objects.distinct('title').filter(is_trashed=False).values_list('title', flat=True)
        status_data = ['Published', 'Draft', 'Scheduled']
        data = {
            "community": community_data,
            "tag": tag_data,
            "status": status_data
        }
        return Response({'data': data, 'message': COMMUNITY_TAGS_STATUS_DATA})


class StoriesList(generics.ListAPIView):
    """
    Stories List API
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    queryset = Story.objects.filter(is_trashed=False)
    serializer_class = StorySerializer
    filterset_class = StoriesFilter
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, IsAuthorizedForListCreate]

    def get(self, request, *args, **kwargs):
        self.queryset = self.filter_queryset(self.queryset)
        if search := request.GET.get('search'):
            entry_query = get_query(search, ['community__name', 'status'])
            self.queryset = self.queryset.filter(entry_query)
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return Response({'data': response.data, 'message': STORIES_RETRIEVE_SUCCESSFULLY})


class CommunityTagsListCreate(generics.ListCreateAPIView):
    """
    Community Tags List API
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    queryset = Community.objects.filter(is_trashed=False)
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


class CommunitySettingsView(generics.ListCreateAPIView):
    """
    API to add and list community social media credentials.
    """

    queryset = Community.objects.all()
    pagination_class = CustomPagination
    filter_backends = [OrderingFilter, SearchFilter]
    ordering_fields = ['name']
    search_fields = ['name']
    permission_classes = [IsAuthenticated, IsAuthorizedForListCreate]

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    def get_serializer_class(self):
        """
        Returns serializer according to request.
        """
        if self.request.method == "GET":
            return CommunitySerializer
        else:
            return CommunitySettingsSerializer

    def get(self, request, *args, **kwargs):
        self.queryset = self.filter_queryset(self.queryset)
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return Response({'data': response.data, 'message': COMMUNITY_SETTINGS_RETRIEVE_SUCCESSFULLY},
                            status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        if not request.data:
            return Response({'data': '', 'message': 'Data not provided.'}, status=status.HTTP_400_BAD_REQUEST)

        community_id = request.data.pop('community_id')
        data_list = []
        for channel in request.data:
            data = {
                'channel': channel,
                'community': community_id,
                'url': request.data.get(channel).get('url'),
                'api_key': request.data.get(channel).get('api_key')
            }
            data_list.append(data)
        serializer = self.get_serializer(data=data_list, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': '', 'message': COMMUNITY_SETTINGS_SUCCESS}, status=status.HTTP_201_CREATED)
