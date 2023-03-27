from rest_framework.filters import OrderingFilter
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.pagination import CustomPagination
from common.search import get_query
from community.filters import StoriesFilter
from community.models import Story, Community
from community.serializers import StorySerializer, CommunityTagsSerializers


class StoriesList(generics.ListAPIView):
    """
    Stories List API
    """

    queryset = Story.objects.all()
    serializer_class = StorySerializer
    filterset_class = StoriesFilter
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

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






