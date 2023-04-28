import csv
import os
import zipfile

import requests
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
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
    COMMUNITY_SETTINGS_UPDATE_SUCCESS, COMMUNITY_ID_NOT_PROVIDED, COMMUNITY_SETTING_RETRIEVE_SUCCESSFULLY, \
    STORY_RETRIEVE_SUCCESSFULLY, PROGRAM_RETRIEVED_SUCCESSFULLY, \
    PROGRAM_UPDATED_SUCCESSFULLY, COPY_CODE_RETRIEVED_SUCCESSFULLY, PROGRAM_CREATED_SUCCESSFULLY, \
    COPY_CODE_CREATED_SUCCESSFULLY, COPY_CODE_UPDATED_SUCCESSFULLY, CREATIVE_CODE_RETRIEVED_SUCCESSFULLY, \
    CREATIVE_CODE_CREATED_SUCCESSFULLY, CREATIVE_CODE_UPDATED_SUCCESSFULLY, SOMETHING_WENT_WRONG
from community.filters import StoriesFilter
from community.models import Story, Community, Tag, CommunitySetting, Channel, CommunityChannel, Program, CopyCode, \
    CreativeCode
from community.permissions import IsAuthorizedForListCreate
from community.serializers import StorySerializer, CommunityTagsSerializer, \
    TagCreateSerializer, CommunitySettingsSerializer, ChannelListCreateSerializer, \
    ChannelRetrieveUpdateDestroySerializer, CommunityChannelSerializer, ProgramSerializer, CopyCodeSerializer, \
    CreativeCodeSerializer


class CommunityList(APIView):
    permission_classes = [IsAuthenticated, IsAuthorizedForListCreate]

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    def get(self, request, *args, **kwargs):
        community_data = Community.objects.distinct('id', 'name').filter(is_trashed=False).values('id',
                                                                                                  'name').order_by('id')
        tag_data = Tag.objects.filter(is_trashed=False).values('id', name=F('title')).distinct('id', 'name').order_by(
            'id')
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
        return Response({'data': serializer.data, 'message': COMMUNITY_SETTING_RETRIEVE_SUCCESSFULLY},
                        status=status.HTTP_200_OK)

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
        return Response({'data': serializer.data, 'message': CHANNEL_CREATED_SUCCESSFULLY},
                        status=status.HTTP_201_CREATED)


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


class ProgramListCreateAPIView(generics.ListCreateAPIView):
    """
    View for creating program and view list of all programs
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    serializer_class = ProgramSerializer
    queryset = Program.objects.filter(is_trashed=False).order_by('-id')
    pagination_class = CustomPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['community__name', 'title']
    ordering_fields = ['title', 'community__name']
    permission_classes = [IsAuthenticated, IsAuthorizedForListCreate]

    def get(self, request, *args, **kwargs):
        """
        API to get list of programs
        """
        self.queryset = self.filter_queryset(self.queryset)
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return Response({'data': response.data, 'message': PROGRAM_RETRIEVED_SUCCESSFULLY})

    def post(self, request, *args, **kwargs):
        """API to create program"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': "", 'message': PROGRAM_CREATED_SUCCESSFULLY},
                        status=status.HTTP_201_CREATED)


class ProgramRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for retrieving, update and delete program
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    serializer_class = ProgramSerializer
    queryset = Program.objects.filter(is_trashed=False).order_by('-id')
    lookup_field = 'id'
    permission_classes = [IsAuthenticated, IsAuthorizedForListCreate]

    def get(self, request, *args, **kwargs):
        """API to get program"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data, 'message': PROGRAM_RETRIEVED_SUCCESSFULLY})

    def put(self, request, *args, **kwargs):
        """put request to update program"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': "", 'message': PROGRAM_UPDATED_SUCCESSFULLY})

    def delete(self, request, *args, **kwargs):
        """delete request to inactive program"""
        instance = get_object_or_404(Program, pk=kwargs.get('id'), is_trashed=False)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CopyCodeListCreateAPIView(generics.ListCreateAPIView):
    """
    View for creating copy code and view list of all copy codes
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    serializer_class = CopyCodeSerializer
    queryset = CopyCode.objects.filter(is_trashed=False).order_by('-id')
    pagination_class = CustomPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['subject_line', 'title']
    ordering_fields = ['title', 'subject_line']
    permission_classes = [IsAuthenticated, IsAuthorizedForListCreate]

    def get(self, request, *args, **kwargs):
        """
        API to get list of copy codes
        """
        self.queryset = self.filter_queryset(self.queryset)
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return Response({'data': response.data, 'message': COPY_CODE_RETRIEVED_SUCCESSFULLY})

    def post(self, request, *args, **kwargs):
        """API to create copy code"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': "", 'message': COPY_CODE_CREATED_SUCCESSFULLY},
                        status=status.HTTP_201_CREATED)


class CopyCodeRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for retrieving, update and delete copy code
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    serializer_class = CopyCodeSerializer
    queryset = CopyCode.objects.filter(is_trashed=False).order_by('-id')
    lookup_field = 'id'
    permission_classes = [IsAuthenticated, IsAuthorizedForListCreate]

    def get(self, request, *args, **kwargs):
        """API to get copy code"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data, 'message': COPY_CODE_RETRIEVED_SUCCESSFULLY})

    def put(self, request, *args, **kwargs):
        """put request to update copy code"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': "", 'message': COPY_CODE_UPDATED_SUCCESSFULLY})

    def delete(self, request, *args, **kwargs):
        """delete request to inactive copy code"""
        instance = get_object_or_404(CopyCode, pk=kwargs.get('id'), is_trashed=False)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CreativeCodeListCreateAPIView(generics.ListCreateAPIView):
    """
    View for creating copy code and view list of all creative codes
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    serializer_class = CreativeCodeSerializer
    queryset = CreativeCode.objects.filter(is_trashed=False).order_by('-id')
    pagination_class = CustomPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'file_name', 'format', 'creative_theme', 'link']
    ordering_fields = ['title', 'file_name', 'format', 'creative_theme', 'link']
    permission_classes = [IsAuthenticated, IsAuthorizedForListCreate]

    def get(self, request, *args, **kwargs):
        """
        API to get list of creative codes
        """
        self.queryset = self.filter_queryset(self.queryset)
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return Response({'data': response.data, 'message': CREATIVE_CODE_RETRIEVED_SUCCESSFULLY})

    def post(self, request, *args, **kwargs):
        """API to create creative code"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': "", 'message': CREATIVE_CODE_CREATED_SUCCESSFULLY},
                        status=status.HTTP_201_CREATED)


class CreativeCodeRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for retrieving, update and delete creative code
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    serializer_class = CreativeCodeSerializer
    queryset = CreativeCode.objects.filter(is_trashed=False).order_by('-id')
    lookup_field = 'id'
    permission_classes = [IsAuthenticated, IsAuthorizedForListCreate]

    def get(self, request, *args, **kwargs):
        """API to get creative code"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data, 'message': CREATIVE_CODE_RETRIEVED_SUCCESSFULLY})

    def put(self, request, *args, **kwargs):
        """put request to update creative code"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': "", 'message': CREATIVE_CODE_UPDATED_SUCCESSFULLY})

    def delete(self, request, *args, **kwargs):
        """delete request to inactive creative code"""
        instance = get_object_or_404(CreativeCode, pk=kwargs.get('id'), is_trashed=False)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ExportArticleCsv(APIView):

    def post(self, request, *args, **kwargs):
        try:
            story_obj = Story.objects.get(id=request.data.get("story_id"))
            data_columns = request.data.get("data_columns")

            response = HttpResponse(content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="story_details.zip"'

            # Create a zip file object
            zip_file = zipfile.ZipFile(response, 'w', zipfile.ZIP_DEFLATED)

            temp_file = 'story_details.csv'
            with open(temp_file, 'w', newline='') as file:
                column_values = []
                column_names = []
                for col in data_columns:
                    column_names.append(col)
                    if col == 'id':
                        column_values.append(story_obj.id)
                    elif col == 'story_id':
                        column_values.append(story_obj.story_id)
                    elif col == "title":
                        column_values.append(story_obj.title)
                    elif col == "lede":
                        column_values.append(story_obj.lede)
                    elif col == "image":
                        column_values.append(story_obj.get_image())
                    elif col == "community":
                        column_values.append(story_obj.community.name if story_obj.community else "")
                    elif col == "community_id":
                        column_values.append(story_obj.community_id)
                    elif col == "publication_date":
                        column_values.append(story_obj.publication_date)
                    elif col == "status":
                        column_values.append(story_obj.status)
                    elif col == "body":
                        column_values.append(story_obj.body)
                    elif col == "p_url":
                        column_values.append(story_obj.p_url)
                    elif col == "tag":
                        column_values.append(story_obj.storytag_set)
                    elif col == "category":
                        column_values.append(story_obj.storycategory_set)
                writer = csv.writer(file)
                writer.writerow(column_names)
                writer.writerow(column_values)

            zip_file.write(temp_file, arcname='my_csv_file.csv')

            for image in story_obj.get_image():
                resp = requests.get(image)

                if resp.status_code == 200:
                    zip_file.writestr(image.split("/")[-1], resp.content)

            # Close the zip file and remove the temporary CSV file
            zip_file.close()
            os.remove(temp_file)

            return response

        except Exception as err:
            print(f"{err}")
            return Response({"error": True, "message": SOMETHING_WENT_WRONG},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
