import csv
import logging
import os
import zipfile

import requests
import io

from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import View
from requests_oauthlib import OAuth1Session
from rest_framework import generics, status, serializers
from rest_framework.exceptions import ValidationError
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
    CREATIVE_CODE_CREATED_SUCCESSFULLY, CREATIVE_CODE_UPDATED_SUCCESSFULLY, SOMETHING_WENT_WRONG, NOT_FOUND, \
    TAG_TO_STORY_ADDED_SUCCESSFULLY, CREATIVE_CODE_DATA_IMPORTED_SUCCESSFULLY, AUDIENCE_RETRIEVED_SUCCESSFULLY
from community.filters import StoriesFilter
from community.models import Story, Community, Tag, CommunitySetting, Channel, CommunityChannel, Program, CopyCode, \
    CreativeCode, StoryTag, Audience, StoryStatusConfig
from community.permissions import IsAuthorizedForListCreate, LinkedInRequirePostPermission
from community.serializers import StorySerializer, CommunityTagsSerializer, \
    TagCreateSerializer, CommunitySettingsSerializer, ChannelListCreateSerializer, \
    ChannelRetrieveUpdateDestroySerializer, CommunityChannelSerializer, ProgramSerializer, CopyCodeSerializer, \
    CreativeCodeSerializer, AddStoryTagsSerializer, StoryTagSerializer, TagSerializer, \
    CommunityAudienceListCreateSerializer
from .tasks import add_community_audiences, delete_story_data
from .utils import validate_client_id_opnsesame

logger = logging.getLogger('django')


class CommunityList(APIView):
    permission_classes = [IsAuthenticated]

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
    # permission_classes = [IsAuthenticated, IsAuthorizedForListCreate]
    lookup_field = 'id'

    def get(self, request, *args, **kwargs):
        if not kwargs.get('id'):
            self.queryset = self.filter_queryset(self.queryset)
            if search := request.GET.get('search'):
                entry_query = get_query(search, ['community__name', 'status', 'title'])
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
    filter_backends = [OrderingFilter, SearchFilter]
    search_fields = ['name', 'tag_community__title']
    ordering_fields = ['name']
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]
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

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        community_setting_obj = serializer.save()
        StoryStatusConfig.objects.create(community=community_setting_obj.community, last_page=0)
        if opn_sesame_obj := CommunityChannel.objects.filter(
            community_setting=community_setting_obj,
            channel__name__iexact='opnsesame',
        ).first():
            organization_id = opn_sesame_obj.meta_data.get("organization_id", "")
            api_key = opn_sesame_obj.meta_data.get("api_key", "")

            if validate_client_id_opnsesame(client_id=organization_id, api_key=api_key):
                # Call Background task for fetching audiences
                logger.info("VALID CLIENT_ID")
                logger.info("Calling background task to add audiences.")
                add_community_audiences.delay(organization_id, api_key, community_setting_obj.community_id)

        return Response({'data': '', 'message': COMMUNITY_SETTINGS_SUCCESS}, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # story_data_entry.delay(instance.community.community_id, instance.community.community_id,
        #                        instance_community_delete=True)
        delete_story_data.delay(instance.community.community_id)
        Audience.objects.filter(community_id=instance.community.id).update(is_trashed=True)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        community_id = instance.community.community_id
        old_opn_obj = CommunityChannel.objects.filter(community_setting=instance,
                                                      channel__name__iexact='opnsesame').first()
        old_opn_organization_id = None
        old_opn_api_key = None
        old_community_id = instance.community.id

        if old_opn_obj:
            old_opn_organization_id = old_opn_obj.meta_data.get("organization_id", "")
            old_opn_api_key = old_opn_obj.meta_data.get("api_key", "")

        with transaction.atomic():
            CommunityChannel.objects.filter(community_setting=instance).delete()
            serializer = CommunitySettingsSerializer(instance=instance, data=request.data,
                                                     context={"channel": request.data.get("channel"),
                                                              "id": kwargs.get('id')})
            serializer.is_valid(raise_exception=True)
            community_setting_obj = serializer.save()
            new_opn_obj = CommunityChannel.objects.filter(community_setting=community_setting_obj,
                                                          channel__name__iexact='opnsesame').first()
            if old_community_id != community_setting_obj.community.id:
                # story_data_entry.delay(community_setting_obj.community.community_id, community_id)
                delete_story_data.delay(community_id)
                StoryStatusConfig.objects.create(community=community_setting_obj.community, last_page=0)
                Audience.objects.filter(community_id=old_community_id).update(is_trashed=True)

            if (
                new_opn_obj
                and (
                    old_community_id != community_setting_obj.community.id
                    or old_opn_organization_id != new_opn_obj.meta_data.get("organization_id", "")
                    or old_opn_api_key != new_opn_obj.meta_data.get("api_key", "")
                )
                and validate_client_id_opnsesame(
                    client_id=new_opn_obj.meta_data.get("organization_id", ""),
                    api_key=new_opn_obj.meta_data.get("api_key", "")
                )
            ):

                # Call Background task for fetching audiences
                logger.info("VALID CLIENT_ID")
                logger.info("Calling background task to add audiences.")
                add_community_audiences.delay(new_opn_obj.meta_data.get("organization_id", ""),
                                              new_opn_obj.meta_data.get("api_key", ""),
                                              community_setting_obj.community_id)


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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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
    search_fields = ['subject_line', 'title', 'body', 'notes']
    ordering_fields = ['title', 'subject_line', 'body', 'notes']
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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
    search_fields = ['title', 'file_name', 'format', 'creative_theme', 'horizontal_pixel', 'vertical_pixel', 'duration',
                     'link', 'notes']
    ordering_fields = ['title', 'file_name', 'format', 'creative_theme', 'horizontal_pixel', 'vertical_pixel',
                       'duration', 'link', 'notes']
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            story_obj = Story.objects.get(id=request.data.get("story_id"))
        except Story.DoesNotExist as err:
            return Response({"error": True, "message": NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        try:
            data_columns = request.data.get("data_columns")
            response = HttpResponse(content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="story_details.zip"'

            # Create a zip file object
            zip_file = zipfile.ZipFile(response, 'w', zipfile.ZIP_DEFLATED)

            temp_file = 'story_details.csv'
            with open(temp_file, 'w', newline='', encoding='utf-8') as file:
                column_values = []
                column_names = []
                for col in data_columns:
                    column_names.append(col)
                    if col == 'id':
                        column_values.append(story_obj.id)
                    elif col == 'story_id':
                        column_values.append(story_obj.story_id)
                    elif col == 'story_url':
                        column_values.append(story_obj.story_url)
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
                    elif col == "publication":
                        column_values.append(story_obj.publication_date)
                    elif col == "status":
                        column_values.append(story_obj.status)
                    elif col == "body":
                        column_values.append(story_obj.body)
                    elif col == "p_url":
                        column_values.append(story_obj.p_url)
                    elif col == "tag":
                        tags = []
                        for tag in story_obj.storytag_set.all():
                            tags.append(tag.tag.title)
                        column_values.append(tags)
                    elif col == "category":
                        categories = []
                        for category in story_obj.storycategory_set.all():
                            categories.append(category.category.title)
                        column_values.append(categories)
                    else:
                        column_values.append("")
                writer = csv.writer(file)
                writer.writerow(column_names)
                writer.writerow(column_values)

            zip_file.write(temp_file, arcname='story.csv')

            if "image" in data_columns:
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
                            status=status.HTTP_400_BAD_REQUEST)


class AddStoryTagsView(generics.CreateAPIView, generics.DestroyAPIView):
    """
    API to add tags to existing story and also associate tag to community.
    """
    serializer_class = AddStoryTagsSerializer
    permission_classes = [IsAuthenticated]

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': "", 'message': TAG_TO_STORY_ADDED_SUCCESSFULLY}, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        serializer = StoryTagSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        StoryTag.objects.filter(story=serializer.data.get("story"), tag=serializer.data.get("tag")).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OpnSesameViewSet(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            base_url = os.environ.get("OPNSESAME_API_URL", "")
            url = request.data.pop("url", "")
            method = request.data.pop("method", "")
            token = request.data.pop("token", None)

            if url == "auth/api-token-auth/":
                request.data["username"] = os.environ.get("OPNSESAME_USERNAME")
                request.data["password"] = os.environ.get("OPNSESAME_PASSWORD")

            headers = {
                'Content-Type': 'application/json; charset=UTF-8',
                'Accept': 'application/json'
            }
            if token:
                headers["Authorization"] = f"Token {token}"

            logger.info(f"## URL => {base_url}{url}")
            response = requests.request(method, f"{base_url}{url}", headers=headers, json=request.data)

            logger.info(f"## Response Body => {response.request.body}")
            return Response({"data": response.json(), "status_code": response.status_code},
                            status=status.HTTP_200_OK)

        except Exception as err:
            logger.error(f"## Error in OpnSesameViewSet => {err}")

            return Response({"error": True, "message": SOMETHING_WENT_WRONG},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StoryDetailView(View):

    def get(self, request, **kwargs):
        story_obj = get_object_or_404(Story, pk=kwargs.get('id'), is_trashed=False)
        images = story_obj.get_image()

        return render(request, 'story-detail.html', context={
            'title': story_obj.title,
            'id': story_obj.id,
            'lede': story_obj.lede,
            'image': images[0] if images else "",
            'body': story_obj.body,
            'type': 'story',
            'url': f'https://dev.adifect.com/company-projects/{story_obj.id}',
            'site_name': 'Adifect'
        })


class CreativeCodeImportAPIView(APIView):

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            return Response({"error": "true",
                             "message": "CSV file is missing"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            if not csv_file.name.lower().endswith('csv'):
                return Response({"error": "true",
                                 "message": "Uploaded file is not a valid CSV file"},
                                status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response({"error": "true",
                             "message": "Uploaded file is not a valid CSV file"},
                            status=status.HTTP_400_BAD_REQUEST)

        creative_code_objs_list = []
        creative_code_necessary_data_list = ['title', 'file_name', 'format', 'creative_theme', 'horizontal_pixel',
                                             'vertical_pixel', 'duration', 'link', 'notes']
        missing_row_data = {}
        reader_flag = False
        for row in reader:
            reader_flag = True
            for data in creative_code_necessary_data_list:
                if row.get(data) is None:
                    missing_row_data[data] = ["This field is required!"]
            if missing_row_data:
                    raise ValidationError(missing_row_data)
            creative_code_objs = CreativeCode(title=row.get('title'), file_name=row.get('file_name'),
                                              format=row.get('format'),
                                              creative_theme=row.get('creative_theme'),
                                              horizontal_pixel=row.get('horizontal_pixel'),
                                              vertical_pixel=row.get('vertical_pixel'),
                                              duration=row.get('duration'), link=row.get('link'),
                                              notes=row.get('notes'))
            creative_code_objs_list.append(creative_code_objs)

        if not reader_flag:
            for data in creative_code_necessary_data_list:
                missing_row_data[data] = ["This field is required!"]
            raise ValidationError(missing_row_data)
        CreativeCode.objects.bulk_create(creative_code_objs_list)
        return Response({'data': "", 'message': CREATIVE_CODE_DATA_IMPORTED_SUCCESSFULLY})


class CommunityAudienceListCreateView(generics.ListAPIView):
    """
    View for view list of all audiences
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    serializer_class = CommunityAudienceListCreateSerializer
    queryset = Audience.objects.filter(is_trashed=False).exclude(row_count=0).order_by('-id')
    pagination_class = CustomPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['audience_id', 'name']
    ordering_fields = ['id', 'name', 'audience_id', 'opted_out', 'row_count', 'community__name']
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        API to get list of audiences
        """
        self.queryset = self.filter_queryset(self.get_queryset())

        if community_id := request.GET.get('community'):
            self.queryset = self.queryset.filter(community_id=community_id)

        if ordering := request.GET.get('ordering', None):
            main_queryset = self.queryset.filter(
                id__in=self.queryset.order_by('community', 'audience_id').distinct(
                        'community', 'audience_id').values_list('id', flat=True)
            ).order_by(ordering)
        else:
            main_queryset = self.queryset.filter(
                id__in=self.queryset.order_by('community', 'audience_id').distinct(
                        'community', 'audience_id').values_list('id', flat=True)
            )

        # self.queryset = self.queryset.filter().order_by('community', 'audience_id'
        #                                                 ).distinct('community', 'audience_id')

        if not request.GET.get("page", None):
            serializer = self.get_serializer(main_queryset, many=True)
            return Response({'data': serializer.data, 'message': AUDIENCE_RETRIEVED_SUCCESSFULLY},
                            status=status.HTTP_200_OK)
        page = self.paginate_queryset(main_queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return Response({'data': response.data, 'message': AUDIENCE_RETRIEVED_SUCCESSFULLY})


class FacebookPostHandlerAPIView(APIView):
    """
    API to handle all the Facebook post on specified page.
    """

    permission_classes = [IsAuthenticated]

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    def post(self, request, *args, **kwargs):
        base_url = os.environ.get("FACEBOOK_API_URL", "")
        request_url = request.data.get("url", "")
        story_obj = get_object_or_404(Story, pk=kwargs.get('id'), is_trashed=False)
        url = base_url
        http_method = "GET"

        if not story_obj.story_url:
            raise serializers.ValidationError("No story_url found for this story.")
        if not request_url:
            raise serializers.ValidationError({"url": ["This field is required!"]})

        facebook_obj = CommunityChannel.objects.filter(
            community_setting=story_obj.community.community_setting_community.first(),
            channel__name__iexact='facebook').first()

        if request_url == "oauth/access_token":
            # Generate long-lived Token from short-lived token.

            short_token = request.data.get("token")
            url += "oauth/access_token"
            params = {"grant_type": "fb_exchange_token",
                      "client_id": facebook_obj.meta_data.get("app_id", ""),
                      "client_secret": facebook_obj.meta_data.get("app_secret_key", ""),
                      "fb_exchange_token": short_token}

        elif request_url == "me/accounts":
            # Get all pages from user facebook account.

            fb_access_token = facebook_obj.meta_data.get("fb_access_token", "")
            url += "me/accounts"
            params = {"fields": "name,access_token", "access_token": fb_access_token}

        elif request_url == "feed":
            # Get all pages from user facebook account.
            # Map the page name with id and page access token and pass in params in next API.

            fb_access_token = facebook_obj.meta_data.get("fb_access_token", "")
            params = {"fields": "name,access_token", "access_token": fb_access_token}
            page_resp = requests.request(http_method, f"{base_url}me/accounts", params=params)

            if page_resp.status_code == 200:
                page_access = None
                page_id = None
                for page in page_resp.json().get("data", []):
                    if page.get("name") == request.data.get("page_name", ""):
                        page_access = page.get("access_token")
                        page_id = page.get("id")

                params = {"link": story_obj.story_url, "access_token": page_access, "message": ""}
                url += f"{page_id}/feed"
            http_method = "POST"

        else:
            raise serializers.ValidationError({"url": ["Invalid Url."]})

        resp = requests.request(http_method, url, params=params)
        if resp.status_code == 200 and "oauth" in url:
            # If the response is success then store the long-lived access token into the DB.

            facebook_obj.meta_data["fb_access_token"] = resp.json().get("access_token")
            facebook_obj.save(update_fields=["meta_data"])

        if resp.status_code == 200:
            response_data = {"data": resp.json()}
        else:
            response_data = {"message": resp.json().get("error", {}).get("message"), "error": True}

        return Response(response_data, status=resp.status_code)


class TwitterPostHandlerAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    def post(self, request, *args, **kwargs):

        story_obj = get_object_or_404(Story, pk=kwargs.get('id'), is_trashed=False)
        if not story_obj.story_url:
            raise serializers.ValidationError("No story url found for this story!")
        twitter_obj = CommunityChannel.objects.filter(
            community_setting=story_obj.community.community_setting_community.first(),
            channel__name__iexact='twitter').first()
        if not twitter_obj:
            raise serializers.ValidationError("Twitter credentials not provided!")

        consumer_key = twitter_obj.meta_data.get('consumer_key')
        consumer_secret = twitter_obj.meta_data.get('consumer_secret')
        access_token = twitter_obj.meta_data.get('access_token')
        access_token_secret = twitter_obj.meta_data.get('access_token_secret')

        oauth = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
        )
        response = oauth.post(
            os.environ.get("TWITTER_POST_API_URL", ""),
            json={
                "text": story_obj.story_url
            },
        )

        if response.status_code != 201:
            response_data = {"error": True,
                             "message": response.json().get("detail", "") or response.json().get("title", "")}
        else:
            response_data = {"message": "Tweet posted successfully!"}

        return Response(data=response_data, status=response.status_code)


class LinkedInPostHandlerAPIView(APIView):
    permission_classes = [LinkedInRequirePostPermission]

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    def get(self, request, *args, **kwargs):
        story_obj = get_object_or_404(Story, pk=request.query_params.get('state'), is_trashed=False)
        base_url = os.environ.get('LINKEDIN_API_URL')

        linkedin_obj = CommunityChannel.objects.filter(
            community_setting=story_obj.community.community_setting_community.first(),
            channel__name__iexact='linkedin').first()

        code = request.query_params.get('code')
        access_token_url = f"{base_url}oauth/v2/accessToken"

        absolute_url = request.build_absolute_uri()

        base_redirect_url = absolute_url.split('?')[0]
        params = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": base_redirect_url,
            "client_id": linkedin_obj.meta_data.get('client_id'),
            "client_secret": linkedin_obj.meta_data.get('client_secret'),
        }

        response = requests.request('Post', access_token_url, params=params)
        if response.status_code == 200:
            access_token = response.json().get("access_token")
        else:
            response_data = {"message": response.json(), "error": True}
            return Response(data=response_data, status=response.status_code)

        profile_url = f"{base_url}v2/me"
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.request('Get', profile_url, headers=headers)
        if response.status_code == 200:
            user_id = response.json().get("id")
        else:
            response_data = {"message": response.json(), "error": True}
            return Response(data=response_data, status=response.status_code)

        linkedin_obj.meta_data["access_token"] = access_token
        linkedin_obj.meta_data["user_id"] = user_id
        linkedin_obj.save(update_fields=["meta_data"])

        return Response(data={}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):

        story_obj = get_object_or_404(Story, pk=request.data.get('story_id'), is_trashed=False)
        if not story_obj.story_url:
            raise serializers.ValidationError("No story url found for this story!")

        base_url = os.environ.get('LINKEDIN_API_URL')

        linkedin_obj = CommunityChannel.objects.filter(
            community_setting=story_obj.community.community_setting_community.first(),
            channel__name__iexact='linkedin').first()
        if not linkedin_obj:
            raise serializers.ValidationError("LinkedIn credentials not provided!")

        access_token = linkedin_obj.meta_data.get('access_token')
        user_id = linkedin_obj.meta_data.get('user_id')

        post_url = f"{base_url}v2/ugcPosts"

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0',
        }

        data = {
            "author": f"urn:li:person:{user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": ""
                    },
                    "shareMediaCategory": "ARTICLE",
                    "media": [
                        {
                            "status": "READY",
                            "originalUrl": story_obj.story_url
                        }
                    ]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        response = requests.post(post_url, json=data, headers=headers)

        if response.status_code != 201:
            response_data = {"error": True,
                             "message": response.json()}
        else:
            response_data = {"data": {}, "message": "Content shared successfully on LinkedIn!"}

        return Response(data=response_data, status=response.status_code)