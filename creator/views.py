from django.shortcuts import render
from rest_framework.response import Response
from administrator.models import Job, JobAttachments, JobApplied, JobActivity, SubmitJobWork, JobTasks, JobActivityAttachments, JobWorkActivityAttachments , JobAppliedAttachments
from administrator.serializers import JobSerializer, JobsWithAttachmentsSerializer, JobAppliedSerializer, \
    JobActivitySerializer, SubmitJobWorkSerializer, JobTasksSerializer, JobAttachmentsSerializer, JobActivityAttachmentsSerializer, JobWorkActivityAttachmentsSerializer, JobAppliedAttachmentsSerializer

from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .serializers import PublicJobViewSerializer
from agency.serializers import MyProjectSerializer
from administrator.pagination import FiveRecordsPagination
from authentication.manager import IsAdmin, IsAgency, IsCreator
from django.db.models import Count
import datetime as dt
from django.db.models import Q
from rest_framework.decorators import action

@permission_classes([IsAuthenticated])
class LatestsJobsViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    queryset = Job.objects.filter(is_trashed=False, is_blocked=False)

    def list(self, request, *args, **kwargs):
        job_data = self.queryset.filter(user=request.user.id)
        serializer = JobsWithAttachmentsSerializer(job_data, many=True)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


@permission_classes([IsAuthenticated])
class JobAppliedViewSet(viewsets.ModelViewSet):
    serializer_class = JobAppliedSerializer
    queryset = JobApplied.objects.filter(is_trashed=False)
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['job']

    def list(self, request, *args, **kwargs):
        job_data = self.filter_queryset(self.get_queryset()).filter(user=request.user)
        data = job_data.values('id')
        if data:
            data = data[0]
        return Response(data=data, status=status.HTTP_201_CREATED)


# @permission_classes([IsAuthenticated])
class CreatorJobsViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    queryset = Job.objects.filter(is_trashed=False, is_blocked=False)



    def retrieve(self, request, pk=None):
        id = pk
        if id is not None:
            job_data = self.queryset.get(id=id)
            serializer = JobsWithAttachmentsSerializer(job_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    

    def create(self, request, *args, **kwargs):
        # ------ create not allowed ----#

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

        # ------ end ---------#
        '''
        serializer = self.get_serializer(data=request.data)
        image = request.FILES.getlist('image')
        if serializer.is_valid():
            serializer.fields.pop('image')
            self.perform_create(serializer)
            job_id = Job.objects.latest('id')
            for i in image:
                JobAttachments.objects.create(job=job_id, job_images=i)
            context = {
                'message': 'Job Created Successfully',
                'status': status.HTTP_201_CREATED,
                'errors': serializer.errors,
                'data': serializer.data,
            }
            return Response(context)
        else:
            return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        '''

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        image = request.FILES.getlist('image')

        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            if image:
                serializer.fields.pop('image')
                for i in JobAttachments.objects.filter(job_id=instance.id, is_trashed=False):
                    i.delete()
                for i in image:
                    JobAttachments.objects.create(job_id=instance.id, job_images=i)

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
        for i in JobAttachments.objects.filter(job_id=instance.id, is_trashed=False):
            i.delete()
        self.perform_destroy(instance)

        context = {
            'message': 'Deleted Succesfully',
            'status': status.HTTP_204_NO_CONTENT,
            'errors': False,
        }
        return Response(context)


@permission_classes([IsAuthenticated])
class MyJobsViewSet(viewsets.ModelViewSet):
    # serializer_class = JobAppliedSerializer
    queryset = JobApplied.objects.filter(is_trashed=False, job__is_trashed=False).exclude(status=1).exclude(job=None)
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['modified', 'job__job_due_date', 'job__created', 'job__modified', 'created']
    ordering = ['job__job_due_date', 'job__created', 'job__modified', 'modified', 'created']
    filterset_fields = ['status', 'job__company']
    search_fields = ['=status', ]
    pagination_class = FiveRecordsPagination
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        user = request.user
        queryset = self.filter_queryset(self.get_queryset())
        job_applied_data = queryset.filter(user=user).values_list('job_id', flat=True)
        latest_job = Job.objects.filter(id__in=list(job_applied_data))
        latest_job = sorted(latest_job, key=lambda i: list(job_applied_data).index(i.pk))
        paginated_data = self.paginate_queryset(latest_job)
        serializer = JobsWithAttachmentsSerializer(paginated_data, many=True, context={'request': request})
        return self.get_paginated_response(data=serializer.data)


class PublicJobViewApi(viewsets.ModelViewSet):
    serializer_class = PublicJobViewSerializer
    queryset = Job.objects.filter(is_trashed=False, is_blocked=False)
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['id']
    ordering_fields = ['created', 'modified']
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.serializer_class(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


@permission_classes([IsAgency])
class MyProjectAllJob(APIView):

    def get(self, request, *args, **kwargs):
        queryset = JobApplied.objects.filter(is_trashed=False, user=request.user).exclude(status=1)
        job_list = []
        applied = queryset.filter(status=0).first()
        if applied is not None:
            job_list.append(applied.id)
        hired = queryset.filter(status=2).first()
        if hired is not None:
            job_list.append(hired.id)
        in_review = queryset.filter(status=3).f, is_blocked = Falseirst()
        if in_review is not None:
            job_list.append(in_review.id)
        complete = queryset.filter(status=4).first()
        if complete is not None:
            job_list.append(complete.id)
        if job_list:
            latest_job = JobApplied.objects.filter(id__in=list(job_list))
            serializer = MyProjectSerializer(latest_job, many=True, context={'request': request})
            return Response(data=serializer.data)
        return Response(data={'message': 'no data found'}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
class AvailableJobs(viewsets.ModelViewSet):
    queryset = Job.objects.filter(is_blocked=False).exclude(status=0).exclude(is_active=0)
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['created', 'modified']
    ordering = ['created', 'modified']
    filterset_fields = ['status']
    search_fields = ['=status', ]
    pagination_class = FiveRecordsPagination
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).filter(is_active=1)
        applied_data = JobApplied.objects.filter(user=request.user, is_trashed=False).values_list('job_id',
                                                                                                  flat=True)
        jobs = queryset.exclude(id__in=list(applied_data)).order_by('-modified')
        paginated_data = self.paginate_queryset(jobs.filter(job_due_date__gte=dt.datetime.today()))
        serializer = JobsWithAttachmentsSerializer(paginated_data, many=True, context={'request': request})
        return self.get_paginated_response(data=serializer.data)

    def retrieve(self, request, pk=None):
        id = pk
        if id is not None:
            if JobApplied.objects.filter(Q(user=request.user) & Q(job=id)).exists():
                job_data = Job.objects.filter(id=id).first()
                if job_data:
                    serializer = JobsWithAttachmentsSerializer(job_data, context={'request': request})
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response({'message': 'No Data Found', 'error': True}, status=status.HTTP_204_NO_CONTENT)
            else:
                job_data = Job.objects.filter(id=id, is_active=1).first()
                if job_data:
                    serializer = JobsWithAttachmentsSerializer(job_data, context={'request': request})
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response({'message': 'No Data Found', 'error': True}, status=status.HTTP_204_NO_CONTENT)


@permission_classes([IsAuthenticated])
class CreatorCompanyList(APIView):
    def get(self, request, *args, **kwargs):
        job_applied = JobApplied.objects.filter(user=request.user).exclude(status=1).values_list('job_id',
                                                                                                 flat=True)
        jobs = Job.objects.filter(id__in=list(job_applied), company__is_trashed=False, is_blocked=False).values(
            'company', 'company__name').annotate(company_count=Count('company')).filter(company_count__gte=1)
        context = {
            'message': 'company list',
            'status': status.HTTP_200_OK,
            'error': False,
            'data': jobs
        }
        return Response(context)


@permission_classes([IsAuthenticated])
class JobActivityCreaterViewSet(viewsets.ModelViewSet):
    serializer_class = JobActivitySerializer
    queryset = JobActivity.objects.all()
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['job']

    # search_fields = ['=status', ]
    # pagination_class = FiveRecordsPagination
    # http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).filter(Q(user=request.user) | Q(user__isnull=True))
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)


@permission_classes([IsAuthenticated])
class GetRejectedWork(APIView):
    queryset = SubmitJobWork.objects.all()
    serializer_class = SubmitJobWorkSerializer

    def post(self, request, *args, **kwargs):
        job = request.data.get('job', None)
        user = request.data.get('user', None)
        if job and user:
            get_rejected = self.queryset.filter(job_applied__job__id=job, job_applied__user_id=user, status=2)
            get_rejected_data = self.serializer_class(get_rejected, many=True, context={'request': request})
            context = {
                'message': 'Please Edit Your Request',
                'status': status.HTTP_200_OK,
                'error': False,
                'data': get_rejected_data.data
            }
            return Response(context, status=status.HTTP_200_OK)
        else:
            context = {
                'message': 'Job Or User Not Found',
                'status': status.HTTP_400_BAD_REQUEST,
                'error': True
            }
            return Response(context, status=status.HTTP_400_BAD_REQUEST)

@permission_classes([IsAuthenticated])
class GetTaskList(APIView):
    queryset = SubmitJobWork.objects.all()

    def post(self, request, *args, **kwargs):
        job = request.data.get('job', None)
        user = request.data.get('user', None)
        if job and user:
            get_task = self.queryset.filter(job_applied__job__id=job, job_applied__user_id=user,task__isnull=False).exclude(status=2).values('task__title','task')
            context = {
                'message': 'Success',
                'Data':get_task,
                'status': status.HTTP_200_OK,
                'error': True
            }
            return Response(context, status=status.HTTP_200_OK)
        else:
            context = {
                'message': 'Job Or User Not Found',
                'status': status.HTTP_400_BAD_REQUEST,
                'error': True
            }
            return Response(context, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
class CreatorJobsCountViewSet(viewsets.ModelViewSet):
    serializer_class = JobAppliedSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    pagination_class = FiveRecordsPagination
    queryset = JobApplied.objects.filter(is_trashed=False)

    def list(self, request, *args, **kwargs):
        job_data = self.filter_queryset(self.get_queryset()).filter(user=request.user,
                                                                    user__is_account_closed=False).order_by("-modified")
        job_count = job_data.count()
        in_review = job_data.filter(status=2)
        in_review_count = in_review.count()
        context = {
            'Total_Job_count': job_count,
            'In_progress_jobs': in_review_count,
        }
        return Response(context)

@permission_classes([IsAuthenticated])
class JobAttachmentsView(APIView):

    def get(self, request, *args, **kwargs):
        job = request.GET.get('job', None)

        job_attachments = JobAttachments.objects.filter(job=job)
        job_attachments_data = JobAttachmentsSerializer(job_attachments, many=True, context={'request': request})
        job_activity = JobActivityAttachments.objects.filter(job_activity_chat__job_activity__job=job,
                                                             job_activity_chat__job_activity__user=request.user)
        job_activity_attachments = JobActivityAttachmentsSerializer(job_activity, many=True,
                                                                    context={'request': request})
        job_work_approved = JobWorkActivityAttachments.objects.filter(work_activity__work_activity="approved",work_activity__job_activity_chat__job=job,
                                                             work_activity__job_activity_chat__user=request.user)
        job_work_approved_attachments = JobWorkActivityAttachmentsSerializer(job_work_approved, many=True, context={'request': request})
        job_work_rejected = JobWorkActivityAttachments.objects.filter(work_activity__work_activity="rejected",work_activity__job_activity_chat__job=job,
                                                             work_activity__job_activity_chat__user=request.user)
        job_work_rejected_attachments = JobWorkActivityAttachmentsSerializer(job_work_rejected, many=True, context={'request': request})
        job_applied = JobAppliedAttachments.objects.filter(job_applied__job=job, job_applied__user=request.user)
        job_applied_attachments = JobAppliedAttachmentsSerializer(job_applied, many=True, context={'request': request})

        context = {
            'job_attachments': job_attachments_data.data,
            'job_activity_attachments': job_activity_attachments.data,
            'approved_job_work_attachments': job_work_approved_attachments.data,
            'rejected_job_work_attachments': job_work_rejected_attachments.data,
            'job_applied_attachments': job_applied_attachments.data
        }
        return Response(context, status=status.HTTP_200_OK)