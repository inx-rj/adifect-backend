from django.shortcuts import render
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import permission_classes
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated

from administrator.models import JobApplied, JobActivity, Job, MemberApprovals
from administrator.pagination import FiveRecordsPagination
from administrator.serializers import JobAppliedSerializer, JobActivitySerializer, JobsWithAttachmentsSerializer
from rest_framework.response import Response
from rest_framework import status

from agency.models import Workflow_Stages, InviteMember
from agency.serializers import InviteMemberSerializer


# Create your views here.
class MemberApprovedJobViewSet(viewsets.ModelViewSet):
    serializer_class = JobAppliedSerializer
    queryset = JobApplied.objects.filter(is_trashed=False)
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def list(self, request, *args, **kwargs):
        queryset = JobApplied.objects.filter(job__workflow__stage_workflow__approvals__user__user=request.user)
        job_count = queryset.count()
        job_review = queryset.filter(status=3).count()
        job_progress = queryset.filter(status=2).count()
        job_completed = queryset.filter(status=4).count()
        serializer = self.serializer_class(queryset, many=True, context={request: request})
        context = {
            'Total_Job_count': job_count,
            'In_progress_jobs': job_progress,
            'In_review': job_review,
            'completed_jobs': job_completed,
            'data': serializer.data,
        }
        return Response(context, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
class JobActivityMemberViewSet(viewsets.ModelViewSet):
    serializer_class = JobActivitySerializer
    queryset = JobActivity.objects.all()
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['job', 'user', 'job__user']
    # search_fields = ['=status', ]
    # pagination_class = FiveRecordsPagination
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)


class MemberJobListViewSet(viewsets.ModelViewSet):
    serializer_class = JobsWithAttachmentsSerializer
    queryset = Workflow_Stages.objects.all()
    pagination_class = FiveRecordsPagination

    def list(self, request, *args, **kwargs):
        user = request.user
        workflow_id = self.queryset.filter(approvals__user__user=user, workflow__is_trashed=False,
                                           workflow__isnull=False, is_trashed=False).values_list('workflow_id',
                                                                                                 flat=True)
        job_data = Job.objects.filter(workflow_id__in=list(workflow_id)).order_by('-modified')
        paginated_data = self.paginate_queryset(job_data)
        serializer = self.serializer_class(paginated_data, many=True, context={'request': request})
        return self.get_paginated_response(data=serializer.data)
        # return Response(data=serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        if pk:
            job_data = Job.objects.filter(id=pk).first()
            serializer = self.serializer_class(job_data, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'details': 'No Job Found'}, status=status.HTTP_404_NOT_FOUND)


class MemberApprovalJobListViewSet(viewsets.ModelViewSet):
    serializer_class = JobsWithAttachmentsSerializer
    queryset = MemberApprovals.objects.all()
    pagination_class = FiveRecordsPagination

    def list(self, request, *args, **kwargs):
        job_id = self.filter_queryset(self.get_queryset()).filter(approver__user__user=request.user,
                                                                  status=0).values_list('job_work__job_applied__job_id',
                                                                                        flat=True)
        job_data = Job.objects.filter(id__in=list(job_id)).order_by('-modified')
        paginated_data = self.paginate_queryset(job_data)
        serializer = self.serializer_class(paginated_data, many=True, context={'request': request})
        return self.get_paginated_response(data=serializer.data)
        # return Response(data=serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        if pk:
            job_data = Job.objects.filter(id=pk).first()
            serializer = self.serializer_class(job_data, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'details': 'No Job Found'}, status=status.HTTP_404_NOT_FOUND)

class InviteUserCompanyListViewSet(viewsets.ModelViewSet):
    serializer_class = InviteMemberSerializer
    queryset = InviteMember.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).filter(user__user=request.user)
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)