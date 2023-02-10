from django.shortcuts import render
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import permission_classes
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated

from administrator.models import JobApplied, JobActivity, Job, MemberApprovals, JobAttachments, JobTemplateAttachments, JobTasks, JobTemplate, JobTemplateTasks, JobActivityAttachments, JobWorkActivityAttachments, JobAppliedAttachments, JobWorkAttachments

from administrator.pagination import FiveRecordsPagination
from administrator.serializers import JobAppliedSerializer, JobActivitySerializer, JobsWithAttachmentsSerializer, JobSerializer, JobTemplateAttachmentsSerializer, JobsWithAttachmentsThumbnailSerializer,  JobTemplateSerializer,  JobTemplateSerializer, JobTemplateWithAttachmentsSerializer, JobAttachmentsSerializer, JobActivityAttachmentsSerializer, JobWorkActivityAttachmentsSerializer, JobAppliedAttachmentsSerializer, JobWorkAttachmentsSerializer

from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.db.models import Count, Avg
from agency.models import Workflow_Stages, InviteMember, Company,WorksFlow, DAM, DamMedia
from authentication.manager import IsAdminMember, IsMarketerMember, IsApproverMember,InHouseMember
from agency.serializers import InviteMemberSerializer,CompanySerializer,WorksFlowSerializer, MyProjectSerializer, StageSerializer, DAMSerializer, DamWithMediaSerializer, DamWithMediaRootSerializer, DamMediaSerializer
from django.db.models import Subquery
from rest_framework.decorators import action
from administrator.views  import validate_job_attachments, dam_images_templates, dam_sample_template_images_list, dam_images_list, dam_sample_images_list
import json
from sendgrid.helpers.mail import Mail, Email, To, Content
from adifect.settings import SEND_GRID_API_key, FRONTEND_SITE_URL, LOGO_122_SERVER_PATH, BACKEND_SITE_URL, \
    TWILIO_NUMBER, TWILIO_NUMBER_WHATSAPP, SEND_GRID_FROM_EMAIL
from helper.helper import StringEncoder, send_text_message, send_skype_message, send_email, send_whatsapp_message
from django.db.models import Subquery, Q
from notification.models import Notifications
from notification.serializers import NotificationsSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet
from datetime import datetime
from django.utils import timezone


# Create your views here.
@permission_classes([IsAuthenticated])
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
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
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


# @permission_classes([IsAuthenticated])
# class MemberJobListViewSet(viewsets.ModelViewSet):
#     serializer_class = JobsWithAttachmentsSerializer
#     queryset = Workflow_Stages.objects.all()
#     pagination_class = FiveRecordsPagination
#     filter_backends = [DjangoFilterBackend, SearchFilter]
#     # filterset_fields = ['status']
#     search_fields = ['stage_workflow__job_workflow_title','stage_workflow__job_workflow_description','stage_workflow__job_workflow_skills__skill_name','stage_workflow__job_workflow_tags']

#     def list(self, request, *args, **kwargs):
#         user = request.user
#         if request.GET.get('company'): 
#             if  InviteMember.objects.filter(company=request.GET.get('company'),user__user=request.user,user__levels=3):
#                 workflow_id = self.filter_queryset(self.get_queryset()).filter(workflow__is_trashed=False,
#                                                 workflow__isnull=False, is_trashed=False).values_list('workflow_id',
#                                                                                                         flat=True)
#                 job_data = Job.objects.filter(workflow_id__in=list(workflow_id),company=request.GET.get('company')).exclude(status=0).order_by('-modified')
#             else:
#                 job_data = Job.objects.filter(company=request.GET.get('company')).exclude(status=0).order_by('-modified')
#             if request.GET.get('status'):
#                 job_data = job_data.filter(job_applied__status=request.GET.get('status'))
#             if request.GET.get('ordering'):    
#                 job_data = job_data.order_by(request.GET.get('ordering'))
#             paginated_data = self.paginate_queryset(job_data)
#             serializer = self.serializer_class(paginated_data, many=True, context={'request': request})
#             return self.get_paginated_response(data=serializer.data)
#         return Response({'details': 'No Company Found'}, status=status.HTTP_404_NOT_FOUND)

#     def retrieve(self, request, pk=None):
#         if pk:
#             job_data = Job.objects.filter(id=pk).first()
#             serializer = self.serializer_class(job_data, context={'request': request})
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response({'details': 'No Job Found'}, status=status.HTTP_404_NOT_FOUND)





@permission_classes([IsAuthenticated])
class MemberJobListViewSet(viewsets.ModelViewSet):
    serializer_class = JobsWithAttachmentsSerializer
    queryset = Job.objects.all().exclude(status=0)
    pagination_class = FiveRecordsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter,OrderingFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', '-created']
    filterset_fields = ['company','job_applied__status']
    search_fields = ['title','description','skills__skill_name','tags']

    def list(self, request, *args, **kwargs):
        user = request.user
        if request.GET.get('company'):
            if  InviteMember.objects.filter(company=request.GET.get('company'),user__user=request.user,user__levels=3):
                job_data = self.filter_queryset(self.get_queryset()).filter(workflow__is_trashed=False,
                                                workflow__isnull=False,workflow__stage_workflow__approvals__user__user=user)
            else:
                job_data = self.filter_queryset(self.get_queryset())
            # if request.GET.get('status'):
            #     job_data = job_data.filter(job_applied__status=request.GET.get('status'))
            # if request.GET.get('ordering'):    
            #     job_data = job_data.order_by(request.GET.get('ordering'))
            paginated_data = self.paginate_queryset(job_data)
            serializer = self.serializer_class(paginated_data, many=True, context={'request': request})
            return self.get_paginated_response(data=serializer.data)
        return Response({'details': 'No Company Found'}, status=status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, pk=None):
        if pk:
            job_data = Job.objects.filter(id=pk).first()
            serializer = self.serializer_class(job_data, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'details': 'No Job Found'}, status=status.HTTP_404_NOT_FOUND)






@permission_classes([IsAuthenticated])
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


@permission_classes([IsAdminMember | IsApproverMember | IsMarketerMember | InHouseMember ])
class InviteUserCompanyListViewSet(viewsets.ModelViewSet):
    serializer_class = InviteMemberSerializer
    queryset = InviteMember.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).filter(user__user=request.user).values('company','company__name','agency').exclude(status=2)
        # serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(data=queryset, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
class MemberMarketerJobViewSet(viewsets.ModelViewSet):
    serializer_class = JobAppliedSerializer
    queryset = JobApplied.objects.filter(is_trashed=False)
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def list(self, request, *args, **kwargs):
        jobs = Job.objects.filter(workflow__stage_workflow__observer__user__user=request.user)
        queryset = JobApplied.objects.filter(job__workflow__stage_workflow__observer__user__user=request.user)
        job_count = jobs.count()
        job_review = queryset.filter(status=3).count()
        job_progress = queryset.filter(status=2).count()
        job_completed = queryset.filter(status=4).count()
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        context = {
            'Total_Job_count': job_count,
            'In_progress_jobs': job_progress,
            'In_review': job_review,
            'completed_jobs': job_completed,
            'data': serializer.data,
        }
        return Response(context, status=status.HTTP_200_OK)


@permission_classes([IsApproverMember | IsAdminMember | IsMarketerMember | InHouseMember])
class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    queryset = Company.objects.all().order_by('-modified')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_active', 'agency', 'is_blocked','name']
    search_fields = ['=is_active']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        company = queryset.filter(invite_company_list__user__user=request.user)
        serializer = self.serializer_class(company, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        queryset = self.queryset.get(pk=pk)
        serializer = self.serializer_class(queryset, context={'request': request})
        job_count = queryset.job_company.all().count()
        context = {
        'Total_Job_count': job_count,
        'data': serializer.data

        }
        return Response(context, status=status.HTTP_200_OK)



@permission_classes([IsAdminMember | IsMarketerMember])
class WorksFlowViewSet(viewsets.ModelViewSet):
    serializer_class = WorksFlowSerializer
    queryset = WorksFlow.objects.filter(is_trashed=False).order_by('-modified')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['company', 'is_blocked','agency']
    search_fields = ['=company']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).filter(company__is_active=True)
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    def create(self, request, *args, **kwargs):
        data = request.data
        print(data)
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
                                                    workflow=workflow_latest, order=i['order'],approval_time=i['approval_time'],is_nudge=i['is_nudge'],nudge_time=i['nudge_time'])
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
                                                                is_all_approval=i['is_all_approval'],approval_time=i['approval_time'],is_nudge=i['is_nudge'],nudge_time=i['nudge_time'])
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
                                                              is_all_approval=i['is_all_approval'], order=i['order'],approval_time=i['approval_time'],is_nudge=i['is_nudge'],nudge_time=i['nudge_time'])
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


@permission_classes([IsAdminMember | IsMarketerMember])
class MemberStageViewSet(viewsets.ModelViewSet):
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



@permission_classes([IsAdminMember | IsMarketerMember])
class MemberMyProjectViewSet(viewsets.ModelViewSet):
    serializer_class = MyProjectSerializer
    queryset = JobApplied.objects.filter(job__is_trashed=False).exclude(job=None)
    filter_backends = [DjangoFilterBackend, SearchFilter, ]
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
        filter_data = queryset.filter(
            pk__in=Subquery(
                queryset.order_by('job_id').distinct('job_id').values('pk')
            )).order_by(ordering)
        if request.GET.get('job__is_active', None) == 'true':
            filter_data = filter_data.filter(job__is_active=True)
        paginated_data = self.paginate_queryset(filter_data)
        serializer = self.serializer_class(paginated_data, many=True, context={'request': request})
        return self.get_paginated_response(data=serializer.data)        

@permission_classes([IsMarketerMember | IsAdminMember])
class InviteMemberViewSet(viewsets.ModelViewSet):
    serializer_class = InviteMemberSerializer
    queryset = InviteMember.objects.all().order_by('-modified')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['company']
    search_fields = ['=company']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).filter(is_trashed=False,
                                                                    user__isnull=False,
                                                                    agency__is_account_closed=False,company__is_active=True).order_by(
            '-modified').exclude(user__user=self.request.user)
        serializer = InviteMemberSerializer(queryset, many=True)
        return Response(serializer.data)

@permission_classes([IsAdminMember | IsMarketerMember])
class JobViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    queryset = Job.objects.filter(company__is_active=True)
    job_template_attach = JobTemplateAttachmentsSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['company','is_active','status']
    search_fields = ['company__name', 'title', 'description', 'tags', 'skills__skill_name']
    pagination_class = FiveRecordsPagination

    def list(self, request, *args, **kwargs):
        user_role = request.user.role
        if user_role == 0:
            job_data = self.filter_queryset(self.get_queryset()).exclude(status=0).order_by('-modified')
        else:
            job_data = self.filter_queryset(self.get_queryset()).exclude(status=0).exclude(is_active=0).order_by('-modified')
        paginated_data = self.paginate_queryset(job_data)
        serializer = JobsWithAttachmentsThumbnailSerializer(paginated_data, many=True, context={'request': request})
        return self.get_paginated_response(data=serializer.data)

    def retrieve(self, request, pk=None):
        id = pk
        if id is not None:
            job_data = Job.objects.get(id=pk)
            serializer = JobsWithAttachmentsSerializer(job_data, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        image = request.FILES.getlist('image')
        sample_image = request.FILES.getlist('sample_image')
        template_image = request.FILES.getlist('template_image')
        templte_sample_image = request.FILES.getlist('template_sample_image')
        dam_images = request.data.getlist('dam_images')
        dam_sample_images = request.data.getlist('dam_sample_images')

        if serializer.is_valid():
            template_name = serializer.validated_data.get('template_name', None)
            if template_name:
                if Job.objects.filter(template_name=template_name, is_trashed=False).exclude(
                        template_name=None).exists():
                    context = {
                        'message': 'Job Template Already Exist',
                        'status': status.HTTP_400_BAD_REQUEST,
                        'errors': serializer.errors,
                        'data': serializer.data,
                    }
                    return Response(context)

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
            dam_images_list(dam_images, job_id)
            dam_sample_images_list(dam_sample_images, job_id)
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
                print("here data")
                if second_serializer.is_valid():
                    self.perform_create(second_serializer)
                    print("done")
                    Job_template_id = JobTemplate.objects.latest('id')
                    if request.data.get("tasks", None):
                        objs = []
                        for i in json.loads(request.data['tasks']):
                            task_title = i['title']
                            if task_title:
                                objs.append(JobTemplateTasks(job_template=Job_template_id, title=task_title,
                                                             due_date=i['due_date']))
                        task = JobTemplateTasks.objects.bulk_create(objs)

                    if image:
                        image_error = validate_job_attachments(image)
                        if image_error != 0:
                            return Response({'message': "Invalid Job Attachments images"},
                                            status=status.HTTP_400_BAD_REQUEST)
                        for i in template_image:
                            JobTemplateAttachments.objects.create(job_template=Job_template_id, job_template_images=i)
                    if sample_image:
                        sample_image_error = validate_job_attachments(sample_image)
                        if sample_image_error != 0:
                            return Response({'message': "Invalid Job Attachments images"},
                                            status=status.HTTP_400_BAD_REQUEST)
                        for i in templte_sample_image:
                            JobTemplateAttachments.objects.create(job_template=Job_template_id, work_sample_images=i)
                else:
                    print("here error")
                    print(serializer.errors)
            JobActivity.objects.create(job=job_id, activity_type=JobActivity.Type.Create)
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
        template_image = request.FILES.getlist('template_image')
        templte_sample_image = request.FILES.getlist('template_sample_image')
        dam_images = request.data.getlist('dam_images')
        dam_sample_images = request.data.getlist('dam_sample_images')
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            if not JobApplied.objects.filter(Q(job=instance) & (Q(status=2) | Q(status=3) | Q(status=4))):
                template_name = serializer.validated_data.get('template_name', None)
                if template_name:
                    if Job.objects.filter(
                            Q(pk=instance.pk) & Q(template_name=template_name) & Q(is_trashed=False)).exclude(
                        template_name=None).exists():
                        context = {
                            'message': 'Job Template Already Exist',
                            'status': status.HTTP_400_BAD_REQUEST,
                            'errors': serializer.errors,
                            'data': serializer.data,
                        }
                        return Response(context, status=status.HTTP_400_BAD_REQUEST)
                self.perform_update(serializer)
                job_id = Job.objects.latest('id')
                JobApplied.objects.filter(job=instance).update(is_modified=True)
                if remove_image_ids:
                    for id in remove_image_ids:
                        JobAttachments.objects.filter(id=id).delete()
                if image:
                    image_error = validate_job_attachments(image)
                    if image_error != 0:
                        return Response({'message': "Invalid Job Attachments images"},
                                        status=status.HTTP_400_BAD_REQUEST)
                    for i in image:
                        JobAttachments.objects.create(job=instance, job_images=i)
                    dam_images_list(dam_images, job_id)
                    dam_sample_images_list(dam_sample_images, job_id)
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
                            for i in template_image:
                                JobTemplateAttachments.objects.create(job_template=Job_template_id,
                                                                      job_template_images=i)
                        if sample_image:
                            sample_image_error = validate_job_attachments(sample_image)
                            if sample_image_error != 0:
                                return Response({'message': "Invalid Job Attachments images"},
                                                status=status.HTTP_400_BAD_REQUEST)
                            for i in templte_sample_image:
                                JobTemplateAttachments.objects.create(job_template=Job_template_id,
                                                                      work_sample_images=i)

                user_list = JobApplied.objects.filter(Q(job=instance) & Q(status=0))
                for users in user_list:
                    from_email = Email(SEND_GRID_FROM_EMAIL)
                    to_email = To(users.user.email)
                    skills = ''
                    for i in users.job.skills.all():
                        skills += f'<div><button style="background-color:rgba(36,114,252,.08);border-radius:30px;font-style:normal;font-weight:600;font-size:15px;line-height:18px;text-align:center;border:none;color:#2472fc;padding:8px 20px 8px 20px">{i.skill_name}</button></div>'
                    try:
                        subject = "Job Edited"
                        content = Content("text/html",
                                          f'<div style="background: rgba(36, 114, 252, 0.06) !important"><table style="font: Arial, sans-serif;border-collapse: collapse;width: 600px;margin: 0 auto;" width="600" cellpadding="0" cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 0"><div style="padding: 34px 44px; border-radius: 8px !important;background: #fff;border: 1px solid #dddddd5e;margin-bottom: 50px;margin-top: 50px;"><div class="email-logo"><img style="width: 165px"src="{LOGO_122_SERVER_PATH}"/></div><a href="#"></a><div class="welcome-text"style="padding-top: 80px"><h1 style="font: 24px">Hello {users.user.get_full_name()},</h1></div><div class="welcome-paragraph"><div style="padding: 10px 0px;font-size: 16px;color: #384860;">There has been update to your job:</div><div style="border-radius: 0px 8px 8px 0;margin-top: 10px;display: flex;"><div style="width: 13px;max-width: 5px;min-width: 5px;background-color: #2472fc;border-radius: 50px;"></div><div><div style="padding: 20px"><div><h1 style="font: 24px">{users.job.title}</h1></div><div style="padding: 13px 0px;font-size: 16px;color: #384860;">{users.job.description}</div><div><button style="background-color: rgba(36,114,252,0.08);border-radius: 30px;font-style: normal;font-weight: 600;font-size: 15px;line-height: 18px;text-align: center;border: none;color: #2472fc;padding: 8px 20px 8px 20px;">{users.get_status_display()}</button></div><div style="font-size: 16px;line-height: 19px;color: rgba(0, 0, 0, 0.7);font-weight: bold;padding: 15px 0px;">Due on:<span style="padding: 0px 12px">{users.job.job_due_date}</span></div><div style="display: flex">{skills}</div></div></div></div><div style="padding: 10px 0px;font-size: 16px;color: #384860;">Please click the link below to view the new updates.</div><div style= "padding: 20px 0px;font-size: 16px; color: #384860;"></div>Sincerely,<br />The Adifect Team</div><div style="padding-top: 40px"><a href="{FRONTEND_SITE_URL}/jobs/details/{users.job.id}"<button style="height: 56px;padding: 15px 44px;background: #2472fc;border-radius: 8px;border-style: none;color: white;font-size: 16px;">View Job Update</button></a></div><div style="padding: 50px 0px"class="email-bottom-para"><div style="padding: 20px 0px;font-size: 16px;color: #384860;">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect? <a href="#"><span style="text-decoration: underline">Unsubscribe.</span></a></div><div style="font-size: 16px; color: #384860">© 2022 Adifect</div></div></div></td></tr></tbody></table></div>')
                        data = send_email(from_email, to_email, subject, content)
                    except Exception as e:
                        print(e)
                # --------------------------------------- end -----------------------------------------------#

                context = {
                    'message': 'Updated Successfully',
                    'status': status.HTTP_200_OK,
                    'errors': serializer.errors,
                    'data': serializer.data,
                }
                return Response(context)
            else:
                context = {
                    'message': 'You cannot update the job',
                    'errors': serializer.errors,
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



@permission_classes([IsAdminMember | IsMarketerMember])
class MemberJobTemplatesViewSet(viewsets.ModelViewSet):
    serializer_class = JobTemplateSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    queryset = JobTemplate.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['company']
    search_fields = ['=company', ]

    # pagination_class = FiveRecordsPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        job_data = queryset.order_by('-modified')
        serializer = JobTemplateWithAttachmentsSerializer(job_data, many=True, context={'request': request})
        return Response(data=serializer.data)

    def retrieve(self, request, pk=None):
        id = pk
        if id is not None:
            job_data = JobTemplate.objects.get(id=id)
            serializer = JobTemplateWithAttachmentsSerializer(job_data, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        image = request.FILES.getlist('image')
        sample_image = request.FILES.getlist('sample_image')
        remove_image_ids = request.data.getlist('remove_image', None)
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        dam_images = request.data.getlist('dam_images')
        dam_sample_work = request.data.getlist('dam_sample_work')

        if serializer.is_valid():
            template_name = serializer.validated_data.get('template_name', None)
            job_template_id = JobTemplate.objects.latest('id')
            if template_name:
                if JobTemplate.objects.filter(
                        ~Q(pk=instance.pk) & Q(template_name=template_name) & Q(is_trashed=False)).exclude(
                    template_name=None).exists():
                    context = {
                        'message': 'Job Template Already Exist',
                        'status': status.HTTP_400_BAD_REQUEST,
                        'errors': serializer.errors,
                        'data': serializer.data,
                    }
                    return Response(context, status=status.HTTP_400_BAD_REQUEST)
            self.perform_update(serializer)
            update_job_template = Job.objects.filter(template_name=template_name).update(template_name=template_name)
            # ------- ----- -- -- --- -- task -- --- -- --- ----  --- ----#
            if request.data.get('tasks', None):
                for i in json.loads(request.data['tasks']):
                    name = i['title']
                    if name:
                        if 'id' in i:
                            JobTemplateTasks.objects.filter(id=i['id']).update(title=i['title'],
                                                                               due_date=i['due_date'])
                        else:
                            JobTemplateTasks.objects.create(job_template=instance, title=name, due_date=i['due_date'])
            # ------ --- -- - --- ---- end ---  --- -- - --- ---  ----  --#

            if remove_image_ids:
                for id in remove_image_ids:
                    JobTemplateAttachments.objects.filter(id=id).delete()
            if image:
                image_error = validate_job_attachments(image)
                if image_error != 0:
                    return Response({'message': "Invalid Job Attachments images"}, status=status.HTTP_400_BAD_REQUEST)
                for i in image:
                    JobTemplateAttachments.objects.create(job_template=instance, job_template_images=i)
            dam_images_templates(dam_images, job_template_id)
            dam_sample_template_images_list(dam_sample_work, job_template_id)

            if sample_image:
                sample_image_error = validate_job_attachments(sample_image)
                if sample_image_error != 0:
                    return Response({'message': "Invalid Job Attachments images"},
                                    status=status.HTTP_400_BAD_REQUEST)
                for i in sample_image:
                    JobTemplateAttachments.objects.create(job_template=instance, work_sample_images=i)
            context = {
                'message': 'Updated Succesfully',
                'status': status.HTTP_200_OK,
                'errors': serializer.errors,
                'data': serializer.data,
            }
            return Response(context)
        context = {
            'message': 'Something Went Wrong',
            'status': status.HTTP_400_BAD_REQUEST,
            'errors': serializer.errors,
            'data': serializer.data,
        }
        return Response(context)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        for i in JobTemplateAttachments.objects.filter(job_template=instance):
            i.delete()
        update_job_template = Job.objects.filter(template_name=instance.template_name).update(template_name=None,
                                                                                              status=2)
        self.perform_destroy(instance)
        context = {
            'message': 'Deleted Succesfully',
            'status': status.HTTP_204_NO_CONTENT,
            'errors': False,
        }
        return Response(context)


@permission_classes([IsAdminMember])
class MemberInviteMemberUserList(APIView):
    serializer_class = InviteMemberSerializer

    def get(self, request, *args, **kwargs):
        company_id = request.GET.get('company', None)
        level = request.GET.get('level', None)
        agency = request.user
        if level == '3':
            invited_user = InviteMember.objects.filter(company=company_id,is_blocked=False, status=1,
                                                       user__user__isnull=False, user__levels=3)
        else:
            invited_user = InviteMember.objects.filter(company=company_id,is_blocked=False, status=1,
                                                       user__user__isnull=False)
        if company_id:
            invited_user = invited_user.filter(Q(company_id=company_id) | Q(user__user=agency))
        serializer = self.serializer_class(invited_user, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

@permission_classes([IsAdminMember | IsMarketerMember])
class DraftJobViewSet(viewsets.ModelViewSet):
    serializer_class = JobsWithAttachmentsSerializer
    queryset = Job.objects.filter(status=0).order_by('-modified')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['company']
    search_fields = ['=company']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
class MemberDAMViewSet(viewsets.ModelViewSet):
    serializer_class = DAMSerializer
    queryset = DAM.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['id', 'parent', 'type', 'name', 'is_favourite', 'is_video', 'agency','company']
    search_fields = ['name']

    def list(self, request, *args, **kwargs):
        parent=request.GET.get('parent',None)
        if parent:
            queryset = self.filter_queryset(self.get_queryset()).filter(agency=request.user)
        else:
            print('dddddddddddddddddddddddddddddddddddddddd')
            queryset = self.filter_queryset(self.get_queryset()).filter(Q(parent=None)| Q(parent=False))
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
                                                agency=serializer.validated_data['agency'])
                    DamMedia.objects.create(dam=dam_id, title=dam_name[index], media=i)
            # elif serializer.validated_data['type']==1:
            #     print("yesssssssssssssssssss")
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
        partial = kwargs.pop('partial', False)
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
                for i in DamMedia.objects.filter(id__in=order_list):
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
class MemberDamRootViewSet(viewsets.ModelViewSet):
    serializer_class = DAMSerializer
    queryset = DAM.objects.filter(Q(parent=None) | Q(parent=False))
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['id', 'parent', 'type', 'agency','company']
    search_fields = ['name']
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        # user = request.user
        queryset = self.filter_queryset(self.get_queryset())
        serializer = DamWithMediaRootSerializer(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)


@permission_classes([IsAuthenticated])
class MemberDamMediaViewSet(viewsets.ModelViewSet):
    serializer_class = DamMediaSerializer
    queryset = DamMedia.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['modified', 'created', 'limit_used']
    ordering = ['modified', 'created', 'limit_used']
    filterset_fields = ['dam_id', 'title', 'id', 'image_favourite', 'is_video','dam__agency','dam__company','dam__parent']
    search_fields = ['title', 'tags', 'skills__skill_name', 'dam__name']
    http_method_names = ['get', 'put', 'delete', 'post']

    def list(self, request, *args, **kwargs):
        dam__parent = request.GET.get('dam__parent', None)
        if dam__parent:
            queryset = self.filter_queryset(self.get_queryset()).filter(dam__agency=request.user.id).exclude(dam__type=2)
        else:
            queryset = self.filter_queryset(self.get_queryset()).filter(dam__parent=None).exclude(dam__type=2)
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

    @action(methods=['get'], detail=False, url_path='latest_records', url_name='latest_records')
    def latest_records(self, request, *args, **kwargs):
        if request.GET.get('dam__company'):
            queryset = self.filter_queryset(self.get_queryset()).filter(Q(dam__company=request.GET.get('dam__company')) &
                (Q(dam__parent__is_trashed=False) | Q(dam__parent__isnull=True))).order_by(
                '-created')[:4]

        if request.GET.get('dam__agency'):
            queryset = self.filter_queryset(self.get_queryset()).filter(Q(dam__agency=request.GET.get('dam__agency')) &
                (Q(dam__parent__is_trashed=False) | Q(dam__parent__isnull=True))).order_by(
                '-created')[:4]
        else:
             queryset = self.filter_queryset(self.get_queryset()).filter(
            Q(dam__parent__is_trashed=False) | Q(dam__parent__isnull=True)).order_by(
            '-created')[:4]
        serializer = DamMediaSerializer(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)

    @action(methods=['post'], detail=False, url_path='move_collection', url_name='move_collection')
    def move_collection(self, request, *args, **kwargs):
        data = request.POST.get('dam_images', None)
        dam_intial = 0
        for i in data.split(','):
            print(request.data)
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
class MemberDamDuplicateViewSet(viewsets.ModelViewSet):
    serializer_class = DAMSerializer
    queryset = DAM.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['id', 'parent', 'type','agency','company']
    search_fields = ['=name']
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        # user = request.user
        if request.GET.get('root'):
            queryset = self.filter_queryset(self.get_queryset()).filter(parent=None)
        else:
            queryset = self.filter_queryset(self.get_queryset()).filter(agency=request.user)
        serializer = DamWithMediaSerializer(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)


@permission_classes([IsAuthenticated])
class MemberDamMediaFilterViewSet(viewsets.ModelViewSet):
    serializer_class = DamMediaSerializer
    queryset = DamMedia.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['modified', 'created', 'limit_used']
    ordering = ['modified', 'created']
    filterset_fields = ['dam_id', 'title', 'id','dam__agency','dam__company']
    search_fields = ['title']

    @action(methods=['get'], detail=False, url_path='favourites', url_name='favourites')
    def favourites(self, request, pk=None, *args, **kwargs):
        id = request.GET.get('id', None)
        user_id = request.GET.get('id', None)
        if id:
            fav_folder = DAM.objects.filter(type=1, agency=user_id, is_favourite=True, parent=id)
            fav_folder_data = DamWithMediaSerializer(fav_folder, many=True, context={'request': request})
            fav_collection = DamMedia.objects.filter(dam__parent=id, image_favourite=True, dam__agency=user_id)
            fav_collection_data = DamWithMediaSerializer(fav_collection, many=True, context={'request': request})
            fav_images = DAM.objects.filter(parent=id, type=3, agency=user_id, is_favourite=True)
            fav_images_data = DamWithMediaSerializer(fav_images, many=True, context={'request': request})
        else:
            fav_folder = DAM.objects.filter(type=1, agency=user_id, is_favourite=True)
            fav_folder_data = DamWithMediaSerializer(fav_folder, many=True, context={'request': request})
            fav_collection = DamMedia.objects.filter(dam__parent=id, image_favourite=True, dam__agency=user_id)
            fav_collection_data = DamWithMediaSerializer(fav_collection, many=True, context={'request': request})
            fav_images = DAM.objects.filter(type=3, agency=user_id, is_favourite=True, )
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
        user_id = request.GET.get('user_id', None)
        company_id = request.GET.get('company_id', None)
        dam_data = DAM.objects.filter()
        dammedia_data = DamMedia.objects.filter()                                    
        if company_id:
            dam_data = dam_data.filter(company=company_id)
            dammedia_data = dammedia_data.filter(dam__company=company_id)
                                       
        if id:
            fav_folder = dam_data.filter(agency=user_id, is_favourite=True, parent=id,
                                            is_trashed=False).count()
            total_image = dammedia_data.filter(dam__type=3, dam__agency=user_id, dam__parent=id,
                                                  is_trashed=False, is_video=False).count()
            total_video = dammedia_data.filter(dam__type=3, dam__agency=user_id, dam__parent=id,
                                                  is_trashed=False, is_video=True).count()
            total_collection = dam_data.filter(type=2, agency=user_id, parent=id, is_trashed=False).count()
            total_folder = dam_data.filter(type=1,agency=user_id,parent=id,is_trashed=False).count()

        else:
            fav_folder = dam_data.filter(agency=user_id, is_favourite=True, parent__isnull=True).count()
            total_image = dammedia_data.filter(dam__type=3, dam__agency=user_id, is_trashed=False,
                                                  is_video=False, dam__parent__isnull=True).count()
            total_collection = dam_data.filter(type=2, agency=user_id,parent__isnull=True).count()
            total_video = dammedia_data.filter(dam__type=3, dam__agency=user_id, is_trashed=False,
                                                  is_video=True, dam__parent__isnull=True).count()
            total_folder = dam_data.filter(type=1, agency=user_id,parent__isnull=True).count()

        context = {'fav_folder': fav_folder,
                   'total_image': total_image,
                   'total_collection': total_collection,
                   'total_video': total_video,
                   'total_folder':total_folder,
                   }
        return Response(context, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
class MemberDAMFilter(viewsets.ModelViewSet):
    serializer_class = DAMSerializer
    queryset = DAM.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['created', 'dam_media__job_count']
    ordering = ['created', 'dam_media__job_count']
    filterset_fields = ['id', 'parent', 'type', 'name', 'is_video', 'is_favourite','agency','company']
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
        photo = None
        video = None
        collection = None
        folder = None
        if photos:
            data = self.filter_queryset(self.get_queryset()).filter(type=3, is_video=False,
                                                                    is_trashed=False)
            photos_data = DamWithMediaSerializer(data, many=True, context={'request': request})
            photo = photos_data.data
        if videos:
            data = self.filter_queryset(self.get_queryset()).filter(type=3, is_video=True,
                                                                    is_trashed=False)
            videos_data = DamWithMediaSerializer(data, many=True, context={'request': request})
            video = videos_data.data
        if collections:
            data = set(self.filter_queryset(self.get_queryset()).filter(type=2,
                                                                        is_trashed=False).values_list('pk', flat=True))
            collections = set(list(data))
            filter_data = DAM.objects.filter(id__in=data)
            collections_data = DamWithMediaSerializer(filter_data, many=True, context={'request': request})
            collection = collections_data.data
        if folders:
            data = self.filter_queryset(self.get_queryset()).filter(type=1,
                                                                    is_trashed=False)
            folders_data = DamWithMediaSerializer(data, many=True, context={'request': request})
            folder = folders_data.data

        if not photos and not videos and not collections:
            data1 = self.filter_queryset(self.get_queryset()).filter(type=3, is_video=False,
                                                                     is_trashed=False)
            photos_data = DamWithMediaSerializer(data1, many=True, context={'request': request})
            photo = photos_data.data
            data2 = self.filter_queryset(self.get_queryset()).filter(type=3, is_video=True,
                                                                     is_trashed=False)
            videos_data = DamWithMediaSerializer(data2, many=True, context={'request': request})
            video = videos_data.data
            data = set(self.filter_queryset(self.get_queryset()).filter(type=2,
                                                                        is_trashed=False).values_list('pk', flat=True))
            filter_data = DAM.objects.filter(id__in=data)
            collections_data = DamWithMediaSerializer(filter_data, many=True, context={'request': request})
            collection = collections_data.data
            data4 = self.filter_queryset(self.get_queryset()).filter(type=1,
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



class MemberCollectionDAMFilter(viewsets.ModelViewSet):
    serializer_class = DAMSerializer
    queryset = DamMedia.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['created', 'job_count']
    ordering = ['created', 'job_count']
    filterset_fields = ['dam_id', 'is_video','image_favourite']
    search_fields = ['dam__name','title']

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
                data = self.filter_queryset(self.get_queryset()).filter(
                                                                        is_video=False,
                                                                        is_trashed=False)
                photos_data = DamMediaSerializer(data, many=True, context={'request': request})
                photo = photos_data.data
        if videos:
                data = self.filter_queryset(self.get_queryset()).filter(is_video=True,
                                                                        is_trashed=False)
                videos_data = DamMediaSerializer(data, many=True, context={'request': request})
                video = videos_data.data

        

        if not photos and not videos:
            data1 = self.filter_queryset(self.get_queryset()).filter(is_video=False,
                                                                     is_trashed=False)
            photos_data = DamMediaSerializer(data1, many=True, context={'request': request})
            photo = photos_data.data
            data2 = self.filter_queryset(self.get_queryset()).filter(is_video=True,
                                                                     is_trashed=False)
            videos_data = DamMediaSerializer(data2, many=True, context={'request': request})
            video = videos_data.data
        
        context = {
            'photos': photo,
            'videos': video,
        }
        return Response(context, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
class JobAttachmentsView(APIView):

    def get(self, request, *args, **kwargs):
        job = request.GET.get('job', None)
        level = request.GET.get('level', None)
        user = request.GET.get('user', None)
        job_attachments = JobAttachments.objects.filter(job=job, job__user_id=user)
        job_attachments_data = JobAttachmentsSerializer(job_attachments, many=True, context={'request': request})
        job_activity = JobActivityAttachments.objects.filter(job_activity_chat__job_activity__job=job,
                                                             job_activity_chat__job_activity__job__user_id=user)
        job_activity_attachments = JobActivityAttachmentsSerializer(job_activity, many=True,
                                                                    context={'request': request})
        job_work_approved = JobWorkActivityAttachments.objects.filter(work_activity__work_activity="approved",work_activity__job_activity_chat__job=job,
                                                             work_activity__job_activity_chat__job__user_id=user)
        job_work_approved_attachments = JobWorkActivityAttachmentsSerializer(job_work_approved, many=True, context={'request': request})
        job_work_rejected = JobWorkActivityAttachments.objects.filter(work_activity__work_activity="rejected",work_activity__job_activity_chat__job=job,
                                                             work_activity__job_activity_chat__job__user_id=user)
        job_work_rejected_attachments = JobWorkActivityAttachmentsSerializer(job_work_rejected, many=True, context={'request': request})
        job_applied = JobAppliedAttachments.objects.filter(job_applied__job=job, job_applied__job__user_id=user)
        job_applied_attachments = JobAppliedAttachmentsSerializer(job_applied, many=True, context={'request': request})
        context = {
            'job_attachments': job_attachments_data.data,
            'job_activity_attachments': job_activity_attachments.data,
            'approved_job_work_attachments': job_work_approved_attachments.data,
            'rejected_job_work_attachments': job_work_rejected_attachments.data,
            'job_applied_attachments': job_applied_attachments.data,
        }
        return Response(context, status=status.HTTP_200_OK)


class JobHouseMember(viewsets.ModelViewSet):
    serializer_class = JobsWithAttachmentsThumbnailSerializer
    queryset = Job.objects.filter(is_trashed=False,is_house_member=True)
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter ]
    ordering_fields = ['created', 'modified', 'job_due_date','job__created']
    ordering = ['created', 'modified', 'job_due_date','job__created']
    filterset_fields = ['id', 'is_active','job_applied__status','job_applied__user','company']
    search_fields = ['company__name', 'title', 'description', 'tags', 'skills__skill_name']
    pagination_class = FiveRecordsPagination
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        
        job_data = self.filter_queryset(self.get_queryset()).filter(house_member__user__user=request.user).distinct()
        paginated_data = self.paginate_queryset(job_data)
        serializer = self.serializer_class(paginated_data, many=True, context={'request': request})
        return self.get_paginated_response(data=serializer.data)

    def retrieve(self, request,*args, **kwargs):
        obj = self.get_object()
        serializer = JobsWithAttachmentsSerializer(obj, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

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
        job_work_approved = JobWorkActivityAttachments.objects.filter(work_activity__work_activity="approved",work_activity__job_activity_chat__job=job,
                                                             work_activity__job_activity_chat__job__user=request.user)
        job_work_approved_attachments = JobWorkActivityAttachmentsSerializer(job_work_approved, many=True, context={'request': request})
        job_work_rejected = JobWorkActivityAttachments.objects.filter(work_activity__work_activity="rejected",work_activity__job_activity_chat__job=job,
                                                             work_activity__job_activity_chat__job__user=request.user)
        job_work_rejected_attachments = JobWorkActivityAttachmentsSerializer(job_work_rejected, many=True, context={'request': request})
        job_applied = JobAppliedAttachments.objects.filter(job_applied__job=job, job_applied__job__user=request.user)
        job_applied_attachments = JobAppliedAttachmentsSerializer(job_applied, many=True, context={'request': request})
        final_approved_data = JobWorkAttachments.objects.filter(job_work__job_applied__job=job,job_work__job_applied__job__user=request.user,job_work__status=1)
        final_approved = JobWorkAttachmentsSerializer(final_approved_data,many=True,context={'request': request})
        context = {
            'job_attachments': job_attachments_data.data,
            'job_activity_attachments': job_activity_attachments.data,
            'approved_job_work_attachments': job_work_approved_attachments.data,
            'rejected_job_work_attachments': job_work_rejected_attachments.data,
            'job_applied_attachments': job_applied_attachments.data,
            'final_approved_data':final_approved.data
        }
        return Response(context, status=status.HTTP_200_OK)


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

        company_data = Company.objects.filter(invite_company_list__user__user=request.user,is_active=True)
        if id:
            parent = id
        else:
            parent = None
        q_photos = Q()
        if photos:
            print('hiiiiiiiiiiiiiiii')
            q_photos = Q(Q(type=3) & Q(is_video=False))
            print(q_photos)
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
            company_count = DAM.objects.filter((q_photos | q_videos | q_collections | q_folders)).filter((Q(q_favourites & q_photos)| (Q(q_favourites & q_videos)) | (Q(q_favourites & q_collections)) | (Q(q_favourites & q_photos & q_videos))) & (Q(company=i) & Q(parent=parent))).count()
            result.append({f'name':{i.name},'id':{i.id},'count':company_count})

        context = {
            'company_data': result,
            'status': status.HTTP_200_OK,
        }
        return Response(context, status=status.HTTP_200_OK)

    
        # id = request.GET.get('id', None)
        # user_id = request.GET.get('user_id', None)
        # if id:
        #     company_count = Company.objects.filter(agency=user_id,dam_company__parent=id)
        #     initial_count = company_count.values_list('id',flat=True)
        #     company_count = company_count.values('dam_company__company','name','id','is_active').order_by().annotate(Count('dam_company__company'))

        #     # null_company_count = company_count = Company.objects.filter(Q(agency=request.user) & (Q(dam_company__parent=id) | Q(dam_company__parent=None))).values('dam_company__company','name','id','is_active').order_by().annotate(Count('dam_company__company'))
        #     null_company_count = Company.objects.filter(agency=user_id , dam_company__parent=None).exclude(id__in=list(initial_count)).values('dam_company__company','name','id','is_active').distinct('pk')
        #     context = {
        #     'company_count': company_count,
        #     'null_company_count': null_company_count,
        #     }
        #     return Response(context, status=status.HTTP_200_OK)
        # else:
        #     company_initial = Company.objects.filter(agency=request.user, dam_company__parent=None)
        #     company_count = company_initial.values('dam_company__company', 'name', 'id',
        #                                            'is_active').order_by().annotate(Count('dam_company__company'))
        #     null_company_count = Company.objects.filter(agency=request.user).exclude(
        #         id__in=list(company_initial.values_list('id', flat=True))).values('dam_company__company', 'name', 'id',
        #                                                                           'is_active').distinct('pk')
        #     context = {
        #         'company_count': company_count,
        #         'null_company_count': null_company_count,
        #     }
        #     return Response(context, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
class CompanyCountView(APIView):

    def get(self, request, *args, **kwargs):
        id = request.GET.get('id', None)
        company = request.GET.get('company', None)
        user_id = request.GET.get('user_id', None)
        if id and company:
            order_list = company.split(",")
            fav_folder = DAM.objects.filter(agency=user_id, is_favourite=True, company__in=order_list, parent=id,
                                            is_trashed=False).count()
            print(fav_folder)
            total_image = DamMedia.objects.filter(dam__type=3, dam__agency=user_id, dam__company__in=order_list,
                                                  dam__parent=id,
                                                  is_trashed=False, is_video=False).count()
            total_video = DamMedia.objects.filter(dam__type=3, dam__agency=user_id, dam__company__in=order_list,
                                                  dam__parent=id,
                                                  is_trashed=False, is_video=True).count()
            print(total_image)
            total_collection = DAM.objects.filter(type=2, agency=user_id, company__in=order_list, parent=id,
                                                  is_trashed=False).count()
        if company and not id:
            order_list = company.split(",")
            fav_folder = DAM.objects.filter(agency=user_id, parent__isnull=True, is_favourite=True,
                                            company__in=order_list,
                                            is_trashed=False).count()
            total_image = DamMedia.objects.filter(dam__type=3, dam__parent__isnull=True, dam__agency=user_id,
                                                  dam__company__in=order_list,
                                                  is_trashed=False, is_video=False).count()
            total_video = DamMedia.objects.filter(dam__type=3, dam__parent__isnull=True, dam__agency=user_id,
                                                  dam__company__in=order_list,
                                                  is_trashed=False, is_video=True).count()
            total_collection = DAM.objects.filter(type=2, parent__isnull=True, agency=user_id, company__in=order_list,
                                                  is_trashed=False).count()
            context = {'fav_folder': fav_folder,
                       'total_image': total_image,
                       'total_collection': total_collection,
                       'total_video': total_video,
                       'status': status.HTTP_201_CREATED,
                       }
            return Response(context)
        return Response({"message":"Please add company id"},status=status.HTTP_200_OK)




class MemberNotificationViewset(viewsets.ModelViewSet):
    serializer_class = NotificationsSerializer
    queryset = Notifications.objects.all()
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['user', 'is_seen','company']


    def list(self, request, *args, **kwargs):
        today = datetime.now().date()
        queryset = self.filter_queryset(self.get_queryset())
        queryset_today =queryset.filter(created__date=today).values()
        queryset_earlier = queryset.exclude(created__date=today).values()
        offset =int(request.GET.get('offset', default=0))
        count= queryset.filter(is_seen=False).count()
        if offset:
                queryset = queryset[0:offset]
        else:
             queryset = queryset[0:5]

        serializer = self.serializer_class(queryset, many=True, context={request: 'request'})
        context = {'data': serializer.data, 'count':count,'today':queryset_today,'earlier':queryset_earlier}
        return Response(context)


    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        if serializer.is_valid(raise_exception=True):
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

    # @action(methods=['get'], detail=False, url_path='favourites', url_name='favourites')
    # def favourites(self, request, pk=None, *args, **kwargs):
    #     id = request.GET.get('id', None)
    #     company = request.GET.get('company', None)
    #     user_id = request.GET.get('user_id', None)
    #     if id:
    #         fav_folder = DAM.objects.filter(type=1, agency=user_id, is_favourite=True, parent=id)
    #         fav_folder_data = DamWithMediaSerializer(fav_folder, many=True, context={'request': request})
    #         fav_collection = DamMedia.objects.filter(dam__parent=id, image_favourite=True, dam__agency=user_id)
    #         fav_collection_data = DamWithMediaSerializer(fav_collection, many=True, context={'request': request})
    #         fav_images = DAM.objects.filter(parent=id, type=3, agency=user_id, is_favourite=True)
    #         fav_images_data = DamWithMediaSerializer(fav_images, many=True, context={'request': request})
    #     else:
    #         fav_folder = DAM.objects.filter(type=1, agency=user_id, is_favourite=True)
    #         fav_folder_data = DamWithMediaSerializer(fav_folder, many=True, context={'request': request})
    #         fav_collection = DamMedia.objects.filter(dam__parent=id, image_favourite=True, dam__agency=user_id)
    #         fav_collection_data = DamWithMediaSerializer(fav_collection, many=True, context={'request': request})
    #         fav_images = DAM.objects.filter(type=3, agency=user_id, is_favourite=True, )
    #         fav_images_data = DamWithMediaSerializer(fav_images, many=True, context={'request': request})

    #     context = {
    #         'fav_folder': fav_folder_data.data,
    #         'fav_collection': fav_collection_data.data,
    #         'fav_images': fav_images_data.data
    #     }
    #     return Response(context, status=status.HTTP_200_OK)




@permission_classes([IsAuthenticated])
class MyJobsViewSet(viewsets.ModelViewSet):
    # serializer_class = JobAppliedSerializer
    queryset = JobApplied.objects.filter(is_trashed=False, job__is_trashed=False).exclude(status=1).exclude(job=None)
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['modified', 'job__job_due_date', 'job__created', 'job__modified', 'created']
    ordering = ['job__job_due_date', 'job__created', 'job__modified', 'modified', 'created']
    filterset_fields = ['status', 'job__company']
    search_fields = ['status', 'job__tags', 'job__skills__skill_name', 'job__description', 'job__title']
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

class CollectionCount(ReadOnlyModelViewSet):
    queryset = DamMedia.objects.all()
    def list(self, request, *args, **kwargs):
        id = request.GET.get('id',None)
        agency = request.GET.get('agency',None)
        favourite = self.queryset.filter(dam__agency=agency, image_favourite=True, dam=id).count()
        images = self.queryset.filter(dam__agency=agency, is_video=False, dam=id).count()
        videos = self.queryset.filter(dam__agency=agency, is_video=True, dam=id).count()

        context = {'favourites': favourite,
                   'images': images,
                   'videos': videos,
                   }
        return Response(context)


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