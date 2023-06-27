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
from rest_framework import generics, status
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
    CreativeCode, StoryTag, Audience
from community.permissions import IsAuthorizedForListCreate
from community.serializers import StorySerializer, CommunityTagsSerializer, \
    TagCreateSerializer, CommunitySettingsSerializer, ChannelListCreateSerializer, \
    ChannelRetrieveUpdateDestroySerializer, CommunityChannelSerializer, ProgramSerializer, CopyCodeSerializer, \
    CreativeCodeSerializer, AddStoryTagsSerializer, StoryTagSerializer, TagSerializer, \
    CommunityAudienceListCreateSerializer
from .tasks import story_data_entry, add_community_audiences
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
        story_data_entry.delay(community_setting_obj.community.community_id)
        opn_sesame_obj = CommunityChannel.objects.filter(community_setting=community_setting_obj,
                                                         channel__name__iexact='opnsesame').first()
        if opn_sesame_obj and validate_client_id_opnsesame(client_id=opn_sesame_obj.url,
                                                           api_key=opn_sesame_obj.api_key):
            # Call Background task for fetching audiences
            logger.info("VALID CLIENT_ID")
            logger.info("Calling background task to add audiences.")
            add_community_audiences.delay(opn_sesame_obj.url, opn_sesame_obj.api_key,
                                          community_setting_obj.community_id)

        return Response({'data': '', 'message': COMMUNITY_SETTINGS_SUCCESS}, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        story_data_entry.delay(instance.community.community_id, instance.community.community_id,
                               instance_community_delete=True)
        Audience.objects.filter(community_id=instance.community.id).update(is_trashed=True)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        community_id = instance.community.community_id
        old_opn_obj = CommunityChannel.objects.filter(community_setting=instance,
                                                      channel__name__iexact='opnsesame').first()
        old_opn_url = old_opn_obj.url
        old_opn_api_key = old_opn_obj.api_key
        old_community_id = instance.community.id

        with transaction.atomic():
            CommunityChannel.objects.filter(community_setting=instance).delete()
            serializer = CommunitySettingsSerializer(instance=instance, data=request.data,
                                                     context={"channel": request.data.get("channel"),
                                                              "id": kwargs.get('id')})
            serializer.is_valid(raise_exception=True)
            community_setting_obj = serializer.save()
            new_opn_obj = CommunityChannel.objects.filter(community_setting=community_setting_obj,
                                                          channel__name__iexact='opnsesame').first()
            story_data_entry.delay(community_setting_obj.community.community_id, community_id)

            if old_community_id != community_setting_obj.community.id or old_opn_url \
                    != new_opn_obj.url or old_opn_api_key != new_opn_obj.api_key:
                Audience.objects.filter(community_id=old_community_id).update(is_trashed=True)

                if new_opn_obj and validate_client_id_opnsesame(client_id=new_opn_obj.url,
                                                                api_key=new_opn_obj.api_key):
                    # Call Background task for fetching audiences
                    logger.info("VALID CLIENT_ID")
                    logger.info("Calling background task to add audiences.")
                    add_community_audiences.delay(new_opn_obj.url, new_opn_obj.api_key,
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
    queryset = Audience.objects.filter(is_trashed=False).order_by('-id')
    pagination_class = CustomPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['audience_id', 'name']
    ordering_fields = ['id', 'name', 'audience_id']
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        API to get list of audiences
        """
        self.queryset = self.filter_queryset(self.get_queryset())

        if community_id := request.GET.get('community'):
            self.queryset = self.queryset.filter(community_id=community_id)

        if not request.GET.get("page", None):
            serializer = self.get_serializer(self.queryset, many=True)
            return Response({'data': serializer.data, 'message': AUDIENCE_RETRIEVED_SUCCESSFULLY},
                            status=status.HTTP_200_OK)
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return Response({'data': response.data, 'message': AUDIENCE_RETRIEVED_SUCCESSFULLY})
