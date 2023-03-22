from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from common.pagination import CustomPagination
from community.models import Story
from community.serializers import StorySerializer


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
