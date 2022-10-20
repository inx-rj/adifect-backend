from django.shortcuts import render
from rest_framework.response import Response
from administrator.models import Job, JobAttachments, JobApplied
from administrator.serializers import JobSerializer, JobsWithAttachmentsSerializer, JobAppliedSerializer, \
    JobsWithAttachmentsSerializer
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter,OrderingFilter
from .serializers import PublicJobViewSerializer
from agency.serializers import MyProjectSerializer
from administrator.pagination import FiveRecordsPagination
from authentication.manager import IsAdmin,IsAgency,IsCreator
from django.db.models import Count
import datetime as dt



@permission_classes([IsAuthenticated])
class LatestsJobsViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    queryset = Job.objects.filter(is_trashed=False)

    def list(self, request, *args, **kwargs):
        job_data = self.queryset.filter(user=request.user.id)
        serializer = JobsWithAttachmentsSerializer(job_data, many=True)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


@permission_classes([IsAuthenticated])
class JobAppliedViewSet(viewsets.ModelViewSet):
    serializer_class = JobAppliedSerializer
    queryset = JobApplied.objects.filter(is_trashed=False)


# @permission_classes([IsAuthenticated])
class CreatorJobsViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    queryset = Job.objects.filter(is_trashed=False)

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
                for i in JobAttachments.objects.filter(job_id=instance.id,is_trashed=False):
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
        for i in JobAttachments.objects.filter(job_id=instance.id,is_trashed=False):
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
    queryset = JobApplied.objects.filter(is_trashed=False).exclude(status=1)
    filter_backends = [DjangoFilterBackend,OrderingFilter,SearchFilter]
    ordering_fields = ['modified','job__job_due_date','job__created','job__modified','created']
    ordering = ['job__job_due_date','job__created','job__modified','modified','created']
    filterset_fields = ['status','job__company']
    search_fields = ['=status',]
    pagination_class = FiveRecordsPagination
    http_method_names = ['get']


    def list(self, request, *args, **kwargs):
        user = request.user
        queryset = self.filter_queryset(self.get_queryset())
        job_applied_data = queryset.filter(user=user).values_list('job_id',flat=True)
        latest_job = Job.objects.filter(id__in=list(job_applied_data))
        latest_job = sorted(latest_job, key=lambda i: list(job_applied_data).index(i.pk))
        paginated_data = self.paginate_queryset(latest_job)
        serializer = JobsWithAttachmentsSerializer(paginated_data, many=True, context={'request': request})
        return self.get_paginated_response(data=serializer.data)


class PublicJobViewApi(viewsets.ModelViewSet):
    serializer_class = PublicJobViewSerializer
    queryset = Job.objects.filter(is_trashed=False)
    filter_backends = [DjangoFilterBackend,OrderingFilter,SearchFilter]
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
        queryset = JobApplied.objects.filter(is_trashed=False,user=request.user).exclude(status=1)
        job_list = []
        applied = queryset.filter(status=0).first()
        if applied is not None:
              job_list.append(applied.id)
        hired = queryset.filter(status=2).first()
        if hired is not None:
                job_list.append(hired.id)
        in_review = queryset.filter(status=3).first()
        if in_review is not None:
                job_list.append(in_review.id)
        complete = queryset.filter(status=4).first()
        if complete is not None:
                job_list.append(complete.id)
        if job_list:
            latest_job = JobApplied.objects.filter(id__in=list(job_list))
            serializer = MyProjectSerializer(latest_job, many=True, context={'request': request})
            return Response(data=serializer.data)
        return Response(data={'message':'no data found'},status=status.HTTP_400_BAD_REQUEST)




@permission_classes([IsAuthenticated])
class AvailableJobs(viewsets.ModelViewSet):
    queryset = Job.objects.exclude(status=0).exclude(is_active=0)
    filter_backends = [DjangoFilterBackend,OrderingFilter,SearchFilter]
    ordering_fields = ['created', 'modified']
    ordering = ['created','modified']
    filterset_fields = ['status']
    search_fields = ['=status', ]
    pagination_class = FiveRecordsPagination
    http_method_names = ['get']


    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        applied_data = JobApplied.objects.filter(user=request.user, is_trashed=False).values_list('job_id',
                                                                                                  flat=True)
        jobs = queryset.exclude(id__in=list(applied_data)).order_by('-modified')
        paginated_data = self.paginate_queryset(jobs.filter(job_due_date__gte=dt.datetime.today()))
        serializer = JobsWithAttachmentsSerializer(paginated_data, many=True, context={'request': request})
        return self.get_paginated_response(data=serializer.data)

@permission_classes([IsAuthenticated])
class CreatorCompanyList(APIView):
    def get(self, request, *args, **kwargs):
            job_applied = JobApplied.objects.filter(user=request.user).exclude(status=1).values_list('job_id',
                                                                                                  flat=True)
            jobs = Job.objects.filter(id__in=list(job_applied),company__is_trashed=False).values('company','company__name').annotate(company_count=Count('company')).filter(company_count__gte=1)
            context = {
                'message': 'company list',
                'status': status.HTTP_200_OK,
                'error': False,
                'data':jobs
            }
            return Response(context)
