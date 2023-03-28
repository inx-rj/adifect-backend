from rest_framework.filters import OrderingFilter
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import CustomPagination
from common.search import get_query
from community.filters import StoriesFilter
from community.models import Story, Community, Tag
from community.permissions import IsAuthorizedForListCreate
from community.serializers import StorySerializer, CommunityTagsSerializer, \
    TagCreateSerializer


class CommunityList(APIView):

    def get(self, request, *args, **kwargs):
        community_data = Community.objects.distinct('name').filter(is_trashed=False).values_list('name', flat=True)
        tag_data = Tag.objects.distinct('title').filter(is_trashed=False).values_list('title', flat=True)
        status_data = ['Published', 'Draft', 'Scheduled']
        data = {
            "community": community_data,
            "tag": tag_data,
            "status": status_data
        }
        return Response(data)


class StoriesList(generics.ListAPIView):
    """
    Stories List API
    """

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
            return Response(response.data)
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)


class CommunityTagsListCreate(generics.ListCreateAPIView):
    """
    Community Tags List API
    """

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
