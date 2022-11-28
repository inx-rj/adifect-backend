from django.shortcuts import render
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import permission_classes
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated

from administrator.models import JobApplied, JobActivity, Job, MemberApprovals, JobAttachments, JobTemplateAttachments, JobTasks, JobTemplate, JobTemplateTasks
from administrator.pagination import FiveRecordsPagination
from administrator.serializers import JobAppliedSerializer, JobActivitySerializer, JobsWithAttachmentsSerializer, JobSerializer, JobTemplateAttachmentsSerializer, JobsWithAttachmentsThumbnailSerializer,  JobTemplateSerializer,  JobTemplateSerializer, JobTemplateWithAttachmentsSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from agency.models import Workflow_Stages, InviteMember, Company,WorksFlow
from authentication.manager import IsAdminMember, IsMarketerMember, IsApproverMember
from agency.serializers import InviteMemberSerializer,CompanySerializer,WorksFlowSerializer, MyProjectSerializer, StageSerializer
from django.db.models import Subquery
from rest_framework.decorators import action
from administrator.views  import validate_job_attachments, dam_images_templates, dam_sample_template_images_list
import json
from sendgrid.helpers.mail import Mail, Email, To, Content
from adifect.settings import SEND_GRID_API_key, FRONTEND_SITE_URL, LOGO_122_SERVER_PATH, BACKEND_SITE_URL, \
    TWILIO_NUMBER, TWILIO_NUMBER_WHATSAPP, SEND_GRID_FROM_EMAIL
from helper.helper import StringEncoder, send_text_message, send_skype_message, send_email, send_whatsapp_message
from django.db.models import Subquery, Q



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


@permission_classes([IsAuthenticated])
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


@permission_classes([IsAdminMember | IsApproverMember | IsMarketerMember])
class InviteUserCompanyListViewSet(viewsets.ModelViewSet):
    serializer_class = InviteMemberSerializer
    queryset = InviteMember.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).filter(user__user=request.user).values('company','company__name','agency')
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


@permission_classes([IsApproverMember | IsAdminMember])
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



@permission_classes([IsAdminMember])
class WorksFlowViewSet(viewsets.ModelViewSet):
    serializer_class = WorksFlowSerializer
    queryset = WorksFlow.objects.filter(is_trashed=False).order_by('-modified')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['company', 'is_blocked','agency']
    search_fields = ['=company']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)
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
                                                    workflow=workflow_latest, order=i['order'],approval_time=i['approval_time'])
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
                                                                is_all_approval=i['is_all_approval'],approval_time=i['approval_time'])
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
                                                              is_all_approval=i['is_all_approval'], order=i['order'],approval_time=i['approval_time'])
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


@permission_classes([IsAdminMember])
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



@permission_classes([IsAdminMember])
class MemberMyProjectViewSet(viewsets.ModelViewSet):
    serializer_class = MyProjectSerializer
    queryset = JobApplied.objects.filter(job__is_trashed=False).exclude(job=None)
    filter_backends = [DjangoFilterBackend, SearchFilter, ]
    filterset_fields = ['job', 'status', 'job__company', 'job__is_active']
    ordering_fields = ['modified', 'job__job_due_date', 'job__created', 'job__modified', 'created']
    ordering = ['job__job_due_date', 'job__created', 'job__modified', 'modified', 'created']
    search_fields = ['=status', ]
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
                                                                    agency__is_account_closed=False).order_by(
            '-modified').exclude(user__user=self.request.user)
        serializer = InviteMemberSerializer(queryset, many=True)
        return Response(serializer.data)

@permission_classes([IsAdminMember])
class JobViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    queryset = Job.objects.all()
    job_template_attach = JobTemplateAttachmentsSerializer
    filterset_fields = ['company','is_active','status']
    pagination_class = FiveRecordsPagination

    def list(self, request, *args, **kwargs):
        user_role = request.user.role
        if user_role == 0:
            job_data = self.queryset.filter(user=request.user).exclude(status=0).order_by('-modified')
        else:
            job_data = self.queryset.exclude(status=0).exclude(is_active=0).order_by('-modified')
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



@permission_classes([IsAdminMember])
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
        if level == '3':
            invited_user = InviteMember.objects.filter(company=company_id,is_blocked=False, status=1,
                                                       user__user__isnull=False, user__levels=3)
        else:
            invited_user = InviteMember.objects.filter(company=company_id,is_blocked=False, status=1,
                                                       user__user__isnull=False)
        if company_id:
            invited_user = invited_user.filter(company_id=company_id)
        serializer = self.serializer_class(invited_user, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

