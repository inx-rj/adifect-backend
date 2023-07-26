import os

from django.shortcuts import render
from rest_framework.response import Response
from administrator.models import Job, JobAttachments, JobApplied, MemberApprovals, JobActivity, JobActivityAttachments, \
    JobWorkActivityAttachments, JobAppliedAttachments, JobWorkAttachments, JobFeedback, JobTemplate
from administrator.serializers import JobSerializer, JobsWithAttachmentsSerializer, JobActivitySerializer, \
    JobAppliedSerializer, JobActivityAttachmentsSerializer, JobActivityChatSerializer, \
    JobWorkActivityAttachmentsSerializer, JobAppliedAttachmentsSerializer, JobAttachmentsSerializer, \
    JobWorkAttachmentsSerializer, JobFeedbackSerializer
from common.exceptions import custom_handle_exception
from common.pagination import CustomPagination
from community.constants import CHANNEL_RETRIEVED_SUCCESSFULLY
from community.models import Story
from community.permissions import IsAuthorizedForListCreate
from notification.models import Notifications
from notification.serializers import NotificationsSerializer
from rest_framework import status, serializers
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from authentication.models import CustomUser
from authentication.serializers import UserSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from administrator.pagination import FiveRecordsPagination
from django.db.models import Q
from django.db.models import Count, Avg
from rest_framework import generics
from rest_framework import filters

from .constants import AGENCY_INVITE_MEMBER_RETRIEVE_SUCCESSFULLY, AUDIENCE_CREATED_SUCCESSFULLY, \
    AUDIENCE_RETRIEVED_SUCCESSFULLY, AUDIENCE_UPDATED_SUCCESSFULLY, AGENCY_WORKFLOW_RETRIEVED_SUCCESSFULLY, \
    COMPANY_RETRIEVED_SUCCESSFULLY, INDUSTRY_RETRIEVED_SUCCESSFULLY
from .models import InviteMember, WorksFlow, Workflow_Stages, Industry, Company, DAM, DamMedia, AgencyLevel, TestModal, \
    Audience
from .serializers import InviteMemberSerializer, \
    InviteMemberRegisterSerializer, WorksFlowSerializer, StageSerializer, IndustrySerializer, CompanySerializer, \
    DAMSerializer, DamMediaSerializer, DamWithMediaSerializer, MyProjectSerializer, TestModalSerializer, \
    DamWithMediaRootSerializer, DamWithMediaThumbnailSerializer, DamMediaThumbnailSerializer, AgencyLevelSerializer, \
    DamMediaNewSerializer, AudienceListCreateSerializer, AudienceRetrieveUpdateDestroySerializer, \
    AudienceCommunityListSerializer
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from adifect.settings import SEND_GRID_API_key, FRONTEND_SITE_URL, LOGO_122_SERVER_PATH, BACKEND_SITE_URL, \
    TWILIO_NUMBER, TWILIO_NUMBER_WHATSAPP, SEND_GRID_FROM_EMAIL
from helper.helper import StringEncoder, send_text_message, send_skype_message, send_email, send_whatsapp_message
from django.db.models import Count
from django.db.models import Subquery
import base64
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import datetime as dt
from rest_framework.viewsets import ReadOnlyModelViewSet
from datetime import datetime
from django.utils import timezone


# Create your views here.
@permission_classes([IsAuthenticated])
class IndustryViewSet(viewsets.ModelViewSet):
    serializer_class = IndustrySerializer
    queryset = Industry.objects.all().order_by('-modified')
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['user']
    search_fields = ['industry_name', 'created']
    ordering_fields = ['industry_name', 'created', 'is_active']

    def list(self, request, *args, **kwargs):
        user = self.request.user
        queryset = self.filter_queryset(self.get_queryset()).filter(Q(user=None) | Q(user=user))
        if not request.GET.get("page", None):
            serializer = self.serializer_class(queryset, many=True, context={'request': request})
            return Response({'data': serializer.data, 'message': INDUSTRY_RETRIEVED_SUCCESSFULLY},
                            status=status.HTTP_200_OK)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True, context={'request': request})
            response = self.get_paginated_response(serializer.data)
            return Response({'data': response.data, 'message': INDUSTRY_RETRIEVED_SUCCESSFULLY},
                            status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    queryset = Company.objects.all().order_by('-modified')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'agency', 'is_blocked']
    search_fields = ['name', 'created', 'id']
    ordering_fields = ['name', 'created', 'agency__role', 'is_active']

    def get_queryset(self):
        user = self.request.user
        queryset = Company.objects.filter((Q(agency=user) & (Q(created_by=user) | (Q(created_by__isnull=True)))) | Q(invite_company_list__user__user=self.request.user),
                                          agency__is_account_closed=False).order_by('-modified').distinct()
        return queryset

    def list(self, request, *args, **kwargs):
        """
        API to get list of company
        """
        self.queryset = self.filter_queryset(self.get_queryset())
        if not request.GET.get("page", None):
            serializer = self.get_serializer(self.queryset, many=True)
            return Response({'data': serializer.data, 'message': COMPANY_RETRIEVED_SUCCESSFULLY},
                            status=status.HTTP_200_OK)
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return Response({'data': response.data, 'message': COMPANY_RETRIEVED_SUCCESSFULLY},
                            status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = serializer.validated_data.get('name', None)
        description = serializer.validated_data.get('description', None)
        is_active = serializer.validated_data.get('is_active', None)
        agency = serializer.validated_data.get('agency', None)
        created_by = serializer.validated_data.get('created_by', None)
        self.perform_create(serializer)

        user_company = Company.objects.filter(created_by=created_by)
        serializer = CompanySerializer(user_company, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        #   serializer.validated_data['is_active']
        if serializer.is_valid(raise_exception=True):
            if not instance.job_company.all():
                self.perform_update(serializer)
                context = {
                    'message': 'Updated Successfully...',
                    'status': status.HTTP_200_OK,
                    'errors': serializer.errors,
                    'data': serializer.data,
                }
                return Response(context, status=status.HTTP_200_OK)
            else:
                if instance.job_company.filter(is_active=True).exists():
                    if serializer.validated_data['is_active']:
                        context = {
                            'message': 'Updated Successfully........',
                            'status': status.HTTP_200_OK,
                        }
                        return Response(context, status=status.HTTP_200_OK)
                context = {
                    'message': 'This company is assigned to a Job, so the status cannot be Edited!',
                    'status': status.HTTP_400_BAD_REQUEST,
                    'errors': True,
                }
            return Response(context, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.serializer_class(instance)
        # if not data['is_assigned_workflow'].value:
        #     self.perform_destroy(instance)
        #     context = {
        #         'message': 'Deleted Succesfully',
        #         'status': status.HTTP_204_NO_CONTENT,
        #         'errors': False,
        #     }
        # else:
        #     context = {
        #         'message': 'This company is assigned to a workflow, so cannot be deleted!',
        #         'status': status.HTTP_400_BAD_REQUEST,
        #         'errors': True,
        #     }
        # return Response(context)
        instance = self.get_object()
        data = self.serializer_class(instance)
        if instance.job_company.filter(is_active=True).exists():
            context = {
                'message': 'This company is associated with an active job, so cannot be Edited!',
                'status': status.HTTP_400_BAD_REQUEST,
                'errors': True,
            }
        else:
            instance.is_active = False
            instance.save()
            context = {
                'message': 'Company Inactive successfully.',
                'status': status.HTTP_204_NO_CONTENT,
                'errors': False,
            }
        return Response(context)


@permission_classes([IsAuthenticated])
class AgencyJobsViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    queryset = Job.objects.filter(is_trashed=False, company__is_active=True).exclude(status=0)
    pagination_class = FiveRecordsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['company', 'is_active', 'job_applied__status']
    search_fields = ['company__name', 'title', 'description', 'tags', 'skills__skill_name']

    def list(self, request, *args, **kwargs):
        if request.GET.get('expire'):
            job_data = self.filter_queryset(self.get_queryset()).filter(Q(user=request.user) &
                                                                        Q(job_due_date__lt=dt.datetime.today()) &
                                                                        Q(user__is_account_closed=False)).exclude(
                Q(job_applied__status=2) | Q(job_applied__status=3) | Q(job_applied__status=4)).order_by(
                "-modified")

        elif request.GET.get('progress'):

            job_data = self.filter_queryset(self.get_queryset()).filter(
                Q(user=request.user) & Q(user__is_account_closed=False) & Q(
                    Q(job_applied__status=2) | Q(job_applied__status=3))).order_by(
                "-modified")


        elif request.GET.get('completed'):
            # job_data = self.filter_queryset(self.get_queryset()).filter(
            #     Q(user=request.user) & Q(user__is_account_closed=False) & Q(job_applied__status=4)).exclude(
            #     Q(job_applied__status=2) | Q(job_applied__status=3)).order_by(
            #     "-modified")

            job_data = self.filter_queryset(self.get_queryset()).filter(
                Q(user=request.user) & Q(user__is_account_closed=False) & Q(job_applied__status=4)).order_by(
                "-modified")


        else:
            job_data = self.filter_queryset(self.get_queryset()).filter(user=request.user,
                                                                        user__is_account_closed=False).order_by(
                "-modified")
        job_count = job_data.count()
        paginated_data = self.paginate_queryset(job_data)
        serializer = JobsWithAttachmentsSerializer(paginated_data, many=True, context={'request': request})
        job_id = job_data.values_list('id', flat=True)
        applied = JobApplied.objects.filter(job_id__in=list(job_id), job__is_trashed=False, status=2).order_by(
            'job_id').distinct('job_id').values_list('id', flat=True).count()
        Context = {
            'Total_Job_count': job_count,
            'In_progress_jobs': applied,
            'data': serializer.data,
        }
        return self.get_paginated_response(Context)

    def retrieve(self, request, pk=None):
        id = pk
        if id is not None:
            job_data = Job.objects.filter(id=id, user=request.user).first()
            if job_data:
                serializer = JobsWithAttachmentsSerializer(job_data, context={'request': request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response({'message': 'No Data Found', 'error': True}, status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        image = request.FILES.getlist('image')
        dam_images = request.FILES.getlist('dam_images')
        if serializer.is_valid():
            if dam_images:
                serializer.fields.pop('image')
                for i in dam_images:
                    if i.limit_usage > i.limit_used:
                        context = {
                            'message': 'Limit Exceeded',
                            'status': status.HTTP_400_BAD_REQUEST,
                            'errors': serializer.errors,
                        }
                        return Response(context)
                    else:
                        self.perform_create(serializer)
                        i.limit_usage += 1
                        job_id = Job.objects.latest('id')
                        JobAttachments.objects.create(job=job_id, job_images=i)
                        context = {
                            'message': 'Job Created Successfully',
                            'status': status.HTTP_201_CREATED,
                            'errors': serializer.errors,
                            'data': serializer.data,
                        }
                        return Response(context)

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
                for i in JobAttachments.objects.filter(job_id=instance.id):
                    i.delete()
                for i in image:
                    JobAttachments.objects.create(job_id=instance.id, job_images=i)

            context = {
                'message': 'Updated Successfully...',
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


@permission_classes([IsAuthenticated])
class GetAgencyUnappliedJobs(viewsets.ModelViewSet):
    def list(self, request, *args, **kwargs):
        unapplied_jobs = Job.objects.filter(user=request.user.id, status=0, is_trashed=False, company__is_active=True)
        unapplied_jobs_data = JobsWithAttachmentsSerializer(unapplied_jobs, many=True)
        context = {
            'message': 'pending jobs',
            'status': status.HTTP_200_OK,
            'data': unapplied_jobs_data.data,
        }
        return Response(context)


@permission_classes([IsAuthenticated])
class WorksFlowViewSet(viewsets.ModelViewSet):
    serializer_class = WorksFlowSerializer
    queryset = WorksFlow.objects.filter(is_trashed=False).order_by('-modified')
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['company', 'is_blocked']
    search_fields = ['company__name', 'name']
    ordering_fields = ['company__name', 'name', 'is_active']

    def list(self, request, *args, **kwargs):
        user = self.request.user
        queryset = self.filter_queryset(self.get_queryset()).filter(company__is_active=True)
        workflow_data = queryset.filter(agency=user, agency__is_account_closed=False)
        if not request.GET.get("page", None):
            serializer = self.get_serializer(workflow_data, many=True)
            return Response({'data': serializer.data, 'message': AGENCY_WORKFLOW_RETRIEVED_SUCCESSFULLY},
                            status=status.HTTP_200_OK)

        page = self.paginate_queryset(workflow_data)
        if page is not None:
            serializer = self.serializer_class(page, many=True, context={'request': request})
            response = self.get_paginated_response(serializer.data)
            return Response({'data': response.data, 'message': AGENCY_WORKFLOW_RETRIEVED_SUCCESSFULLY},
                            status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        data = request.data
        try:
            serializer = self.serializer_class(data=data)
            if serializer.is_valid():
                serializer.save()
                workflow_latest = WorksFlow.objects.latest('id')
                if request.data.get('stage', None):
                    for i in request.data['stage']:
                        name = i['stage_name']
                        if name:
                            stage = Workflow_Stages(name=name, is_approval=i['is_approval'],
                                                    is_observer=i['is_observer'], is_all_approval=i['is_all_approval'],
                                                    workflow=workflow_latest, order=i['order'],
                                                    approval_time=i['approval_time'], is_nudge=i['is_nudge'],
                                                    nudge_time=i['nudge_time'])
                            stage.save()
                            if i['approvals']:
                                approvals = i['approvals']
                                stage.approvals.add(*approvals)
                            if i['is_observer']:
                                observer = i['observer']
                                stage.observer.add(*observer)
                context = {
                    'message': "Workflow Created Successfully",
                    'status': status.HTTP_201_CREATED,
                    'errors': serializer.errors,
                    'data': serializer.data,
                }

                return Response(context)
            context = {
                'message': "Error!",
                'status': status.HTTP_400_BAD_REQUEST,
                'errors': serializer.errors,
                'data': [],
            }
            return Response(context)
        except Exception as e:
            print(e)
            context = {
                'message': "Something Went Wrong",
                'status': status.HTTP_400_BAD_REQUEST,
                'errors': "Error",
                'data': [],
            }
            return Response(context)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            if not Job.objects.filter(workflow=instance):
                serializer = WorksFlowSerializer(instance, data=request.data, partial=partial)
                if serializer.is_valid():
                    self.perform_update(serializer)
                    if request.data.get('stage', None):
                        for i in request.data['stage']:
                            name = i['stage_name']
                            if name:
                                if i['stage_id'] == '':
                                    new_stage = Workflow_Stages(name=name, is_approval=i['is_approval'],
                                                                is_observer=i['is_observer'],
                                                                workflow=instance, order=i['order'],
                                                                is_all_approval=i['is_all_approval'],
                                                                approval_time=i['approval_time'],
                                                                is_nudge=i['is_nudge'], nudge_time=i['nudge_time'])
                                    new_stage.save()
                                    if i['approvals']:
                                        approvals = i['approvals']
                                        new_stage.approvals.add(*approvals)
                                    if i['is_observer']:
                                        observer = i['observer']
                                        new_stage.observer.add(*observer)
                                else:
                                    stage = Workflow_Stages.objects.filter(pk=i['stage_id'], workflow=instance)
                                    if stage:
                                        update = stage.update(name=name, is_approval=i['is_approval'],
                                                              is_observer=i['is_observer'],
                                                              is_all_approval=i['is_all_approval'], order=i['order'],
                                                              approval_time=i['approval_time'], is_nudge=i['is_nudge'],
                                                              nudge_time=i['nudge_time'])
                                        stage = stage.first()
                                        if i['approvals']:
                                            approvals = i['approvals']
                                            stage.approvals.clear()
                                            stage.approvals.add(*approvals)
                                        else:
                                            stage.approvals.clear()
                                        if i['is_observer']:
                                            observer = i['observer']
                                            stage.observer.clear()
                                            stage.observer.add(*observer)
                                        else:
                                            stage.observer.clear()
                    context = {
                        'message': "Workflow Updated Successfully",
                        'status': status.HTTP_201_CREATED,
                        'errors': serializer.errors,
                        'data': serializer.data,
                    }
                    return Response(context)
                context = {
                    'message': "error",
                    'status': status.HTTP_400_BAD_REQUEST,
                    'errors': serializer.errors,
                    'data': serializer.data,
                }
                return Response(context)
            context = {
                'message': "This workflow is currently in use and cannot be edited",
                'status': status.HTTP_400_BAD_REQUEST,
                'errors': 'ERROR',
                'data': [],
            }
            return Response(context)
        except Exception as e:
            print(e)
            context = {
                'message': "Something Went Wrong",
                'status': status.HTTP_400_BAD_REQUEST,
                'errors': "Error",
                'data': [],
            }
            return Response(context)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        workflow_id = instance.id
        if instance.job_workflow.all():
            return Response({'message': 'workflow assign to job cannot delete.', 'status': status.HTTP_404_NOT_FOUND},
                            status=status.HTTP_400_BAD_REQUEST)
        self.perform_destroy(instance)
        if workflow_id:
            Workflow_Stages.objects.filter(workflow_id=workflow_id).delete()
        context = {
            'message': 'WorkFlow Deleted successfully',
            'status': status.HTTP_204_NO_CONTENT,
            'errors': False,
        }
        return Response(context)


@permission_classes([IsAuthenticated])
class InviteMemberViewSet(viewsets.ModelViewSet):
    serializer_class = InviteMemberSerializer
    queryset = InviteMember.objects.all().order_by('-modified')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    pagination_class = CustomPagination
    filterset_fields = ['company']
    search_fields = ['company__name', 'email', 'user__user__username']
    ordering_fields = ['company__name', 'email', 'user__user__username', 'user__levels']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).filter(agency=request.user, is_trashed=False,
                                                                    user__isnull=False,
                                                                    agency__is_account_closed=False,
                                                                    company__is_active=True,
                                                                    is_inactive=False).order_by(
            '-modified')
        if request.GET.get('company'):
            queryset = queryset.filter(company=request.GET.get('company'))

        if not request.GET.get("page", None):
            serializer = self.get_serializer(queryset, many=True)
            return Response({'data': serializer.data, 'message': AGENCY_INVITE_MEMBER_RETRIEVE_SUCCESSFULLY},
                            status=status.HTTP_200_OK)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return Response({'data': response.data, 'message': AGENCY_INVITE_MEMBER_RETRIEVE_SUCCESSFULLY},
                            status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data.get('email', None)
            exclusive = serializer.validated_data.get('exclusive', None)
            company = serializer.validated_data.get('company', None)
            levels = serializer.validated_data.get('levels', None)
            user = CustomUser.objects.filter(email=email, is_trashed=False).first()
            agency = CustomUser.objects.filter(pk=serializer.validated_data['agency'].id, is_trashed=False).first()
            if not agency:
                return Response({'message': 'Agency does not exists', 'error': True},
                                status=status.HTTP_400_BAD_REQUEST)

            if InviteMember.objects.filter(Q(company=company) & Q(is_inactive=False) & (Q(email=email) | Q(user__user__email=email))).exclude(
                    status=2):
                return Response({'message': 'The user is Already Invited.', 'error': True},
                                status=status.HTTP_400_BAD_REQUEST)
            if user:
                # if user.role == 2:
                #     return Response({'message': "You Can't Invite Agency Directly", 'error': True,
                #                      'status': status.HTTP_400_BAD_REQUEST},
                #                     status=status.HTTP_400_BAD_REQUEST)

                if user.is_exclusive:
                    return Response({'message': 'User Is Exculsive', 'error': True},
                                    status=status.HTTP_400_BAD_REQUEST)
            if exclusive:
                exclusive_decode = StringEncoder.encode(self, 1)
            else:
                exclusive_decode = StringEncoder.encode(self, 0)
            from_email = Email(SEND_GRID_FROM_EMAIL)
            to_email = To(email)
            invite = InviteMember.objects.filter(user__user__email=email, is_inactive=False, agency=agency, company=company).first()
            if not invite:
                invite = InviteMember.objects.filter(email=email, is_inactive=False, agency=agency, company=company).first()
            if not user:
                email_decode = StringEncoder.encode(self, email)
                if not invite:
                    agency_level = AgencyLevel.objects.create(levels=levels)
                    invite = InviteMember.objects.create(agency=agency, email=email, user=agency_level, status=0,
                                                         company=company)
                decodeId = StringEncoder.encode(self, invite.user.id)
                try:
                    invite_email_from = os.environ.get('INVITE_EMAIL_FROM')
                    subject = f"You're Invited to Join {invite.company.name} Team"
                    content = Content("text/html",
                                      f'<div style="background: rgba(36, 114, 252, 0.06) !important"><table style="font: Arial, sans-serif;border-collapse: collapse;width: 600px;margin: 0 auto;"width="600"cellpadding="0"cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 0"><div style="padding: 34px 44px;border-radius: 8px !important;background: #fff;border: 1px solid #dddddd5e;margin-bottom: 50px;margin-top: 50px;"><div class="email-logo"><img style="width: 165px"src="{LOGO_122_SERVER_PATH}"/></div><a href="#"></a><div class="welcome-text"style="padding-top: 80px"><h1 style="font: 24px">Hello,</h1></div><div class="welcome-paragraph"><div style="padding: 10px 0px;font-size: 16px;color: #384860;">You have been invited to join Adifect for <b>{invite.company.name}</b> as <b>{invite.user.get_levels_display()}.</b></div><div style="padding: 20px 0px;font-size: 16px;color: #384860;">Sincerely,<br />The Adifect Team</div></div><div style="padding-top: 40px"class="create-new-account"><a href="{FRONTEND_SITE_URL}/signup-invite/{decodeId}/{exclusive_decode}/{email_decode}"><button style="height: 56px;padding: 15px 44px;background: #2472fc;border-radius: 8px;border-style: none;color: white;font-size: 16px;">Create New Account</button></a></div><div style="padding: 50px 0px"class="email-bottom-para"><div style="padding: 20px 0px;font-size: 16px;color: #384860;">Don’t want any more emails from Adifect? <a href="#"><span style="text-decoration: underline">Unsubscribe.</span></a></div><div style="font-size: 16px; color: #384860">© 2022 Adifect</div></div></div></td></tr></tbody</table></div>')
                    data = send_email(invite_email_from, to_email, subject, content)
                    if data:
                        return Response({'message': 'mail Send successfully, Please check your mail'},
                                        status=status.HTTP_200_OK)
                    else:
                        return Response({'message': 'You are not authorized to send invitation.'},
                                        status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    print(e)
                    return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            if user:
                if not invite:
                    agency_level = AgencyLevel.objects.create(user=user, levels=levels)
                    invite = InviteMember.objects.create(user=agency_level, agency=agency, status=0, company=company)

                decodeId = StringEncoder.encode(self, invite.id)
                accept_invite_status = 1
                accept_invite_encode = StringEncoder.encode(self, accept_invite_status)
                reject_invite_status = 2
                reject_invite_encode = StringEncoder.encode(self, reject_invite_status)
                if user.preferred_communication_mode == '3':
                    to = user.preferred_communication_id
                    twilio_number = TWILIO_NUMBER
                    data = send_text_message(f'You have been invited to join Adifect by {agency.username}',
                                             twilio_number, to)
                    if data:
                        return Response({'message': 'message Send successfully, Please check your SMS'})
                    else:
                        return Response({'message': 'Something Went Wrong'}, status=status.HTTP_400_BAD_REQUEST)
                elif user.preferred_communication_mode == '2':
                    receiver = user.preferred_communication_id
                    data = send_skype_message(receiver, f'You have been invited to join Adifect by {agency.username}')
                    if data:
                        return Response({'message': 'message Send successfully, Please check your skype'})
                    return Response({'message': 'Something Went Wrong'})
                elif user.preferred_communication_mode == '1':
                    to = user.preferred_communication_id
                    twilio_number_whatsapp = TWILIO_NUMBER_WHATSAPP
                    data = send_whatsapp_message(twilio_number_whatsapp,
                                                 f'You have been invited to join Adifect by {agency.username}', to)
                    if data:
                        return Response({'message': 'message sent successfully,please check your whatsapp'})
                    else:
                        return Response({'message': 'Something went wrong'})
                elif user.preferred_communication_mode == '0':
                    try:
                        invite_email_from = os.environ.get('INVITE_EMAIL_FROM')
                        subject = f"You're Invited to Join {invite.company.name} Team"
                        content = Content("text/html",
                                          f'<div style="background: rgba(36, 114, 252, 0.06) !important"><table style="font: Arial, sans-serif;border-collapse: collapse;width: 600px;margin: 0 auto;"width="600" cellpadding="0" cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 0"><div style="padding: 34px 44px;border-radius: 8px !important;background: #fff;border: 1px solid #dddddd5e;margin-bottom: 50px;margin-top: 50px;"><div class="email-logo"><img style="width: 165px"src="{LOGO_122_SERVER_PATH}"/></div><a href="#"></a><div class="welcome-text" style="padding-top: 80px"><h1 style="font:24px;color: #000;">Hello, {user.first_name} {user.last_name}</h1></div><div class="welcome-paragraph"><div style="padding: 10px 0px;font-size: 16px;color: #384860;">You have been invited to join Adifect for <b>{invite.company.name}</b> as <b>{invite.user.get_levels_display()}.</b></div><div style="padding: 20px 0px;font-size: 16px; color: #384860;">Sincerely,<br />The Adifect Team</div></div><div style="display: flex"><div style="padding-top: 40px; width: 50%"class="create-new-account"><a href={FRONTEND_SITE_URL}/invite-accept/{decodeId}/{accept_invite_encode}/{exclusive_decode}><button style="height: 56px;cursor: pointer;padding: 15px 44px;background: #2472fc;border-radius: 8px;border-style: none;color: white;font-size: 16px;width: 90%;cursor: pointer;">Accept</button></a></div><div style="padding-top: 40px; width: 50%"class="create-new-account"><a href={FRONTEND_SITE_URL}/invite-accept/{decodeId}/{reject_invite_encode}/{exclusive_decode}><button style="height: 56px;padding: 15px 44px;background: #2472fc;border-radius: 8px;border-style: none;color: white;font-size: 16px;width: 90%;cursor: pointer;">Reject</button></a></div></div><div style="padding: 50px 0px"class="email-bottom-para"><div style="padding: 20px 0px;font-size: 16px;color: #384860;">Don’t want any more emails from Adifect? <a href="#"><span style="text-decoration: underline"> Unsubscribe.</span></a></div><div style="font-size: 16px; color: #384860">© 2022 Adifect </div></div></div></td></tr></tbody></table></div>')

                        data = send_email(invite_email_from, to_email, subject, content)
                        if data:
                            return Response({'message': 'mail Send successfully, Please check your mail'},
                                            status=status.HTTP_200_OK)
                        else:
                            return Response({'message': 'You are not authorized to send invitation.'},
                                            status=status.HTTP_400_BAD_REQUEST)

                    except Exception as e:
                        print(e)
                        return Response({'message': str(e)})
            return Response({'message': 'success'},
                            status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        print(instance.user.user.id)
        level = request.data.get('levels', None)
        new_observer = request.data.get('new_observer', None)
        assign_to = request.data.get('assigned_to', None)
        if level:
            is_update = AgencyLevel.objects.filter(id=instance.user.id).update(levels=int(level))
            if instance.user.levels == 1:
                if Workflow_Stages.objects.filter(observer=instance.user.id).exists():
                    for i in Workflow_Stages.objects.filter(observer__user__user_id=instance.user.user.id):
                        i.observer.remove(instance.user.user.id)
                        i.observer.add(int(new_observer))
                if assign_to:
                    job_assigned = Job.objects.filter(assigned_to=instance.user.user.id).update(
                        assigned_to=int(assign_to))
                    job_template_assigned = JobTemplate.objects.filter(assigned_to=instance.user.user.id).update(
                        assigned_to=int(assign_to))
                    Notifications.objects.create(user=instance.user.user, company=instance.company,
                                                 notification=f'You have been assigned {instance.user.user.get_full_name()}"s duties',
                                                 notification_type='invite_accepted', redirect_id=instance.id)
            if is_update:
                context = {
                    'message': 'Updated Successfully...',
                    'status': status.HTTP_200_OK,
                }
                return Response(context)
        else:
            return Response({'message': 'something went wrong', 'error': True}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['put'], detail=False, url_path='update_blocked/(?P<pk>[^/.]+)', url_name='update_blocked')
    def update_blocked(self, request, pk=None, *args, **kwargs):

        data = self.queryset.filter(id=pk).update(is_blocked=request.data['is_blocked'])
        if data:
            context = {
                'message': 'Updated Succesfully',
                'status': status.HTTP_200_OK,
            }
            return Response(context, status=status.HTTP_200_OK)
        else:
            return Response({'message:'}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):

        # instance = self.get_object()
        # agency_level = instance.user.id
        # user_id = None
        # if instance.user.user is not None:
        #     user_id = instance.user.user.id
        # levels = instance.user.levels
        # self.perform_destroy(instance)
        # agency_level = AgencyLevel.objects.filter(id=agency_level).delete()
        # if levels == 4:
        #     user = CustomUser.objects.filter(id=user_id).delete()
        # else:
        #     if not InviteMember.objects.filter(user__user=user_id) and user_id:
        #         CustomUser.objects.filter(id=user_id).delete()
        # context = {
        #     'message': 'Deleted Succesfully',
        #     'status': status.HTTP_204_NO_CONTENT,
        #     'errors': False,
        # }
        # return Response(context)

        instance = self.get_object()
        if not instance.user.user:
            InviteMember.objects.filter(id=instance.id).update(is_inactive=True)
        else:
            user_status = InviteMember.objects.filter(user__user=instance.user.user.id).update(is_inactive=True)
            if user_status:
                user = CustomUser.objects.filter(id=instance.user.user.id).update(is_inactive=True)

        context = {
            'message': 'Deleted Succesfully',
            'status': status.HTTP_204_NO_CONTENT,
            'errors': False,
        }
        return Response(context)


class UpdateInviteMemberStatus(APIView):

    def get(self, request, *args, **kwargs):
        data = {}
        id = kwargs.get('id', None)
        encoded_id = int(StringEncoder.decode(self, id))

        status = kwargs.get('status', None)
        encoded_status = int(StringEncoder.decode(self, status))
        exculsive = kwargs.get('exculsive', None)
        encoded_exculsive = int(StringEncoder.decode(self, exculsive))
        if InviteMember.objects.filter(pk=encoded_id, is_modified=True):
            return Response({'message': 'You are not Authorize.'})
        if id and status:
            data = InviteMember.objects.filter(pk=encoded_id, is_trashed=False)
            if data and exculsive:
                user = CustomUser.objects.filter(pk=data.first().user.id, is_trashed=False).update(
                    is_exclusive=encoded_exculsive)
            update = data.update(status=encoded_status, is_modified=True)
            if update:
                if encoded_status == 1:
                    data = {"message": "Thank you for your response, Invite Accepted.", "status": "success"}
                else:
                    data = {"message": "Thank you for your response, Invite Rejected", "status": "success"}
            else:
                data = {"data": "error", "status": "error"}
        return Response(data)


class SignUpViewInvite(APIView):
    serializer_class = InviteMemberRegisterSerializer

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = InviteMemberRegisterSerializer(data=data)
            if serializer.is_valid():

                if CustomUser.objects.filter(is_trashed=False, email=data['email']).exists():
                    context = {
                        'message': 'Email already exists'
                    }
                    return Response(context, status=status.HTTP_400_BAD_REQUEST)

                if CustomUser.objects.filter(is_trashed=False, username=data['username']).exists():
                    context = {
                        'message': 'Username already exists'
                    }
                    return Response(context, status=status.HTTP_400_BAD_REQUEST)

                if data['password'] != data['confirm_password']:
                    context = {
                        'message': 'Passwords do not match'
                    }
                    return Response(context, status=status.HTTP_400_BAD_REQUEST)

                exculsive = kwargs.get('exculsive', None)
                if exculsive:
                    exculsive = int(StringEncoder.decode(self, exculsive))
                else:
                    exculsive = False
                user = CustomUser.objects.create(
                    username=data['username'],
                    email=data['email'],
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    is_exclusive=exculsive,
                    email_verified=True,
                    role=3
                )

                user.set_password(data['password'])
                user.save()
                id = kwargs.get('invite_id', None)
                encoded_id = int(StringEncoder.decode(self, id))
                user_id = CustomUser.objects.latest('id')
                agency_level = AgencyLevel.objects.filter(pk=encoded_id, is_trashed=False).update(user=user)
                invite = InviteMember.objects.filter(user_id=encoded_id).first()
                invite.status = 1
                invite.save()
                user_email = data['email']
                user_username = data['username']
                agency_user = InviteMember.objects.filter(user__user__email=user_email).values("agency_id")
                Notifications.objects.create(user_id=agency_user[0]["agency_id"],
                                             notification=f'User {user_username} with email {user_email} has accepted your invitation for creator role',
                                             notification_type='invite_accepted', redirect_id=invite.id)
                # To get user id and update the invite table
                return Response({'message': 'User Registered Successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({'message': f'{e} is required'}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
class InviteMemberUserList(APIView):
    serializer_class = InviteMemberSerializer

    def get(self, request, *args, **kwargs):
        company_id = request.GET.get('company', None)
        level = request.GET.get('level', None)
        agency = request.user
        if level == '3':
            invited_user = InviteMember.objects.filter(is_blocked=False, status=1,
                                                       user__user__isnull=False, user__levels__in=[1,2,3])
        else:
            invited_user = InviteMember.objects.filter(is_blocked=False, status=1,
                                                       user__user__isnull=False)
        if company_id:
            invited_user = invited_user.filter(Q(company_id=company_id) | Q(user__user=agency))
        serializer = self.serializer_class(invited_user, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
class StageViewSet(viewsets.ModelViewSet):
    serializer_class = StageSerializer
    queryset = Workflow_Stages.objects.filter(is_trashed=False).order_by('order')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['workflow']
    search_fields = ['=workflow', ]

    @action(methods=['post'], detail=False, url_path='set_order/(?P<userId>[^/.]+)', url_name='set_order')
    def set_order(self, request, *args, **kwargs):
        try:
            order_list = request.data.get('order_list', None)
            if order_list:
                order_list = order_list.split(",")
                updated = False
                for index, id in enumerate(order_list):
                    updated = self.queryset.filter(pk=id).update(order=index)
                if updated:
                    return Response({"message": "Order Set Successfully", "error": False}, status=status.HTTP_200_OK)
                else:
                    return Response({"message": "Something Went Wrong", "error": True},
                                    status=status.HTTP_400_BAD_REQUEST)

            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'Error': str(e)})


def copy_media_logic(id, parent_id=None):
    if id:
        dam_old = DAM.objects.filter(pk=id).first()
        dam_old.pk = None
        dam_old.parent_id = parent_id
        dam_new = dam_old.save()
        new_id = None

        for j in DAM.objects.filter(parent=id, type=3):
            for i in DamMedia.objects.filter(dam=j):
                i.pk = None
                i.dam = dam_new
                i.save()
        for k in DAM.objects.filter(parent=id, type=2):
            for i in DamMedia.objects.filter(dam=k):
                i.pk = None
                i.dam = dam_new
                i.save()
        for l in DAM.objects.filter(parent=id, type=1):
            return copy_media_logic(l.id, dam_new.id)
        return True


@permission_classes([IsAuthenticated])
class DAMViewSet(viewsets.ModelViewSet):
    serializer_class = DAMSerializer
    queryset = DAM.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['id', 'parent', 'type', 'name', 'is_favourite', 'is_video', 'company']
    search_fields = ['name']

    def list(self, request, *args, **kwargs):
        parent = request.GET.get('parent', None)
        if parent:
            queryset = self.filter_queryset(self.get_queryset()).filter(agency=request.user)
        else:
            queryset = self.filter_queryset(self.get_queryset()).filter(
                Q(agency=request.user) & Q(parent=None) | Q(parent=False))
        serializer = DamWithMediaSerializer(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)

    def retrieve(self, request, pk=None):
        id = pk
        if id is not None:
            dam_data = self.queryset.get(id=pk)
            serializer = DamWithMediaSerializer(dam_data, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        dam_files = request.FILES.getlist('dam_files', None)
        dam_name = request.POST.getlist('dam_files_name', None)
        if serializer.is_valid():
            if serializer.validated_data['type'] == 3:
                for index, i in enumerate(dam_files):
                    # self.perform_create(serializer)
                    dam_id = DAM.objects.create(type=3, parent=serializer.validated_data.get('parent', None),
                                                agency=serializer.validated_data['agency'],
                                                company=serializer.validated_data.get('company', None))
                    DamMedia.objects.create(dam=dam_id, title=dam_name[index], media=i)
            # elif serializer.validated_data['type']==1:
            #     if request.data['parent'] is not None:
            #         if DAM.objects.filter(Q(name=request.data['name']) & Q(parent=request.data['parent'])):
            #             print("heloooooooooooooooooooooooooooooo")
            #             context = {
            #                 'message': 'Folder with this name already exist',
            #                 'status': status.HTTP_400_BAD_REQUEST,
            #                 'errors': serializer.errors,
            #             }
            #     elif request.data['parent'] is None:
            #          if DAM.objects.filter(name=request.data['name']):
            #             print("heloooooooooooooooooooooooooooooo")
            #             context = {
            #                 'message': 'Folder with this name already exist',
            #                 'status': status.HTTP_400_BAD_REQUEST,
            #                 'errors': serializer.errors,
            #             }
            #     else:
            #         self.perform_create(serializer)
            #         dam_id = DAM.objects.latest('id')
            #         for index,i in enumerate(dam_files):
            #             DamMedia.objects.create(dam=dam_id,title=dam_name[index],media=i)
            #         context = {
            #             'message': 'Media Uploaded Successfully',
            #             'status': status.HTTP_201_CREATED,
            #             'errors': serializer.errors,
            #             'data': serializer.data,
            #         }
            #         return Response(context)

            else:
                self.perform_create(serializer)
                dam_id = DAM.objects.latest('id')
                for index, i in enumerate(dam_files):
                    DamMedia.objects.create(dam=dam_id, title=dam_name[index], media=i)
            context = {
                'message': 'Media Uploaded Successfully',
                'status': status.HTTP_201_CREATED,
                'errors': serializer.errors,
                'data': serializer.data,
            }
            return Response(context)
        else:
            return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            context = {
                'message': 'Updated Successfully...',
                'status': status.HTTP_200_OK,
                'errors': serializer.errors,
                'data': serializer.data,
            }
            return Response(context)
        else:
            return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=False, url_path='selected_delete', url_name='selected_delete')
    def delete_multiple(self, request, *args, **kwargs):
        try:
            id_list = request.data.get('id_list', None)
            order_list = id_list.split(",")
            if order_list:
                for i in DamMedia.objects.filter(dam_id__in=order_list):
                    i.delete()
                DAM.objects.filter(id__in=order_list).delete()
                context = {
                    'message': 'Deleted Succesfully',
                    'status': status.HTTP_204_NO_CONTENT,
                    'errors': False,
                }
                return Response(context)
            context = {
                'message': 'Data Not Found',
                'status': status.HTTP_404_NOT_FOUND,
                'errors': True,
            }
            return Response(context, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @action(methods=['post'], detail=False, url_path='copy_to', url_name='copy_to')
    def copy_to(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid() and request.data.get('id'):
            id = request.data.get('id')
            type_id = serializer.validated_data.get('type')
            parent = serializer.validated_data.get('parent')
            type_new = int(request.data.get('type_new'))
            # --- image copy from one folder to another -----#
            if type_id == 3 and type_new == 3:
                dam_media_inital = DamMedia.objects.filter(id=request.data.get('id')).first()
                if dam_media_inital:
                    dam_intial = dam_media_inital.dam
                    dam_intial.pk = None
                    dam_intial.parent = parent
                    dam_intial.type = type_new
                    dam_intial.save()
                    dam_media_inital.pk = None
                    dam_media_inital.dam = dam_intial
                    dam_media_inital.save()
                    context = {
                        'message': 'Media Uploaded Successfully',
                        'status': status.HTTP_201_CREATED,
                        'errors': serializer.errors,
                        'data': serializer.data,
                    }

                else:
                    context = {
                        'error': 'DAM id not found.',
                        'errors': serializer.errors,
                    }

                return Response(context)
            # --- collection  copy from one  to collection or image copy into collection  -----#
            if (type_id == 2 and type_new == 2) or (type_id == 3 and type_new == 2):
                dam_media_inital = DamMedia.objects.filter(id=request.data.get('id')).first()
                dam_media_inital.pk = None
                dam_media_inital.dam = parent
                dam_media_inital.save()
                context = {
                    'message': 'Media Uploaded Successfully',
                    'status': status.HTTP_201_CREATED,
                    'errors': serializer.errors,
                    'data': serializer.data,
                }
                return Response(context)

            # ---------------- image copy from collection --------#
            if type_id == 2 and type_new == 3:
                dam_new = DAM.objects.create(type=3, parent=parent, agency=request.user)
                dam_media = DamMedia.objects.filter(id=id).first()
                dam_media.pk = None
                dam_media.dam = dam_new
                dam_media.save()
                context = {
                    'message': 'Media Uploaded Successfully',
                    'status': status.HTTP_201_CREATED,
                    'errors': serializer.errors,
                    'data': serializer.data,
                }
                return Response(context)
            return Response({'message': serializer.errors}, status=status.HTTP_200_OK)
        else:
            return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        for i in DamMedia.objects.filter(dam_id=instance.id):
            if instance.company:
                for j in instance.company.invite_company_list.filter(user__user__isnull=False):
                    members_notification = Notifications.objects.create(user=j.user.user, company=instance.company,
                                                                        notification=f'{instance.agency.get_full_name()} has deleted an asset',
                                                                        notification_type='asset_uploaded')
            agency_notification = Notifications.objects.create(user=instance.agency, company=instance.company,
                                                               notification=f'{instance.agency.get_full_name()} has deleted an asset',
                                                               notification_type='asset_uploaded')
            i.delete()
        self.perform_destroy(instance)
        context = {
            'message': 'Deleted Succesfully',
            'status': status.HTTP_204_NO_CONTENT,
            'errors': False,
        }
        return Response(context)

    @action(methods=['post'], detail=False, url_path='create_collection', url_name='create_collection')
    def create_collection(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(data=request.data, partial=partial)
        images = request.data.get('dam_images', None)
        data = images.split(",")
        dam_files = request.FILES.getlist('dam_files', None)
        dam_name = request.POST.getlist('dam_files_name', None)

        if serializer.is_valid():
            self.perform_create(serializer)
            dam_id = DAM.objects.latest('id')
            for i in data:
                dam_inital = DamMedia.objects.get(id=i)

                DamMedia.objects.create(dam=dam_id, media=dam_inital.media, title=dam_inital.title,
                                        description=dam_inital.description)
                dam_inital.delete()
                if dam_files:
                    for index, i in enumerate(dam_files):
                        DamMedia.objects.create(dam=dam_id, title=dam_name[index], media=i)

            context = {
                'message': 'Media Uploaded Successfully',
                'status': status.HTTP_201_CREATED,
                'errors': serializer.errors,
                'data': serializer.data,
            }

            return Response(context)
        else:
            return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['put'], detail=False, url_path='rename_folder/(?P<pk>[^/.]+)', url_name='rename_folder')
    def rename_folder(self, request, pk=None):
        new_title = request.data.get('new_title', None)
        dam_data = DamMedia.objects.filter(id=pk).update(title=new_title)
        return Response(dam_data.data, status=status.HTTP_200_OK)

    @action(methods=['put'], detail=False, url_path='move_to', url_name='move_to')
    def move_to(self, request, *args, **kwargs):
        try:
            id_list = request.data.get('id', None)
            if id_list:
                DAM.objects.filter(id__in=id_list).update(parent=request.data['parent'])
                context = {
                    'message': 'Updated successfully',
                    'status': status.HTTP_201_CREATED,
                    'errors': False,
                }
                return Response(context)
            context = {
                'message': 'Data Not Found',
                'status': status.HTTP_404_NOT_FOUND,
                'errors': True,
            }
            return Response(context, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND)


@permission_classes([IsAuthenticated])
class DamRootViewSet(viewsets.ModelViewSet):
    serializer_class = DAMSerializer
    queryset = DAM.objects.filter(Q(parent=None) | Q(parent=False))
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['id', 'parent', 'type']
    search_fields = ['name', "dam_media__title"]

    # http_method_names = ['get','put']

    def list(self, request, *args, **kwargs):
        user = request.user
        queryset = self.filter_queryset(self.get_queryset()).filter(
            Q(agency=request.user) & (Q(company__created_by=request.user) | Q(company__created_by__isnull=True)))
        serializer = DamWithMediaRootSerializer(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)


@permission_classes([IsAuthenticated])
class DamMediaViewSet(viewsets.ModelViewSet):
    serializer_class = DamMediaSerializer
    queryset = DamMedia.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['modified', 'created', 'limit_used']
    ordering = ['modified', 'created', 'limit_used']
    filterset_fields = ['dam_id', 'title', 'id', 'image_favourite', 'is_video', 'dam__parent']
    search_fields = ['dam__type', 'title', 'tags', 'skills__skill_name', 'dam__name']
    http_method_names = ['get', 'put', 'delete', 'post']

    def list(self, request, *args, **kwargs):
        dam__parent = request.GET.get('dam__parent', None)
        if dam__parent:
            queryset = self.filter_queryset(self.get_queryset()).filter(dam__agency=request.user.id).exclude(
                dam__type=2)
        else:
            queryset = self.filter_queryset(self.get_queryset()).filter(dam__agency=request.user.id,
                                                                        dam__parent=None).exclude(dam__type=2)
        serializer = DamMediaSerializer(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)

    @action(methods=['get'], detail=False, url_path='get_multiple', url_name='get_multiple')
    def get_multiple(self, request, *args, **kwargs):
        try:
            id_list = request.GET.get('id', None)
            order_list = id_list.split(",")
            if order_list:
                data = DamMedia.objects.filter(id__in=order_list)
                serializer_data = self.serializer_class(data, many=True, context={'request': request})
                return Response(serializer_data.data)
            context = {
                'message': 'Data Not Found',
                'status': status.HTTP_404_NOT_FOUND,
                'errors': True,
            }
            return Response(context, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @action(methods=['delete'], detail=False, url_path='delete_multiple', url_name='delete_multiple')
    def delele_multiple(self, request, *args, **kwargs):
        try:
            id_list = request.GET.get('id', None)
            order_list = id_list.split(",")
            if order_list:
                data = DamMedia.objects.filter(id__in=order_list).delete()
                if data:
                    context = {
                        'message': 'Deleted Successfully',
                        'status': status.HTTP_204_NO_CONTENT,
                        'errors': False,
                    }
                    return Response(context, status=status.HTTP_200_OK)
        except Exception as e:
            context = {
                'message': 'Something Went Wrong',
                'status': status.HTTP_400_BAD_REQUEST,
                'errors': True,
            }
            return Response(context, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)

        if serializer.is_valid():
            if request.data.get('company'):
                if request.data.get('company') == "0":
                    DAM.objects.filter(pk=request.data['dam']).update(company=None)
                    self.perform_update(serializer)
                else:
                    DAM.objects.filter(pk=request.data['dam']).update(company=request.data['company'])
                    self.perform_update(serializer)
            else:
                self.perform_update(serializer)
            context = {
                'message': 'Updated Successfully...',
                'status': status.HTTP_200_OK,
                'errors': serializer.errors,
                'data': serializer.data,
            }
            return Response(context)
        else:
            return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=False, url_path='update_collection', url_name='update_collection')
    def update_collection(self, request, *args, **kwargs):
        serializer = DamMediaNewSerializer(data=request.data)
        dam_files = request.FILES.getlist('dam_files', None)
        dam_id = request.data.get('dam_id', None)
        if serializer.is_valid():
            # Upload the images
            for i in dam_files:
                DamMedia.objects.create(dam_id=dam_id, media=i)

            context = {
                'message': 'Media Uploaded Successfully',
                'status': status.HTTP_201_CREATED,
                'errors': serializer.errors,
                'data': serializer.data,
            }

            return Response(context)
        else:
            return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], detail=False, url_path='latest_records', url_name='latest_records')
    def latest_records(self, request, *args, **kwargs):
        queryset = DamMedia.objects.filter(
            Q(dam__agency=request.user) & (
                        Q(dam__company__created_by=request.user) | Q(dam__company__created_by__isnull=True)) & (
                        Q(dam__parent__is_trashed=False) | Q(dam__parent__isnull=True))).order_by(
            '-created')[:4]
        serializer = DamMediaSerializer(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)

    @action(methods=['post'], detail=False, url_path='move_collection', url_name='move_collection')
    def move_collection(self, request, *args, **kwargs):
        data = request.POST.get('dam_images', None)
        dam_intial = 0
        for i in data.split(','):
            if not request.data.get('parent', None) == 'null':
                dam_id = DAM.objects.create(type=3, parent_id=request.data.get('parent', None),
                                            agency_id=request.data.get('user'))
                dam_media = DamMedia.objects.filter(pk=i).update(dam=dam_id)
                dam_intial += 1
            else:
                dam_id = DAM.objects.create(type=3, agency_id=request.data.get('user'))
                dam_media = DamMedia.objects.filter(pk=i).update(dam=dam_id)
                dam_intial += 1
            if dam_intial:
                context = {
                    'message': 'Media Uploaded Successfully',
                    'status': status.HTTP_201_CREATED,
                }
                return Response(context)
            return Response({"message": "Unable to move"}, status=status.HTTP_404_NOT_FOUND)


@permission_classes([IsAuthenticated])
class DamDuplicateViewSet(viewsets.ModelViewSet):
    serializer_class = DAMSerializer
    queryset = DAM.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['id', 'parent', 'type']
    search_fields = ['=name']
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        user = request.user
        if request.GET.get('root'):
            queryset = self.filter_queryset(self.get_queryset()).filter(agency=request.user, parent=None)
        else:
            queryset = self.filter_queryset(self.get_queryset()).filter(agency=request.user)
        serializer = DamWithMediaSerializer(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)


@permission_classes([IsAuthenticated])
class DraftJobViewSet(viewsets.ModelViewSet):
    serializer_class = JobsWithAttachmentsSerializer
    pagination_class = CustomPagination
    queryset = Job.objects.filter(status=0).order_by('-modified')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['company']
    search_fields = ['company__name', 'title']
    ordering_fields = ['company__name', 'title']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).filter(company__is_active=True)
        draft_data = queryset.filter(user=request.user)
        if not request.GET.get("page", None):
            serializer = self.serializer_class(draft_data, many=True, context={'request': request})
            return Response({'data': serializer.data, 'message': ''},
                            status=status.HTTP_200_OK)
        page = self.paginate_queryset(draft_data)
        if page is not None:
            serializer = self.serializer_class(page, many=True, context={'request': request})
            response = self.get_paginated_response(serializer.data)
            return Response({"data": response.data, 'message': ''}, status=status.HTTP_200_OK)


# --      --   --         --     --    my project --   --       --      --        -- #

@permission_classes([IsAuthenticated])
class MyProjectViewSet(viewsets.ModelViewSet):
    serializer_class = MyProjectSerializer
    queryset = JobApplied.objects.filter(job__is_trashed=False).exclude(job=None)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['job', 'status', 'job__company', 'job__is_active']
    ordering_fields = ['modified', 'job__job_due_date', 'job__created', 'job__modified', 'created']
    ordering = ['job__job_due_date', 'job__created', 'job__modified', 'modified', 'created']
    search_fields = ['status', 'job__tags', 'job__skills__skill_name', 'job__description', 'job__title']
    pagination_class = FiveRecordsPagination
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        user = request.user
        queryset = self.filter_queryset(self.get_queryset())
        ordering = request.GET.get('ordering', None)
        if ordering:
            filter_data = queryset.filter(
                pk__in=Subquery(
                    queryset.filter(job__user=user).order_by('job_id').distinct('job_id').values('pk')
                )).order_by(ordering)
        else:
            filter_data = queryset.filter(
                pk__in=Subquery(
                    queryset.filter(job__user=user).order_by('job_id').distinct('job_id').values('pk')
                ))
        if request.GET.get('job__is_active', None) == 'true':
            filter_data = filter_data.filter(job__is_active=True)
        paginated_data = self.paginate_queryset(filter_data)
        serializer = self.serializer_class(paginated_data, many=True, context={'request': request})
        return self.get_paginated_response(data=serializer.data)


@permission_classes([IsAuthenticated])
class TestModalViewSet(viewsets.ModelViewSet):
    serializer_class = TestModalSerializer
    queryset = TestModal.objects.all()


@permission_classes([IsAuthenticated])
class DamMediaFilterViewSet(viewsets.ModelViewSet):
    serializer_class = DamMediaSerializer
    queryset = DamMedia.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['modified', 'created', 'limit_used']
    ordering = ['modified', 'created']
    filterset_fields = ['dam_id', 'title', 'id']
    search_fields = ['title']

    @action(methods=['get'], detail=False, url_path='favourites', url_name='favourites')
    def favourites(self, request, pk=None, *args, **kwargs):
        id = request.GET.get('id', None)
        if id:
            fav_folder = DAM.objects.filter(type=1, agency=request.user, is_favourite=True, parent=id)
            fav_folder_data = DamWithMediaSerializer(fav_folder, many=True, context={'request': request})
            fav_collection = DamMedia.objects.filter(dam__parent=id, image_favourite=True, dam__agency=request.user)
            fav_collection_data = DamWithMediaSerializer(fav_collection, many=True, context={'request': request})
            fav_images = DAM.objects.filter(parent=id, type=3, agency=request.user, is_favourite=True)
            fav_images_data = DamWithMediaSerializer(fav_images, many=True, context={'request': request})
        else:
            fav_folder = DAM.objects.filter(type=1, agency=request.user, is_favourite=True)
            fav_folder_data = DamWithMediaSerializer(fav_folder, many=True, context={'request': request})
            fav_collection = DamMedia.objects.filter(dam__parent=id, image_favourite=True, dam__agency=request.user)
            fav_collection_data = DamWithMediaSerializer(fav_collection, many=True, context={'request': request})
            fav_images = DAM.objects.filter(type=3, agency=request.user, is_favourite=True, )
            fav_images_data = DamWithMediaSerializer(fav_images, many=True, context={'request': request})

        context = {
            'fav_folder': fav_folder_data.data,
            'fav_collection': fav_collection_data.data,
            'fav_images': fav_images_data.data
        }
        return Response(context, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='count', url_name='count')
    def count(self, request, *args, **kwargs):
        id = request.GET.get('id', None)
        company = request.GET.get('company', None)
        if id:
            fav_folder = DAM.objects.filter(Q(Q(agency=request.user) & (
                        Q(company__created_by=request.user) | Q(company__created_by__isnull=True))) & Q(
                is_favourite=True) & Q(parent=id,
                                       is_trashed=False)).count()
            fav_folder = DamMedia.objects.filter(Q(dam__agency=request.user) & (
                        (Q(dam__company__created_by=request.user)) | Q(dam__company__created_by__isnull=True)),
                                                 image_favourite=True, is_trashed=False).count()
            total_image = DamMedia.objects.filter(Q(dam__agency=request.user) & (
                        (Q(dam__company__created_by=request.user)) | Q(dam__company__created_by__isnull=True)),
                                                  dam__type=3, dam__parent=id,
                                                  is_trashed=False, is_video=False).count()
            total_video = DamMedia.objects.filter(Q(dam__agency=request.user) & (
                        (Q(dam__company__created_by=request.user)) | Q(dam__company__created_by__isnull=True)),
                                                  dam__type=3, dam__parent=id,
                                                  is_trashed=False, is_video=True).count()
            total_collection = DAM.objects.filter(
                Q(agency=request.user) & ((Q(company__created_by=request.user)) | Q(company__created_by__isnull=True)),
                type=2, parent=id, is_trashed=False).count()
            total_folder = DAM.objects.filter(
                Q(agency=request.user) & ((Q(company__created_by=request.user)) | Q(company__created_by__isnull=True)),
                type=1, parent=id, is_trashed=False).count()

        if id and company:
            order_list = company.split(",")
            fav_folder = DAM.objects.filter(
                Q(agency=request.user) & (Q(company__created_by=request.user) | Q(company__created_by__isnull=True)),
                is_favourite=True, company__in=order_list, parent=id,
                is_trashed=False).count()
            print(fav_folder)
            total_image = DamMedia.objects.filter(Q(dam__agency=request.user) & (
                        (Q(dam__company__created_by=request.user)) | Q(dam__company__created_by__isnull=True)),
                                                  dam__type=3, dam__company__in=order_list,
                                                  dam__parent=id,
                                                  is_trashed=False, is_video=False).count()
            total_video = DamMedia.objects.filter(Q(dam__agency=request.user) & (
                        (Q(dam__company__created_by=request.user)) | Q(dam__company__created_by__isnull=True)),
                                                  dam__type=3, dam__company__in=order_list,
                                                  dam__parent=id,
                                                  is_trashed=False, is_video=True).count()
            total_collection = DAM.objects.filter(
                Q(agency=request.user) & (Q(company__created_by=request.user) | Q(company__created_by__isnull=True)),
                type=2, company__in=order_list, parent=id,
                is_trashed=False).count()
            total_folder = DAM.objects.filter(
                Q(agency=request.user) & (Q(company__created_by=request.user) | Q(company__created_by__isnull=True)),
                type=1, company__in=order_list, parent=id, is_trashed=False).count()

        if company and not id:
            order_list = company.split(",")
            fav_folder = DAM.objects.filter(
                Q(agency=request.user) & (Q(company__created_by=request.user) | Q(company__created_by__isnull=True)),
                parent__isnull=True, is_favourite=True,
                company__in=order_list,
                is_trashed=False).count()
            total_image = DamMedia.objects.filter(Q(dam__agency=request.user) & (
                        (Q(dam__company__created_by=request.user)) | Q(dam__company__created_by__isnull=True)),
                                                  dam__type=3, dam__parent__isnull=True,
                                                  dam__company__in=order_list,
                                                  is_trashed=False, is_video=False).count()
            total_video = DamMedia.objects.filter(Q(dam__agency=request.user) & (
                        (Q(dam__company__created_by=request.user)) | Q(dam__company__created_by__isnull=True)),
                                                  dam__type=3, dam__parent__isnull=True,
                                                  dam__company__in=order_list,
                                                  is_trashed=False, is_video=True).count()
            total_collection = DAM.objects.filter(
                Q(agency=request.user) & (Q(company__created_by=request.user) | Q(company__created_by__isnull=True)),
                type=2, parent__isnull=True,
                company__in=order_list, is_trashed=False).count()
            total_folder = DAM.objects.filter(
                Q(agency=request.user) & (Q(company__created_by=request.user) | Q(company__created_by__isnull=True)),
                type=1, parent__isnull=True, company__in=order_list, is_trashed=False).count()

        if not id and not company:
            fav_folder = DAM.objects.filter(
                Q(agency=request.user) & (Q(company__created_by=request.user) | Q(company__created_by__isnull=True)),
                is_favourite=True, parent__isnull=True).count()
            # fav_folder2 = DamMedia.objects.filter(dam__agency=request.user, image_favourite=True,is_trashed=False).count()
            # print(fav_folder2,'aaaaaaaaaaaaaaaaaa')
            # fav_folder=int(fav_folder1)+int(fav_folder2)
            total_image = DamMedia.objects.filter(Q(dam__agency=request.user) & (
                        Q(dam__company__created_by=request.user) | Q(dam__company__created_by__isnull=True)),
                                                  dam__type=3, is_trashed=False,
                                                  is_video=False, dam__parent__isnull=True).count()
            total_collection = DAM.objects.filter(
                Q(agency=request.user) & (Q(company__created_by=request.user) | Q(company__created_by__isnull=True)),
                type=2, parent__isnull=True).count()
            total_video = DamMedia.objects.filter(Q(dam__agency=request.user) & (
                        Q(dam__company__created_by=request.user) | Q(dam__company__created_by__isnull=True)),
                                                  dam__type=3, is_trashed=False,
                                                  is_video=True, dam__parent__isnull=True).count()
            total_folder = DAM.objects.filter(
                Q(agency=request.user) & (Q(company__created_by=request.user) | Q(company__created_by__isnull=True)),
                type=1, parent__isnull=True).count()

        context = {'fav_folder': fav_folder,
                   'total_image': total_image,
                   'total_collection': total_collection,
                   'total_video': total_video,
                   'total_folder': total_folder,
                   'status': status.HTTP_201_CREATED,
                   }
        return Response(context)

    @action(methods=['get'], detail=False, url_path='collectioncount', url_name='collectioncount')
    def collectioncount(self, request, *args, **kwargs):
        id = request.GET.get('id', None)
        if id:
            total_image = DamMedia.objects.filter(dam__type=3, dam__agency=request.user, is_trashed=False,
                                                  is_video=False, dam=id).count()
            total_video = DamMedia.objects.filter(dam__type=3, dam__agency=request.user, is_trashed=False,
                                                  is_video=True, dam=id).count()

        context = {
            'total_image': total_image,
            'total_video': total_video,
            'status': status.HTTP_201_CREATED,
        }
        return Response(context)


@permission_classes([IsAuthenticated])
class JobActivityMemberViewSet(viewsets.ModelViewSet):
    serializer_class = JobActivitySerializer
    queryset = JobActivity.objects.all()
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['job', 'user', 'job__user']
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)


@permission_classes([IsAuthenticated])
class DAMFilter(viewsets.ModelViewSet):
    serializer_class = DAMSerializer
    queryset = DAM.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['created', 'dam_media__job_count']
    ordering = ['created', 'dam_media__job_count']
    filterset_fields = ['id', 'parent', 'type', 'name', 'is_video', 'is_favourite']
    search_fields = ['name']

    def get_queryset(self):
        is_parent = self.request.GET.get('parent', None)
        data = self.request.GET.get('ordering', None)
        queryset = self.queryset
        if not is_parent:
            queryset = queryset.filter(parent__isnull=True)
        if data == '-dam_media__job_count':
            return queryset.order_by('-dam_media__created')

        return queryset

    def list(self, request, *args, **kwargs):
        photos = request.GET.get('photos', None)
        videos = request.GET.get('videos', None)
        collections = request.GET.get('collections', None)
        folders = request.GET.get('folders', None)
        company = request.GET.get('company', None)
        order_list = None
        if company:
            order_list = company.split(",")
        photo = None
        video = None
        collection = None
        folder = None
        if photos:
            if company:
                data = self.filter_queryset(self.get_queryset()).filter(Q(agency=self.request.user) & (
                            Q(company__created_by=self.request.user) | Q(company__created_by__isnull=True)), type=3,
                                                                        is_video=False, company__in=order_list,
                                                                        is_trashed=False)
                photos_data = DamWithMediaSerializer(data, many=True, context={'request': request})
                photo = photos_data.data
            else:
                data = self.filter_queryset(self.get_queryset()).filter(Q(agency=self.request.user) & (
                            Q(company__created_by=self.request.user) | Q(company__created_by__isnull=True)), type=3,
                                                                        is_video=False,
                                                                        is_trashed=False)
                photos_data = DamWithMediaSerializer(data, many=True, context={'request': request})
                photo = photos_data.data
        if videos:
            if company:
                data = self.filter_queryset(self.get_queryset()).filter(Q(agency=self.request.user) & (
                            Q(company__created_by=self.request.user) | Q(company__created_by__isnull=True)), type=3,
                                                                        is_video=True,
                                                                        company__in=order_list,
                                                                        is_trashed=False)
                videos_data = DamWithMediaSerializer(data, many=True, context={'request': request})
                video = videos_data.data
            else:
                data = self.filter_queryset(self.get_queryset()).filter(Q(agency=self.request.user) & (
                            Q(company__created_by=self.request.user) | Q(company__created_by__isnull=True)), type=3,
                                                                        is_video=True,
                                                                        is_trashed=False)
                videos_data = DamWithMediaSerializer(data, many=True, context={'request': request})
                video = videos_data.data
        if collections:
            if company:
                data = set(self.filter_queryset(self.get_queryset()).filter(Q(agency=self.request.user) & (
                            Q(company__created_by=self.request.user) | Q(company__created_by__isnull=True)), type=2,
                                                                            company__in=order_list,
                                                                            is_trashed=False).values_list('pk',
                                                                                                          flat=True))
                collections = set(list(data))
                filter_data = DAM.objects.filter(id__in=data)
                collections_data = DamWithMediaSerializer(filter_data, many=True, context={'request': request})
                collection = collections_data.data
            else:
                data = set(self.filter_queryset(self.get_queryset()).filter(Q(agency=self.request.user) & (
                            Q(company__created_by=self.request.user) | Q(company__created_by__isnull=True)), type=2,
                                                                            is_trashed=False).values_list('pk',
                                                                                                          flat=True))
                collections = set(list(data))
                filter_data = DAM.objects.filter(id__in=data)
                collections_data = DamWithMediaSerializer(filter_data, many=True, context={'request': request})
                collection = collections_data.data
        if folders:
            if company:
                data = self.filter_queryset(self.get_queryset()).filter(Q(agency=self.request.user) & (
                            Q(company__created_by=self.request.user) | Q(company__created_by__isnull=True)), type=1,
                                                                        company__in=order_list,
                                                                        is_trashed=False)
                folders_data = DamWithMediaSerializer(data, many=True, context={'request': request})
                folder = folders_data.data
            else:
                data = self.filter_queryset(self.get_queryset()).filter(Q(agency=self.request.user) & (
                            Q(company__created_by=self.request.user) | Q(company__created_by__isnull=True)), type=1,
                                                                        is_trashed=False)
                folders_data = DamWithMediaSerializer(data, many=True, context={'request': request})
                folder = folders_data.data

        if not photos and not videos and not collections and not company:
            data1 = self.filter_queryset(self.get_queryset()).filter(Q(agency=self.request.user) & (
                        Q(company__created_by=self.request.user) | Q(company__created_by__isnull=True)), type=3,
                                                                     is_video=False,
                                                                     is_trashed=False)
            photos_data = DamWithMediaSerializer(data1, many=True, context={'request': request})
            photo = photos_data.data
            data2 = self.filter_queryset(self.get_queryset()).filter(Q(agency=self.request.user) & (
                        Q(company__created_by=self.request.user) | Q(company__created_by__isnull=True)), type=3,
                                                                     is_video=True,
                                                                     is_trashed=False)
            videos_data = DamWithMediaSerializer(data2, many=True, context={'request': request})
            video = videos_data.data
            data = set(self.filter_queryset(self.get_queryset()).filter(Q(agency=self.request.user) & (
                        Q(company__created_by=self.request.user) | Q(company__created_by__isnull=True)), type=2,
                                                                        is_trashed=False).values_list('pk', flat=True))
            filter_data = DAM.objects.filter(id__in=data)
            collections_data = DamWithMediaSerializer(filter_data, many=True, context={'request': request})
            collection = collections_data.data
            data4 = self.filter_queryset(self.get_queryset()).filter(Q(agency=self.request.user) & (
                        Q(company__created_by=self.request.user) | Q(company__created_by__isnull=True)), type=1,
                                                                     is_trashed=False)
            folders_data = DamWithMediaSerializer(data4, many=True, context={'request': request})
            folder = folders_data.data

        if company and not photos and not videos and not collections:
            data1 = self.filter_queryset(self.get_queryset()).filter(Q(agency=self.request.user) & (
                        Q(company__created_by=self.request.user) | Q(company__created_by__isnull=True)),
                                                                     company__in=order_list,
                                                                     type=3, is_video=False,
                                                                     is_trashed=False)
            photos_data = DamWithMediaSerializer(data1, many=True, context={'request': request})
            photo = photos_data.data
            data2 = self.filter_queryset(self.get_queryset()).filter(Q(agency=self.request.user) & (
                        Q(company__created_by=self.request.user) | Q(company__created_by__isnull=True)),
                                                                     company__in=order_list,
                                                                     type=3, is_video=True,
                                                                     is_trashed=False)
            videos_data = DamWithMediaSerializer(data2, many=True, context={'request': request})
            video = videos_data.data
            data = set(
                self.filter_queryset(self.get_queryset()).filter(Q(agency=self.request.user) & (
                            Q(company__created_by=self.request.user) | Q(company__created_by__isnull=True)),
                                                                 company__in=order_list,
                                                                 type=2,
                                                                 is_trashed=False).values_list('pk', flat=True))
            filter_data = DAM.objects.filter(id__in=data)
            collections_data = DamWithMediaSerializer(filter_data, many=True, context={'request': request})
            collection = collections_data.data
            data4 = self.filter_queryset(self.get_queryset()).filter(Q(agency=self.request.user) & (
                        Q(company__created_by=self.request.user) | Q(company__created_by__isnull=True)), type=1,
                                                                     company__in=order_list,
                                                                     is_trashed=False)
            folders_data = DamWithMediaSerializer(data4, many=True, context={'request': request})
            folder = folders_data.data

        context = {
            'photos': photo,
            'videos': video,
            'collections': collection,
            'folders': folder
        }
        return Response(context, status=status.HTTP_200_OK)


class CollectionDAMFilter(viewsets.ModelViewSet):
    serializer_class = DAMSerializer
    queryset = DamMedia.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['created', 'job_count']
    ordering = ['created', 'job_count']
    filterset_fields = ['dam_id', 'is_video', 'image_favourite']
    search_fields = ['dam__name', 'title']

    def get_queryset(self):
        is_parent = self.request.GET.get('dam_id', None)
        data = self.request.GET.get('ordering', None)
        queryset = self.queryset
        if not is_parent:
            queryset = queryset.filter(parent__isnull=True)
        if data == '-job_count':
            return queryset.order_by('-created')

        return queryset

    def list(self, request, *args, **kwargs):
        photos = request.GET.get('photos', None)
        videos = request.GET.get('videos', None)

        photo = None
        video = None

        if photos:
            data = self.filter_queryset(self.get_queryset()).filter(dam__agency=self.request.user,
                                                                    is_video=False,
                                                                    is_trashed=False)
            photos_data = DamMediaSerializer(data, many=True, context={'request': request})
            photo = photos_data.data
        if videos:
            data = self.filter_queryset(self.get_queryset()).filter(dam__agency=self.request.user, is_video=True,
                                                                    is_trashed=False)
            videos_data = DamMediaSerializer(data, many=True, context={'request': request})
            video = videos_data.data

        if not photos and not videos:
            data1 = self.filter_queryset(self.get_queryset()).filter(dam__agency=self.request.user, is_video=False,
                                                                     is_trashed=False)
            photos_data = DamMediaSerializer(data1, many=True, context={'request': request})
            photo = photos_data.data
            data2 = self.filter_queryset(self.get_queryset()).filter(dam__agency=self.request.user, is_video=True,
                                                                     is_trashed=False)
            videos_data = DamMediaSerializer(data2, many=True, context={'request': request})
            video = videos_data.data

        context = {
            'photos': photo,
            'videos': video,
        }
        return Response(context, status=status.HTTP_200_OK)


class ShareMediaUrl(APIView):

    def post(self, request, *args, **kwargs):
        media = request.data.get('media', None)
        email = request.data.get('email', None)
        media_names = request.data.get('mediaNames', None)
        from_email = Email(SEND_GRID_FROM_EMAIL)
        to_email = To(email)
        try:
            img_url = ''
            for index, url in enumerate(media):
                img_url += f'<p>{url}</p><b>{media_names[index]}</b><br/>'
            subject = "image link"
            content = Content("text/html",
                              f'<div style="background: rgba(36, 114, 252, 0.06) !important"><table style="font: Arial, sans-serif;border-collapse: collapse;width: 600px;margin: 0 auto;"width="600"cellpadding="0"cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 0"><div style="padding: 34px 44px;border-radius: 8px !important;background: #fff;border: 1px solid #dddddd5e;margin-bottom: 50px;margin-top: 50px;"><div class="email-logo"><img style="width: 165px"src="{LOGO_122_SERVER_PATH}"/></div><a href="#"></a><div class="welcome-text"style="padding-top: 80px"><h1 style="font: 24px">Hello,</h1></div><div class="welcome-paragraph"><div style="padding: 10px 0px;font-size: 16px;color: #384860;"> Adifect Media Links <b>{img_url}</b> </div>')
            mail = send_email(from_email, to_email, subject, content)
            if mail:
                return Response({'message': 'Media has been successfullly shared.'},
                                status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Something went wrong'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
class JobAttachmentsView(APIView):

    def get(self, request, *args, **kwargs):
        job = request.GET.get('job', None)
        level = request.GET.get('level', None)

        job_attachments = JobAttachments.objects.filter(job=job, job__user=request.user)
        job_attachments_data = JobAttachmentsSerializer(job_attachments, many=True, context={'request': request})
        job_activity = JobActivityAttachments.objects.filter(job_activity_chat__job_activity__job=job,
                                                             job_activity_chat__job_activity__job__user=request.user)
        job_activity_attachments = JobActivityAttachmentsSerializer(job_activity, many=True,
                                                                    context={'request': request})
        job_work_approved = JobWorkActivityAttachments.objects.filter(work_activity__work_activity="approved",
                                                                      work_activity__job_activity_chat__job=job,
                                                                      work_activity__job_activity_chat__job__user=request.user)
        job_work_approved_attachments = JobWorkActivityAttachmentsSerializer(job_work_approved, many=True,
                                                                             context={'request': request})
        job_work_rejected = JobWorkActivityAttachments.objects.filter(work_activity__work_activity="rejected",
                                                                      work_activity__job_activity_chat__job=job,
                                                                      work_activity__job_activity_chat__job__user=request.user)
        job_work_rejected_attachments = JobWorkActivityAttachmentsSerializer(job_work_rejected, many=True,
                                                                             context={'request': request})
        job_applied = JobAppliedAttachments.objects.filter(job_applied__job=job, job_applied__job__user=request.user)
        job_applied_attachments = JobAppliedAttachmentsSerializer(job_applied, many=True, context={'request': request})
        final_approved_data = JobWorkAttachments.objects.filter(job_work__job_applied__job=job,
                                                                job_work__job_applied__job__user=request.user,
                                                                job_work__status=1)
        final_approved = JobWorkAttachmentsSerializer(final_approved_data, many=True, context={'request': request})
        context = {
            'job_attachments': job_attachments_data.data,
            'job_activity_attachments': job_activity_attachments.data,
            'approved_job_work_attachments': job_work_approved_attachments.data,
            'rejected_job_work_attachments': job_work_rejected_attachments.data,
            'job_applied_attachments': job_applied_attachments.data,
            'final_approved_data': final_approved.data
        }
        return Response(context, status=status.HTTP_200_OK)


def ApprovalReminder(approver, work, reminder=None):
    try:
        if not work.job_applied.user.profile_img:
            profile_image = ''
        else:
            profile_image = work.job_applied.user.profile_img.url
        img_url = ''
        for j in JobWorkAttachments.objects.filter(job_work=work):
            img_url += f'<img style="width: 100.17px;height:100px;margin: 10px 10px 0px 0px;border-radius: 16px;" src="{j.work_attachments.url}"/>'
        subject = f'Job Work Approver Reminder '
        content = Content("text/html",
                          f'<div style="background: rgba(36, 114, 252, 0.06) !important"><table style="font: Arial, sans-serif;border-collapse: collapse;width: 600px;margin: 0 auto;"width="600"cellpadding="0"cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 0"><div style="padding: 34px 44px;border-radius: 8px !important;background: #fff;border: 1px solid #dddddd5e;margin-bottom: 50px;margin-top: 50px;"><div class="email-logo"><img style="width: 165px"src="{LOGO_122_SERVER_PATH}"/></div><a href="#"></a><div class="welcome-text" style="padding-top: 80px"><h1 style="font: 24px">Hello {approver.username},</h1></div><div class="welcome-paragraph"><div style="padding: 10px 0px;font-size: 16px;color: #384860;">Please Approve or Request an Edit of this asset within {reminder} hours of receiving this approval request.</div><div style="background-color: rgba(36, 114, 252, 0.1);border-radius: 8px;"><div style="padding: 20px"><div style="display: flex;align-items: center;"><img style="width: 40px;height: 40px;border-radius: 50%;" src="{profile_image}" /><span style="font-size: 14px;color: #2472fc;font-weight: 700;margin-bottom: 0px;padding: 10px 14px;">{work.job_applied.user.username} delivered the work</span><span style="font-size: 12px;color: #a0a0a0;font-weight: 500;margin-bottom: 0px;padding: 10px 14px;">{work.created.strftime("%B %d, %Y %H:%M:%p")}</span></div><div style="font-size: 16px;color: #000000;padding-left: 54px;">{work.message}</div><div style="padding: 11px 54px 0px">{img_url}</div><div style="display: flex"></div></div></div><div style="padding: 20px 0px;font-size: 16px;color: #384860;"></div>Sincerely,<br />The Adifect Team</div><div style="padding-top: 40px"class="create-new-account"><a href="{FRONTEND_SITE_URL}/?redirect=jobs/details/{work.job_applied.job.id}"><button style="height: 56px;padding: 15px 44px;background: #2472fc;border-radius: 8px;border-style: none;color: white;font-size: 16px;">View Asset on Adifect</button></a></div><div style="padding: 50px 0px"class="email-bottom-para"><div style="padding: 20px 0px;font-size: 16px;color: #384860;">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect? <a href="#"><span style="text-decoration: underline">Unsubscribe.</span></a></div><div style="font-size: 16px; color: #384860">© 2022 Adifect</div></div></div></td></tr></tbody></table></div>')
        data = send_email(Email(SEND_GRID_FROM_EMAIL), approver.email, subject, content)
    except Exception as e:
        print(e)


from django.db.models import F
from django.utils import timezone
from datetime import timedelta


#
class NudgeReminder(APIView):
    queryset = MemberApprovals.objects.all()

    def get(self, request, *args, **kwargs):
        try:
            queryset = self.queryset.filter(status=0, workflow_stage__is_nudge=True).exclude(
                nudge_status=F('workflow_stage__nudge_time'))
            for i in queryset:
                if '3' in i.workflow_stage.nudge_time and not '3' in i.nudge_status if i.nudge_status is not None else '':
                    if timezone.now() >= i.created + timedelta(hours=(int(i.workflow_stage.approval_time) - int(3))):
                        # send email
                        ApprovalReminder(i.approver.user.user, i.job_work, '3')
                        i.nudge_status = i.nudge_status + '3,'
                        i.save()

                if '6' in i.workflow_stage.nudge_time and not '6' in i.nudge_status if i.nudge_status is not None else '':
                    if timezone.now() >= i.created + timedelta(hours=(int(i.workflow_stage.approval_time) - int(6))):
                        # send email
                        ApprovalReminder(i.approver.user.user, i.job_work, '6')
                        i.nudge_status = i.nudge_status + '6,'
                        i.save()

                if '9' in i.workflow_stage.nudge_time and not '9' in i.nudge_status if i.nudge_status is not None else '':
                    if timezone.now() >= i.created + timedelta(hours=(int(i.workflow_stage.approval_time) - int(9))):
                        # send email
                        ApprovalReminder(i.approver.user.user, i.job_work, '9')
                        i.nudge_status = i.nudge_status + '9,'
                        i.save()

                if '12' in i.workflow_stage.nudge_time and not '12' in i.nudge_status if i.nudge_status is not None else '':
                    if timezone.now() >= i.created + timedelta(hours=(int(i.workflow_stage.approval_time) - int(12))):
                        # send email
                        ApprovalReminder(i.approver.user.user, i.job_work, '12')
                        i.nudge_status = i.nudge_status + '12,'
                        i.save()
            return Response({'message': 'Reminder Email Sent Successfully'},
                            status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'message': 'Here Is Error', 'error': str(e)},
                            status=status.HTTP_200_OK)


class InHouseMemberViewset(viewsets.ModelViewSet):
    serializer_class = InviteMemberSerializer
    queryset = InviteMember.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['company']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).filter(user__levels=4, user__user__isnull=False,
                                                                    company__is_active=True, is_inactive=False)
        serializer = self.serializer_class(queryset, many=True, context={request: 'request'})
        return Response(data=serializer.data)


@permission_classes([IsAuthenticated])
class CompanyImageCount(APIView):
    def get(self, request, *args, **kwargs):
        id = request.GET.get('id', None)
        photos = request.GET.get('photos', None)
        videos = request.GET.get('videos', None)
        collections = request.GET.get('collections', None)
        folders = request.GET.get('folders', None)
        favourites = request.GET.get('favourite', None)
        result = []

        company_data = Company.objects.filter(
            Q(agency=request.user) & (Q(created_by=request.user) | (Q(created_by__isnull=True))), is_active=True)
        if id:
            parent = id
        else:
            parent = None

        q_photos = Q()
        if photos:
            q_photos = Q(Q(type=3) & Q(is_video=False))
            # company_count = company_count.filter(dam_company__type=3, is_video=False)
        q_videos = Q()
        if videos:
            q_videos = Q(Q(type=3) & Q(is_video=True))
            # company_count = company_count.filter(dam_company__type=3,dam_company__is_video=True)
        q_collections = Q()
        if collections:
            q_collections = Q(type=2)
            # company_count = company_count.filter(dam_company__type=2,is_trashed=False)
        q_folders = Q()
        if folders:
            q_folders = Q(type=1)
        q_favourites = Q()
        if favourites:
            q_favourites = Q(is_favourite=True)
        for i in company_data:
            # company_count = company_count.filter(dam_company__type=1,is_trashed=False)
            company_count = DAM.objects.filter((q_photos | q_videos | q_collections | q_folders | q_favourites)).filter(
                (Q(q_favourites & q_photos) | (Q(q_favourites & q_videos)) | (Q(q_favourites & q_collections)) | (
                    Q(q_favourites & q_photos & q_videos))) & (Q(company=i) & Q(parent=parent))).count()
            result.append({f'name': {i.name}, 'id': {i.id}, 'count': company_count})
            # company_count = DAM.objects.filter(q_photos | q_videos | q_collections | q_folders & q_company)
        #     initial_count = company_count.values_list('id', flat=True)
        #     company_count = company_count.values('dam_company__company', 'name', 'id', 'is_active').order_by().annotate(
        #         Count('dam_company__company'))
        #     # null_company_count = company_count = Company.objects.filter(Q(agency=request.user) & (Q(dam_company__parent=id) | Q(dam_company__parent=None))).values('dam_company__company','name','id','is_active').order_by().annotate(Count('dam_company__company'))
        #     null_company_count = Company.objects.filter(agency=request.user, dam_company__parent=None).exclude(
        #         id__in=list(initial_count)).values('dam_company__company', 'name', 'id', 'is_active').distinct('pk')
        #     context = {
        #         'company_count': company_count,
        #         'null_company_count': null_company_count,
        #     }
        #     return Response(context, status=status.HTTP_200_OK)
        #
        # else:
        #     company_initial = Company.objects.filter(agency=request.user, dam_company__parent=None)
        #     q_photos = Q()
        #     if photos:
        #         q_photos = Q(Q(dam_company__type=3) & Q(dam_company__is_video=False))
        #         print(q_photos, 'phtoto')
        #         # company_count = company_count.filter(dam_company__type=3, is_video=False)
        #     q_videos = Q()
        #     if videos:
        #         q_videos = Q(Q(dam_company__type=3) & Q(dam_company__is_video=True))
        #         print(q_photos, 'video')
        #
        #         # company_count = company_count.filter(dam_company__type=3,dam_company__is_video=True)
        #     q_collections = Q()
        #     if collections:
        #         q_collections = Q(dam_company__type=2)
        #         print(collections, 'collection')
        #
        #         # company_count = company_count.filter(dam_company__type=2,is_trashed=False)
        #     q_folders = Q()
        #     if folders:
        #         q_folders = Q(dam_company__type=1)
        #         print(folders, 'collection')
        #     company_initial = company_initial.filter(q_photos | q_videos | q_collections | q_folders)
        #     company_count = company_initial.values('dam_company__company', 'name', 'id',
        #                                            'is_active').order_by().annotate(Count('dam_company__company'))
        #     null_company_count = Company.objects.filter(agency=request.user).exclude(
        #         id__in=list(company_initial.values_list('id', flat=True))).values('dam_company__company', 'name', 'id',
        #                                                                           'is_active').distinct('pk')

        context = {
            'company_data': result,
            'status': status.HTTP_200_OK,
            # 'company_count': company_count,
            # 'null_company_count': null_company_count,
        }
        return Response(context, status=status.HTTP_200_OK)
        #     company_count1 = 0
        #     company_count2 = 0
        #     company_count3 = 0
        #     company_count4 = 0
        #     company_count = Company.objects.filter(agency=request.user,dam_company__parent=id) 

        #     if photos:

        #         company_filter1 = company_count.filter(dam_company__type=3, dam_company__is_video=False)
        #         company_count1 = company_filter1.count()
        #         company_name1 = company_filter1.values('name', 'id')
        #         collected_data = company_name1 + company_count1
        #         print(collected_data)
        #         print("hereeeeeeeeeeeeeeeeeeeee")
        #     if videos:
        #         company_count2 = company_count.filter( dam_company__type=3,dam_company__is_video=True).count
        #     if collections :
        #         company_count3 = company_count.filter(dam_company__type=2,is_trashed=False)
        #     if folders:
        #         company_count4 = company_count.filter(dam_company__type=1,is_trashed=False)
        #     final_count = collected_data
        #     initial_count = company_count.values_list('id',flat=True)
        #     company_count = company_count.values('dam_company__company','name','id','is_active','dam_company_').order_by().annotate(Count('dam_company__company'))

        #     # null_company_count = company_count = Company.objects.filter(Q(agency=request.user) & (Q(dam_company__parent=id) | Q(dam_company__parent=None))).values('dam_company__company','name','id','is_active').order_by().annotate(Count('dam_company__company'))
        #     null_company_count = Company.objects.filter(agency=request.user , dam_company__parent=None).exclude(id__in=list(initial_count)).values('dam_company__company','name','id','is_active').distinct('pk')
        #     context = {
        #     'company_count': company_count,
        #     'null_company_count': null_company_count,
        #     'final_count' : collected_data,
        #     }
        #     return Response(context, status=status.HTTP_200_OK)

        # else:
        #     company_initial1 = 0
        #     company_initial2 = 0
        #     company_initial3 = 0
        #     company_initial4 = 0
        #     collected_data = 0
        #     company_initial = Company.objects.filter(agency=request.user,dam_company__parent=None)

        #     if photos:
        #         company_filter1 = company_initial.filter(dam_company__type=3, dam_company__is_video=False)
        #         for company in company_filter1:
        #             print(company)
        #         company_name1 = company_filter1.values('name', 'id')
        #         company_count1 = company_name1.count()
        #         collected_data = company_name1 , company_count1
        #         # print(collected_data)
        #         print("hereeeeeeeeeeeeeeeeeeeee")
        #     if videos:
        #         company_initial2 = company_initial.filter( dam_company__type=3,dam_company__is_video=True).count()
        #     if collections :
        #         company_initial3 = company_initial.filter(dam_company__type=2,is_trashed=False).count()
        #     if folders:
        #         company_initial4 = company_initial.filter(dam_company__type=1,is_trashed=False).count()
        #     final_count = collected_data
        #     company_count= company_initial.values('dam_company__company','name','id','is_active').order_by().annotate(Count('dam_company__company'))
        #     null_company_count = Company.objects.filter(agency=request.user).exclude(id__in=list(company_initial.values_list('id',flat=True))).values('dam_company__company','name','id','is_active').distinct('pk')

        #     context = {
        #     'company_count': company_count,
        #     'null_company_count': null_company_count,
        #     'final_count' : final_count,
        #     }
        #     return Response(context, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
class JobFeedbackViewset(viewsets.ModelViewSet):
    serializer_class = JobFeedbackSerializer
    queryset = JobFeedback.objects.all()
    ordering_fields = ['modified', 'created', 'rating']
    ordering = ['modified', 'created', 'rating']
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['receiver_user', 'sender_user', 'rating', 'job']
    search_fields = ['feedback', ]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).filter(receiver_user=request.user)
        serializer = self.serializer_class(queryset, many=True, context={request: 'request'})
        return Response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            if serializer.validated_data['sender_user'] is not None and serializer.validated_data[
                'sender_user'].role != 1:
                JobActivity.objects.create(job=serializer.validated_data['job'], activity_type=7, activity_status=0,
                                           user=serializer.validated_data['receiver_user'], activity_by=0)
            context = {
                'message': 'Created Successfully',
                'status': status.HTTP_201_CREATED,
                'errors': serializer.errors,
                'data': serializer.data,
            }
            return Response(context)
        else:
            context = {
                'message': 'Error !',
                'status': status.HTTP_400_BAD_REQUEST,
                'errors': serializer.errors,
            }
            return Response(context, status=status.HTTP_400_BAD_REQUEST)


def send_reminder_email():
    try:
        queryset = MemberApprovals.objects.filter(status=0, workflow_stage__is_nudge=True).exclude(
            nudge_status=F('workflow_stage__nudge_time'))
        for i in queryset:
            if '3' in i.workflow_stage.nudge_time and not '3' in i.nudge_status if i.nudge_status is not None else '':
                if timezone.now() >= i.created + timedelta(hours=(int(i.workflow_stage.approval_time) - int(3))):
                    # send email
                    ApprovalReminder(i.approver.user.user, i.job_work, '3')
                    i.nudge_status = i.nudge_status + '3,'
                    i.save()

            if '6' in i.workflow_stage.nudge_time and not '6' in i.nudge_status if i.nudge_status is not None else '':
                if timezone.now() >= i.created + timedelta(hours=(int(i.workflow_stage.approval_time) - int(6))):
                    # send email
                    ApprovalReminder(i.approver.user.user, i.job_work, '2')
                    i.nudge_status = i.nudge_status + '6,'
                    i.save()

            if '9' in i.workflow_stage.nudge_time and not '9' in i.nudge_status if i.nudge_status is not None else '':
                if timezone.now() >= i.created + timedelta(hours=(int(i.workflow_stage.approval_time) - int(9))):
                    # send email
                    ApprovalReminder(i.approver.user.user, i.job_work, '1')
                    i.nudge_status = i.nudge_status + '9,'
                    i.save()

            if '12' in i.workflow_stage.nudge_time and not '12' in i.nudge_status if i.nudge_status is not None else '':
                if timezone.now() >= i.created + timedelta(hours=(int(i.workflow_stage.approval_time) - int(12))):
                    # send email
                    ApprovalReminder(i.approver.user.user, i.job_work)
                    i.nudge_status = i.nudge_status + '12,'
                    i.save()
    except  Exception as e:
        print(e)
        return True


class AgencyNotificationViewset(viewsets.ModelViewSet):
    serializer_class = NotificationsSerializer
    queryset = Notifications.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['user', 'is_seen', 'company']

    def list(self, request, *args, **kwargs):
        read_more = {}
        today = datetime.now().date()
        queryset = self.filter_queryset(self.get_queryset())
        queryset_today = queryset.filter(created__date=today).values()
        queryset_earlier = queryset.filter(created__lt=today).values()
        offset = int(request.GET.get('offset', default=0))
        count = queryset.filter(is_seen=False).count()
        if offset:
            total_items = queryset.count()
            has_more_items = total_items > offset
            queryset = queryset[0:offset]
            queryset_today = queryset_today[0:offset]
            queryset_earlier = queryset_earlier[0:offset]
            if has_more_items:
                read_more = "True"
            else:
                read_more = "False"
        else:
            queryset = queryset[0:5]
            queryset_today = queryset_today[0:5]
            queryset_earlier = queryset_earlier[0:5]

        serializer = self.serializer_class(queryset, many=True, context={request: 'request'})
        context = {'data': serializer.data, 'count': count, 'today': queryset_today, 'earlier': queryset_earlier,
                   'read_more': read_more}
        return Response(context)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        if serializer.is_valid(raise_exception=True):
            company_id = request.data.get('company_id', None)
            if company_id:
                self.perform_update(serializer)
                Notifications.objects.filter(user=request.user.id, is_seen=False, company=company_id).update(
                    is_seen=True)
            else:
                self.perform_update(serializer)
                Notifications.objects.filter(user=request.user.id, is_seen=False).update(is_seen=True)
            context = {
                'message': 'Updated Successfully...',
                'status': status.HTTP_200_OK,
                'errors': serializer.errors,
                'data': serializer.data,
            }
            return Response(context)
        else:
            return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            id_list = request.GET.get('id', None)
            order_list = id_list.split(",") if id_list else []
            user_id = request.GET.get('user_id', None)
            if user_id:
                data = Notifications.objects.filter(user_id=user_id).delete()
            if order_list:
                data = Notifications.objects.filter(id__in=order_list).delete()
            context = {
                'message': 'Deleted Successfully',
                'status': status.HTTP_204_NO_CONTENT,
                'errors': False,
            }
            return Response(context, status=status.HTTP_200_OK)
        except Exception as e:
            context = {
                'message': 'Something Went Wrong',
                'status': status.HTTP_400_BAD_REQUEST,
                'errors': True,
            }
            return Response(context, status=status.HTTP_400_BAD_REQUEST)


class GetAdminMembers(APIView):
    def get(self, request, *args, **kwargs):
        queryset = InviteMember.objects.filter(agency=request.user, user__levels=1, is_trashed=False,
                                               user__isnull=False, agency__is_account_closed=False).order_by(
            '-modified')
        if request.GET.get('company'):
            queryset = queryset.filter(company=request.GET.get('company'))
        serializer = InviteMemberSerializer(queryset, many=True)
        context = {
            "user": self.request.user.id,
            "data": serializer.data,
            "status": status.HTTP_200_OK,
        }
        return Response(context, status=status.HTTP_200_OK)


# class ChangeMemberRole(APIView):
#     queryset = InviteMember.objects.all()
#     def put(self, request,pk=None, *args, **kwargs):
#         if request.data['level']:
#             data = AgencyLevel.objects.update(user=request.data['user'],levels=request.data['level'])
#             context = {
#                     'data':data,
#                     'message': 'Media Uploaded Successfully',
#                     'status': status.HTTP_201_CREATED,
#                 }
#         else:
#             context = {
#                     'message': 'Something went wrong',
#                     'status': status.HTTP_400_BAD_REQUEST,
#                 }
#         return Response(context)

class CollectionCount(ReadOnlyModelViewSet):
    queryset = DamMedia.objects.all()

    def list(self, request, *args, **kwargs):
        id = request.GET.get('id', None)
        favourite = self.queryset.filter(dam__agency=request.user, image_favourite=True, dam=id).count()
        images = self.queryset.filter(dam__agency=request.user, is_video=False, dam=id).count()
        videos = self.queryset.filter(dam__agency=request.user, is_video=True, dam=id).count()

        context = {'favourites': favourite,
                   'images': images,
                   'videos': videos,
                   }
        return Response(context)


class AudienceListCreateView(generics.ListCreateAPIView):
    """
    View for creating audience and view list of all audiences
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    serializer_class = AudienceListCreateSerializer
    queryset = Audience.objects.filter(is_trashed=False).order_by('-id')
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'audience_id']
    ordering_fields = ['id', 'title', 'audience_id']
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        API to get list of audiences
        """
        self.queryset = self.filter_queryset(self.queryset)
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return Response({'data': response.data, 'message': AUDIENCE_RETRIEVED_SUCCESSFULLY})

    def post(self, request, *args, **kwargs):
        serializers = self.get_serializer(data=request.data)
        serializers.is_valid(raise_exception=True)
        serializers.save()
        return Response({'data': serializers.data, 'message': AUDIENCE_CREATED_SUCCESSFULLY},
                        status=status.HTTP_201_CREATED)


class AudienceRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    View to retrieve, update and delete audience
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    serializer_class = AudienceRetrieveUpdateDestroySerializer
    queryset = Audience.objects.filter(is_trashed=False).order_by('-id')
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get(self, request, *args, **kwargs):
        """API to get audience"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data, 'message': AUDIENCE_RETRIEVED_SUCCESSFULLY},
                        status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        """put request to update audience"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': serializer.data, 'message': AUDIENCE_UPDATED_SUCCESSFULLY},
                        status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """delete request to inactivate audience"""
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommunityAudienceListView(generics.ListAPIView):
    """
    View for list of all audiences as per the community
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    serializer_class = AudienceCommunityListSerializer
    queryset = Audience.objects.filter(is_trashed=False).order_by('-id')
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['id', 'title']
    permission_classes = [IsAuthenticated]

    def get_queryset(self, *args, **kwargs):
        story_obj = Story.objects.filter(id=self.request.query_params.get('story_id')).first()
        if not story_obj:
            raise serializers.ValidationError({"story": [f"Invalid pk \"{self.request.query_params.get('story_id')}\" - object does not exist."]})
        queryset = self.queryset.filter(
            Q(community__id=story_obj.community.id) | Q(community__isnull=True))
        return queryset

    def get(self, request, *args, **kwargs):
        """
        API to get list of audiences
        """
        self.queryset = self.filter_queryset(self.get_queryset())
        if not request.GET.get("page", None):
            serializer = self.get_serializer(self.queryset, many=True)
            return Response({'data': serializer.data, 'message': AUDIENCE_RETRIEVED_SUCCESSFULLY},
                            status=status.HTTP_200_OK)
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return Response({'data': response.data, 'message': AUDIENCE_RETRIEVED_SUCCESSFULLY})
