from locale import DAY_1
from sqlite3 import DatabaseError
from django.shortcuts import render
from .serializers import EditProfileSerializer, CategorySerializer, JobSerializer, JobAttachmentsSerializer, \
    JobAppliedSerializer, LevelSerializer, JobsWithAttachmentsSerializer, SkillsSerializer, \
    JobFilterSerializer, JobHiredSerializer, ActivitiesSerializer, RelatedJobsSerializer, \
    JobAppliedAttachmentsSerializer, UserListSerializer, PreferredLanguageSerializer, JobTasksSerializer, \
    JobTemplateSerializer, JobTemplateWithAttachmentsSerializer, JobTemplateAttachmentsSerializer
from authentication.models import CustomUser, CustomUserPortfolio
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import viewsets
from .models import Category, Job, JobAttachments, JobApplied, Level, Skills, JobHired, Activities, \
    JobAppliedAttachments, ActivityAttachments, PreferredLanguage, JobTasks, JobTemplate, JobTemplateAttachments
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import Http404, JsonResponse
from .pagination import FiveRecordsPagination
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
import operator
from functools import reduce
import os
from django.core.exceptions import ValidationError
from authentication.serializers import UserSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
import json
from agency.models import Industry, Company, WorksFlow, Workflow_Stages
from agency.serializers import IndustrySerializer, CompanySerializer, WorksFlowSerializer, StageSerializer

# Create your views here.

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def validate_attachment(attachments):
    error = 0
    for i in attachments:
        ext = os.path.splitext(i.name)[1]
        valid_extensions = ['.jpg', '.jpeg', '.png', '.doc', '.docx', '.mp4', '.pdf', '.xlsx', '.csv']
        if not ext.lower() in valid_extensions:
            error += 1
    return error


@permission_classes([IsAuthenticated])
class ProfileEdit(APIView):
    serializer_class = EditProfileSerializer

    def get(self, request, *args, **kwargs):
        queryset = CustomUser.objects.filter(email=self.request.user.email, is_trashed=False)
        serlizer = EditProfileSerializer(queryset, many=True)
        return Response(serlizer.data)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_data = serializer.validated_data
        user = CustomUser.objects.get(id=request.user.id, is_trashed=False)
        try:
            profile_image = request.FILES["profile_img"]
        except:
            profile_image = None
        user.profile_title = request.data.get('profile_title')
        user.profile_description = request.data.get('profile_description')
        user.profile_status = request.data.get('profile_status', None)
        user.first_name = request.data.get('first_name', None)
        user.last_name = request.data.get('last_name', None)
        video = request.data.get('video', None)
        user.preferred_communication_mode = request.data.get('preferred_communication_mode', None)
        user.preferred_communication_id = request.data.get('preferred_communication_id', None)
        portfolio = request.FILES.getlist('portfolio')
        remove_profile_img = request.data.get('remove_image', None)
        remove_profile_video = request.data.get('remove_video', None)
        remove_portfolio_ids = request.data.getlist('remove_portfolio', None)
        if profile_image:
            profile_error = validate_profile_image_video(profile_image, 'img')
            if profile_error != 0:
                return Response({'message': "Invalid profile images"}, status=status.HTTP_400_BAD_REQUEST)
            user.profile_img = profile_image
        if remove_profile_img:
            user.profile_img = None
        if video:
            video_error = validate_profile_image_video(video, 'video')
            if video_error != 0:
                return Response({'message': "Invalid video format"}, status=status.HTTP_400_BAD_REQUEST)
            user.video = video
        if remove_profile_video:
            user.video = None
        if remove_portfolio_ids:
            for id in remove_portfolio_ids:
                CustomUserPortfolio.objects.filter(id=id).delete()
        if portfolio:
            portfolio_error = validate_portfolio_images(portfolio)
            if portfolio_error != 0:
                return Response({'message': "Invalid portfolio images"}, status=status.HTTP_400_BAD_REQUEST)
            for img in portfolio:
                CustomUserPortfolio.objects.create(user_id=request.user.id, portfolio_images=img)
        user.save()
        user_data = CustomUser.objects.get(id=request.user.id)
        queryset = EditProfileSerializer(user_data, many=False)
        new_data = queryset.data
        new_data.update({'name': user_data.username})
        new_data.update({'user_id': user_data.id})
        token = get_tokens_for_user(user_data)
        context = {
            'message': 'Profile Updated Successfully',
            'user': new_data,
            'token': token['access'],
            'refresh': token['refresh']
        }
        response = Response(context, status=status.HTTP_200_OK)
        return response


def validate_portfolio_images(images):
    error = 0
    for img in images:
        ext = os.path.splitext(img.name)[1]
        valid_extensions = ['.jpg', '.jpeg', '.png']
        if not ext.lower() in valid_extensions:
            error += 1
    return error


def validate_profile_image_video(images, type):
    error = 0
    if images and type == 'img':
        ext = os.path.splitext(images.name)[1]
        valid_extensions = ['.jpg', '.jpeg', '.png']
        if not ext.lower() in valid_extensions:
            error += 1
    if images and type == 'video':
        ext = os.path.splitext(images.name)[1]
        valid_extensions = ['.mp4']
        if not ext.lower() in valid_extensions:
            error += 1
    return error


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.filter(is_trashed=False).order_by('-modified')


#
# class IndustryViewSet(viewsets.ModelViewSet):
#     serializer_class = IndustrySerializer
#     queryset = Industry.objects.filter(is_trashed=False).order_by('-modified')


class LevelViewSet(viewsets.ModelViewSet):
    serializer_class = LevelSerializer
    queryset = Level.objects.filter(is_trashed=False).order_by('-modified')


class SkillsViewSet(viewsets.ModelViewSet):
    serializer_class = SkillsSerializer
    queryset = Skills.objects.filter(is_trashed=False).order_by('-modified')


class UserListViewSet(viewsets.ModelViewSet):
    serializer_class = UserListSerializer
    queryset = CustomUser.objects.all()


@permission_classes([IsAuthenticated])
class JobViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    queryset = Job.objects.all()
    job_template_attach = JobTemplateAttachmentsSerializer
    pagination_class = FiveRecordsPagination

    def list(self, request, *args, **kwargs):
        job_data = self.queryset.exclude(status=0).order_by('-modified')
        paginated_data = self.paginate_queryset(job_data)
        serializer = JobsWithAttachmentsSerializer(paginated_data, many=True, context={'request': request})
        return self.get_paginated_response(data=serializer.data)

    def retrieve(self, request, pk=None):
        id = pk
        if id is not None:
            job_data = Job.objects.get(id=id)
            serializer = JobsWithAttachmentsSerializer(job_data, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        image = request.FILES.getlist('image')
        sample_image = request.FILES.getlist('sample_image')
        if serializer.is_valid():
            template_name = serializer.validated_data.get('template_name',None)
            if template_name:
                if Job.objects.filter(template_name=template_name, is_trashed=False).exclude(template_name=None).exists():
                    context = {
                        'message': 'Job Template Already Exist',
                        'status': status.HTTP_400_BAD_REQUEST,
                        'errors': serializer.errors,
                        'data': serializer.data,
                    }
                    return Response(context)
            '''
            if serializer.validated_data.get('status', None) == 0:
                if self.queryset.filter(user=request.user, status=0).exists():
                    context = {
                        'message': 'Draft Already Exist',
                        'status': status.HTTP_400_BAD_REQUEST,
                        'errors': serializer.errors,
                        'data': serializer.data,
                    }
                    return Response(context)
            '''

            serializer.fields.pop('image')
            serializer.fields.pop('sample_image')
            self.perform_create(serializer)
            job_id = Job.objects.latest('id')
            if image:
                image_error = validate_job_attachments(image)
                if image_error != 0:
                    return Response({'message': "Invalid Job Attachments images"}, status=status.HTTP_400_BAD_REQUEST)
                for i in image:
                    JobAttachments.objects.create(job=job_id, job_images=i)
            if sample_image:
                sample_image_error = validate_job_attachments(sample_image)
                if sample_image_error != 0:
                    return Response({'message': "Invalid Job Attachments images"},
                                    status=status.HTTP_400_BAD_REQUEST)
                for i in sample_image:
                    JobAttachments.objects.create(job=job_id, work_sample_images=i)

            if request.data.get("tasks", None):
                objs = []
                for i in json.loads(request.data['tasks']):
                    task_title = i['title']
                    if task_title:
                        objs.append(JobTasks(job=job_id, title=task_title, due_date=i['due_date']))
                task = JobTasks.objects.bulk_create(objs)

            if serializer.validated_data.get('status', None) == 1:
                second_serializer = JobTemplateSerializer(data=request.data)
                if second_serializer.is_valid():
                    self.perform_create(second_serializer)
                    Job_template_id = JobTemplate.objects.latest('id')
                    if image:
                        image_error = validate_job_attachments(image)
                        if image_error != 0:
                            return Response({'message': "Invalid Job Attachments images"},
                                            status=status.HTTP_400_BAD_REQUEST)
                        for i in image:
                            JobTemplateAttachments.objects.create(job_template=Job_template_id, job_template_images=i)
                    if sample_image:
                        sample_image_error = validate_job_attachments(sample_image)
                        if sample_image_error != 0:
                            return Response({'message': "Invalid Job Attachments images"},
                                            status=status.HTTP_400_BAD_REQUEST)
                        for i in sample_image:
                            JobTemplateAttachments.objects.create(job_template=Job_template_id, work_sample_images=i)

            context = {
                'message': 'Job Created Successfully',
                'status': status.HTTP_201_CREATED,
                'errors': serializer.errors,
                'data': serializer.data,
            }
            return Response(context)
        else:
            return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        image = request.FILES.getlist('image')
        sample_image = request.FILES.getlist('sample_image')
        remove_image_ids = request.data.getlist('remove_image', None)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            template_name = serializer.validated_data.get('template_name', None)
            if template_name:
                if Job.objects.filter(
                        ~Q(pk=instance.pk) & Q(template_name=template_name) & Q(is_trashed=False)).exclude(template_name=None).exists():
                    context = {
                        'message': 'Job Template Already Exist',
                        'status': status.HTTP_400_BAD_REQUEST,
                        'errors': serializer.errors,
                        'data': serializer.data,
                    }
                    return Response(context, status=status.HTTP_400_BAD_REQUEST)
            self.perform_update(serializer)
            if remove_image_ids:
                for id in remove_image_ids:
                    JobAttachments.objects.filter(id=id).delete()
            if image:
                image_error = validate_job_attachments(image)
                if image_error != 0:
                    return Response({'message': "Invalid Job Attachments images"}, status=status.HTTP_400_BAD_REQUEST)
                for i in image:
                    JobAttachments.objects.create(job=instance, job_images=i)
            if sample_image:
                sample_image_error = validate_job_attachments(sample_image)
                if sample_image_error != 0:
                    return Response({'message': "Invalid Job Attachments images"},
                                    status=status.HTTP_400_BAD_REQUEST)
                for i in sample_image:
                    JobAttachments.objects.create(job=instance, work_sample_images=i)

            # ------- task ----#
            if request.data.get('tasks', None):
                for i in json.loads(request.data['tasks']):
                    name = i['title']
                    if name:
                        if 'id' in i:
                            JobTasks.objects.filter(id=i['id']).update(title=i['title'],
                                                                       due_date=i['due_date'])
                        else:
                            JobTasks.objects.create(job=instance, title=name, due_date=i['due_date'])

            # ------ end -------------#

            # ---------------------- job template ------------------------------------#
            if serializer.validated_data.get('status', None) == 1:
                second_serializer = JobTemplateSerializer(data=request.data)
                if second_serializer.is_valid():
                    self.perform_create(second_serializer)
                    Job_template_id = JobTemplate.objects.latest('id')
                    if image:
                        image_error = validate_job_attachments(image)
                        if image_error != 0:
                            return Response({'message': "Invalid Job Attachments images"},
                                            status=status.HTTP_400_BAD_REQUEST)
                        for i in image:
                            JobTemplateAttachments.objects.create(job_template=Job_template_id, job_template_images=i)
                    if sample_image:
                        sample_image_error = validate_job_attachments(sample_image)
                        if sample_image_error != 0:
                            return Response({'message': "Invalid Job Attachments images"},
                                            status=status.HTTP_400_BAD_REQUEST)
                        for i in sample_image:
                            JobTemplateAttachments.objects.create(job_template=Job_template_id, work_sample_images=i)
            # --------------------- end -----------------------------------------------#

            context = {
                'message': 'Updated Successfully',
                'status': status.HTTP_200_OK,
                'errors': serializer.errors,
                'data': serializer.data,
            }
            return Response(context)
        else:
            return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        for i in JobAttachments.objects.filter(job_id=instance.id):
            i.delete()
        self.perform_destroy(instance)

        context = {
            'message': 'Deleted Succesfully',
            'status': status.HTTP_204_NO_CONTENT,
            'errors': False,
        }
        return Response(context)


def validate_job_attachments(images):
    error = 0
    for img in images:
        ext = os.path.splitext(img.name)[1]
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.svg']
        if not ext.lower() in valid_extensions:
            error += 1
    return error


class JobAppliedViewSet(viewsets.ModelViewSet):
    serializer_class = JobAppliedSerializer
    queryset = JobApplied.objects.filter(is_trashed=False)
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def list(self, request, *args, **kwargs):
        user = self.request.user
        job_applied_data = self.queryset.filter(user=user)
        serializer = self.serializer_class(job_applied_data, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        attachments = request.FILES.getlist('job_applied_attachments')
        data = request.data

        if serializer.is_valid():
            if self.queryset.filter(Q(job=data['job']) & Q(user=data['user'])).exists():
                context = {
                    'message': 'Job already applied',
                }
                return Response(context, status=status.HTTP_400_BAD_REQUEST)
            else:
                serializer.fields.pop('attachments')
                attachment_error = validate_attachment(attachments)
                if attachment_error != 0:
                    return Response({'message': "Invalid Attachment"}, status=status.HTTP_400_BAD_REQUEST)
                self.perform_create(serializer)
                job_applied_id = JobApplied.objects.latest('id')

                for i in attachments:
                    JobAppliedAttachments.objects.create(job_applied=job_applied_id, job_applied_attachments=i)
                context = {
                    'message': 'Job Applied Successfully',
                    'status': status.HTTP_201_CREATED,
                    'errors': serializer.errors,
                    'data': serializer.data,
                }

                return Response(context)
        else:
            return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ActivitiesViewSet(viewsets.ModelViewSet):
    serializer_class = ActivitiesSerializer
    queryset = Activities.objects.filter(is_trashed=False)
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def list(self, request, *args, **kwargs):
        activity_data = self.queryset.all()
        serializer = self.serializer_class(activity_data, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        attachments = request.FILES.getlist('activity_attachments')

        if serializer.is_valid():
            serializer.fields.pop('attachments')
            self.perform_create(serializer)
            activity_id = Activities.objects.latest('id')
            attachment_error = validate_attachment(attachments)
            if attachment_error != 0:
                return Response({'message': "Invalid Attachment"}, status=status.HTTP_400_BAD_REQUEST)
            for i in attachments:
                ActivityAttachments.objects.create(activities=activity_id, activity_attachments=i)
            context = {
                'message': 'Message Sent Successfully',
                'status': status.HTTP_201_CREATED,
                'errors': serializer.errors,
                'data': serializer.data,
            }

            return Response(context)
        else:
            return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class JobFilterApi(APIView):
    serializer_class = JobFilterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            request_data = serializer.validated_data
            price = request.data.get('price', None)
            skills = request.data.get('skills', None)
            tags = request.data.get('tags', None)
            jobs_filter_data = Job.objects.filter()
            if tags:
                q = tags.split(",")
                query = reduce(operator.or_, (Q(tags__icontains=item) for item in q))
                jobs_filter_data = jobs_filter_data.filter(
                    query
                )
            if skills:
                q = skills.split(",")
                query = reduce(operator.or_, (Q(skills__skill_name__icontains=item) for item in q))
                jobs_filter_data = jobs_filter_data.filter(
                    query
                )
            if price:
                jobs_filter_data = jobs_filter_data.filter(price=price
                                                           )
            job_data = JobsWithAttachmentsSerializer(jobs_filter_data, many=True, context={'request': request})
            if jobs_filter_data:
                message = 'Job Filter Data get Successfully'
            else:
                message = 'No Data Found'
            context = {
                'message': message,
                'status': status.HTTP_200_OK,
                'data': job_data.data,
            }
            return Response(context)
        else:
            return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
class LatestJobAPI(APIView):

    def get(self, request, *args, **kwargs):
        try:
            applied_data = JobApplied.objects.filter(user=request.user,is_trashed=False).values_list('job_id',flat=True)
            latest_job = Job.objects.exclude(id__in=list(applied_data))
            latest_job = latest_job.exclude(status=0).latest('id')
            data = JobsWithAttachmentsSerializer(latest_job, context={'request': request})
            context = {
                'message': 'Latest Job get Successfully',
                'status': status.HTTP_200_OK,
                'true': True,
                'data': data.data,
            }
            return Response(context)
        except Exception as e:
            print(e)
            context = {
                'false': False,
                'message': 'No jobs to show',
            }
            return Response(context)


# class CompanyViewSet(viewsets.ModelViewSet):
#     serializer_class = CompanySerializer
#     queryset = Company.objects.filter(is_trashed=False).order_by('-modified')


@permission_classes([IsAuthenticated])
class JobHiredViewSet(viewsets.ModelViewSet):
    serializer_class = JobHiredSerializer
    queryset = JobHired.objects.filter(is_trashed=False)
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status']
    search_fields = ['=status', ]


@permission_classes([IsAuthenticated])
class RelatedJobsAPI(APIView):

    def get(self, request, *args, **kwargs):
        if kwargs['company_id']:
            queryset = Job.objects.filter(user=request.user, company_id=kwargs['company_id'])
            if queryset:
                serializer = RelatedJobsSerializer(queryset, many=True)
                context = {
                    'message': 'Related Jobs',
                    'status': status.HTTP_200_OK,
                    'data': serializer.data,
                }
                return Response(context)

        context = {
            'message': 'No data found',
            'status': status.HTTP_200_OK,
            'data': [],
        }
        return Response(context)

    '''
    multiple search code
    def get(self, request, *args, **kwargs):
        if kwargs['title']:
            titles = kwargs['title'].split(' ')
            title_qs = reduce(operator.or_, (Q(title__icontains=x, is_trashed=False) for x in titles))
            queryset = Job.objects.filter(title_qs)
            if queryset:
                serializer = RelatedJobsSerializer(queryset, many=True)
                context = {
                    'message': 'Related Jobs',
                    'status': status.HTTP_200_OK,
                    'data': serializer.data,
                }
            else:
                context = {
                    'message': 'No data found',
                    'status': status.HTTP_200_OK,
                    'data': "",
                }
            return Response(context)
        else:
            context = {
                'message': 'No data found',
                'status': status.HTTP_200_OK,
                'data': "",
            }
        return Response(context)
        '''


@permission_classes([IsAuthenticated])
class PrefferedLanguageViewSet(viewsets.ModelViewSet):
    serializer_class = PreferredLanguageSerializer
    queryset = PreferredLanguage.objects.all()

    def create(self, request, *args, **kwargs):
        if not request.data:
            return Response("No data", status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            ln_code = serializer.validated_data['ln_code']
            if PreferredLanguage.objects.filter(user=user).exists():
                context = {
                    'message': 'Language Already Exist',
                    'status': status.HTTP_400_BAD_REQUEST,
                }
                return Response(context, status=status.HTTP_400_BAD_REQUEST)
            self.perform_create(serializer)
        context = {
            'message': 'Created Successfully',
            'status': status.HTTP_201_CREATED,
            'errors': serializer.errors,
            'data': serializer.data,
        }
        return Response(context)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
        context = {
            'message': 'Updated Succesfully',
            'status': status.HTTP_200_OK,
            'errors': serializer.errors,
            'data': serializer.data,
        }
        return Response(context)


@permission_classes([IsAuthenticated])
class JobTasksViewSet(viewsets.ModelViewSet):
    serializer_class = JobTasksSerializer
    queryset = JobTasks.objects.all()
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['job']
    search_fields = ['=job', ]


@permission_classes([IsAuthenticated])
class JobTemplatesViewSet(viewsets.ModelViewSet):
    serializer_class = JobTemplateSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    queryset = JobTemplate.objects.all()
    pagination_class = FiveRecordsPagination

    def list(self, request, *args, **kwargs):
        job_data = self.queryset.order_by('-modified')
        paginated_data = self.paginate_queryset(job_data)
        serializer = JobTemplateWithAttachmentsSerializer(paginated_data, many=True, context={'request': request})
        return self.get_paginated_response(data=serializer.data)

    def retrieve(self, request, pk=None):
        id = pk
        if id is not None:
            job_data = JobTemplate.objects.get(id=id)
            serializer = JobTemplateWithAttachmentsSerializer(job_data, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)


@permission_classes([IsAuthenticated])
class JobDraftViewSet(viewsets.ModelViewSet):
    serializer_class = JobsWithAttachmentsSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    queryset = Job.objects.filter(status=0)

    def list(self, request, *args, **kwargs):
        job_data = self.queryset.filter(user=request.user).first()
        serializer = JobsWithAttachmentsSerializer(job_data, many=False, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    queryset = Company.objects.filter(is_trashed=False).order_by('-modified')

class WorkflowViewSet(viewsets.ModelViewSet):
    serializer_class = WorksFlowSerializer
    queryset = WorksFlow.objects.filter(is_trashed=False).order_by('-modified')

class StagesViewSet(viewsets.ModelViewSet):
    serializer_class = StageSerializer
    queryset = Workflow_Stages.objects.filter(is_trashed=False).order_by('-modified')



# -------------------------------------------- for testing purpose ----------------------------------------------------#


class TestApi(APIView):
    def get(self, request):
        from django.db import connection, reset_queries
        devices = JobApplied.objects.all()
        print(devices)
        print(connection.queries)
        reset_queries()
        device_second = JobApplied.objects.all().values('user_id', 'links')
        print(device_second)
        print(connection.queries)
        reset_queries()
        context = {
            'message': "Success",
            'status': status.HTTP_200_OK,
        }
        return Response(context)
# ---------------------------------------------------- end ------------------------------------------------ #
