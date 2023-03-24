from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from common.pagination import CustomPagination
from community.models import Story, Community
from community.serializers import StorySerializer, CommunityTagsSerializers


class StoriesList(generics.ListAPIView):
    """
    Stories List API
    """

    queryset = Story.objects.all()
    serializer_class = StorySerializer
    filter_backends = [OrderingFilter, SearchFilter]
    ordering_fields = ['title', 'p_url', 'community__name']
    search_fields = ['p_url', 'community__name', 'tag_community__title']
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]


class CommunityTagsList(generics.ListAPIView):
    """
    Community Tags List API
    """

    queryset = Community.objects.all()
    serializer_class = CommunityTagsSerializers
    filter_backends = [OrderingFilter]
    ordering_fields = ['name']
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]






