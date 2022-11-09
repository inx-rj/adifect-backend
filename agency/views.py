from django.shortcuts import render
from rest_framework.response import Response
from administrator.models import Job, JobAttachments, JobApplied
from administrator.serializers import JobSerializer, JobsWithAttachmentsSerializer
from rest_framework import status
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from authentication.models import CustomUser
from authentication.serializers import UserSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter,OrderingFilter
from administrator.pagination import FiveRecordsPagination
from django.db.models import Q
from django.db.models import Count, Avg
from rest_framework import generics

from .models import InviteMember, WorksFlow, Workflow_Stages, Industry, Company, DAM, DamMedia, AgencyLevel, TestModal
from .serializers import InviteMemberSerializer, \
    InviteMemberRegisterSerializer, WorksFlowSerializer, StageSerializer, IndustrySerializer, CompanySerializer, DAMSerializer, DamMediaSerializer, DamWithMediaSerializer,MyProjectSerializer,TestModalSerializer, DamWithMediaRootSerializer, DamWithMediaThumbnailSerializer, DamMediaThumbnailSerializer
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from adifect.settings import SEND_GRID_API_key, FRONTEND_SITE_URL, LOGO_122_SERVER_PATH, BACKEND_SITE_URL, TWILIO_NUMBER,TWILIO_NUMBER_WHATSAPP,SEND_GRID_FROM_EMAIL
from helper.helper import StringEncoder, send_text_message, send_skype_message, send_email,send_whatsapp_message
from django.db.models import Count
from django.db.models import Subquery
import base64


# Create your views here.
@permission_classes([IsAuthenticated])
class IndustryViewSet(viewsets.ModelViewSet):
    serializer_class = IndustrySerializer
    queryset = Industry.objects.all().order_by('-modified')


@permission_classes([IsAuthenticated])
class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    queryset = Company.objects.all().order_by('-modified')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_active', 'agency', 'is_blocked']
    search_fields = ['=is_active']

    def get_queryset(self):
        user = self.request.user
        queryset = Company.objects.filter(agency=user, agency__is_account_closed=False).order_by('-modified')
        return queryset

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.serializer_class(instance)
        if not data['is_assigned_workflow'].value:
            self.perform_destroy(instance)
            context = {
                'message': 'Deleted Succesfully',
                'status': status.HTTP_204_NO_CONTENT,
                'errors': False,
            }
        else:
            context = {
                'message': 'This company is assigned to a workflow, so cannot be deleted!',
                'status': status.HTTP_400_BAD_REQUEST,
                'errors': True,
            }
        return Response(context)



@permission_classes([IsAuthenticated])
class AgencyJobsViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    queryset = Job.objects.filter(is_trashed=False).exclude(status=0)
    pagination_class = FiveRecordsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['company']
    search_fields = ['=company', '=name']

    def list(self, request, *args, **kwargs):
        job_data = self.filter_queryset(self.get_queryset()).filter(user=request.user, is_active=True,
                                                                    user__is_account_closed=False).order_by("-modified")
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
            job_data = Job.objects.filter(id=id,user=request.user).first()
            if job_data:
                serializer = JobsWithAttachmentsSerializer(job_data,context={'request': request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response({'message':'No Data Found','error':True}, status=status.HTTP_204_NO_CONTENT)


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
                        i.limit_usage+=1
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
        unapplied_jobs = Job.objects.filter(user=request.user.id, status=0, is_trashed=False)
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
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['company', 'is_blocked']
    search_fields = ['=company']

    def list(self, request, *args, **kwargs):
        user = self.request.user
        queryset = self.filter_queryset(self.get_queryset())
        workflow_data = queryset.filter(agency=user, agency__is_account_closed=False)
        serializer = self.serializer_class(workflow_data, many=True, context={'request': request})
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
                                                    is_observer=i['is_observer'],is_all_approval=i['is_all_approval'],
                                                    workflow=workflow_latest,order=i['order'])
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
                                                                workflow=instance,order=i['order'],is_all_approval=i['is_all_approval'])
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
                                                              is_observer=i['is_observer'],is_all_approval=i['is_all_approval'],order=i['order'])
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
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['company']
    search_fields = ['=company']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).filter(agency=request.user, is_trashed=False, user__isnull=False, agency__is_account_closed=False).order_by('-modified')
        serializer = InviteMemberSerializer(queryset, many=True)
        return Response(serializer.data)

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
            invite = InviteMember.objects.filter(user__user__email=email, agency=agency,company=company).first()
            if not invite:
                invite =  InviteMember.objects.filter(email=email,agency=agency,company=company).first()
            if not user:
                email_decode = StringEncoder.encode(self, email)
                if not invite:
                    agency_level = AgencyLevel.objects.create(levels=levels)
                    invite = InviteMember.objects.create(agency=agency,email=email,user=agency_level, status=0, company=company)
                    # invite_id = invite.pk
                decodeId = StringEncoder.encode(self, invite.user.id)
                try:
                    subject = "Invitation link to Join Team"
                    content = Content("text/html",
                                      f'<div style="background: rgba(36, 114, 252, 0.06) !important"><table style="font: Arial, sans-serif;border-collapse: collapse;width: 600px;margin: 0 auto;"width="600"cellpadding="0"cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 0"><div style="padding: 34px 44px;border-radius: 8px !important;background: #fff;border: 1px solid #dddddd5e;margin-bottom: 50px;margin-top: 50px;"><div class="email-logo"><img style="width: 165px"src="{LOGO_122_SERVER_PATH}"/></div><a href="#"></a><div class="welcome-text"style="padding-top: 80px"><h1 style="font: 24px">Hello,</h1></div><div class="welcome-paragraph"><div style="padding: 10px 0px;font-size: 16px;color: #384860;">You have been invited to join Adifect! for <b>{invite.user.get_levels_display()}</b> Please click the link below to<br />create your account.</div><div style="padding: 20px 0px;font-size: 16px;color: #384860;">Sincerely,<br />The Adifect Team</div></div><div style="padding-top: 40px"class="create-new-account"><a href="{FRONTEND_SITE_URL}/signup-invite/{decodeId}/{exclusive_decode}/{email_decode}"><button style="height: 56px;padding: 15px 44px;background: #2472fc;border-radius: 8px;border-style: none;color: white;font-size: 16px;">Create New Account</button></a></div><div style="padding: 50px 0px"class="email-bottom-para"><div style="padding: 20px 0px;font-size: 16px;color: #384860;">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect? <a href="#"><span style="text-decoration: underline">Unsubscribe.</span></a></div><div style="font-size: 16px; color: #384860">© 2022 Adifect</div></div></div></td></tr></tbody</table></div>')
                    data = send_email(from_email, to_email, subject, content)
                    if data:
                        return Response({'message': 'mail Send successfully, Please check your mail'},
                                        status=status.HTTP_200_OK)
                    else:
                        return Response({'message': 'You are not authorized to send invitation.'}, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    print(e)
                    return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            if user:
                if not invite:
                    agency_level = AgencyLevel.objects.create(user=user, levels=levels)
                    invite = InviteMember.objects.create(user=agency_level, agency=agency, status=0, company=company)
                    # invite = InviteMember.objects.latest('id')

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
                        subject = "Invitation link to Join Team"
                        content = Content("text/html",
                                          f'<div style="background: rgba(36, 114, 252, 0.06) !important"><table style="font: Arial, sans-serif;border-collapse: collapse;width: 600px;margin: 0 auto;"width="600" cellpadding="0" cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 0"><div style="padding: 34px 44px;border-radius: 8px !important;background: #fff;border: 1px solid #dddddd5e;margin-bottom: 50px;margin-top: 50px;"><div class="email-logo"><img style="width: 165px"src="{LOGO_122_SERVER_PATH}"/></div><a href="#"></a><div class="welcome-text" style="padding-top: 80px"><h1 style="font:24px;color: #000;">Hello, {user.first_name} {user.last_name}</h1></div><div class="welcome-paragraph"><div style="padding: 10px 0px;font-size: 16px;color: #384860;">You have been invited to join Adifect! for <b>{invite.user.get_levels_display()}</b> Please click the  below links.</div><div style="padding: 20px 0px;font-size: 16px color: #384860;">Sincerely,<br />The Adifect Team</div></div><div style="display: flex"><div style="padding-top: 40px; width: 50%"class="create-new-account"><a href={BACKEND_SITE_URL}/agency/update-invite-member/{decodeId}/{accept_invite_encode}/{exclusive_decode}><button style="height: 56px;cursor: pointer;padding: 15px 44px;background: #2472fc;border-radius: 8px;border-style: none;color: white;font-size: 16px;width: 90%;cursor: pointer;">Accept</button></a></div><div style="padding-top: 40px; width: 50%"class="create-new-account"><a href={BACKEND_SITE_URL}/agency/update-invite-member/{decodeId}/{reject_invite_encode}/{exclusive_decode}><button style="height: 56px;padding: 15px 44px;background: #2472fc;border-radius: 8px;border-style: none;color: white;font-size: 16px;width: 90%;cursor: pointer;">Reject</button></a></div></div><div style="padding: 50px 0px"class="email-bottom-para"><div style="padding: 20px 0px;font-size: 16px;color: #384860;">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect? <a href="#"><span style="text-decoration: underline"> Unsubscribe.</span></a></div><div style="font-size: 16px; color: #384860">© 2022 Adifect </div></div></div></td></tr></tbody></table></div>')

                        data = send_email(from_email, to_email, subject, content)
                        if data:
                            return Response({'message': 'mail Send successfully, Please check your mail'},
                                            status=status.HTTP_200_OK)
                        else:
                            return Response({'message': 'You are not authorized to send invitation.'}, status=status.HTTP_400_BAD_REQUEST)

                    except Exception as e:
                        print(e)
                        return Response({'message': str(e)})
            return Response({'message': 'success'},
                            status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        level = request.data.get('levels',None)
        if level:
            is_update = AgencyLevel.objects.filter(id=instance.user.id).update(levels=int(level))
            if is_update:
                context = {
                    'message': 'Updated Successfully...',
                    'status': status.HTTP_200_OK,
                }
                return Response(context)
        else:
            return Response({'message': 'something went wrong','error':True}, status=status.HTTP_400_BAD_REQUEST)


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
        instance = self.get_object()
        self.perform_destroy(instance)

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
        if id and status:
            data = InviteMember.objects.filter(pk=encoded_id, is_trashed=False)
            if data and exculsive:
                user = CustomUser.objects.filter(pk=data.first().user.id, is_trashed=False).update(
                    is_exclusive=encoded_exculsive)
            update = data.update(status=encoded_status)
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
                # To get user id and update the invite table
                id = kwargs.get('invite_id', None)
                encoded_id = int(StringEncoder.decode(self, id))
                user_id = CustomUser.objects.latest('id')
                agency_level = AgencyLevel.objects.filter(pk=encoded_id, is_trashed=False).update(user=user)
                invite = InviteMember.objects.filter(user_id=encoded_id).update(status=1)


                return Response({'message': 'User Registered Successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({'message': f'{e} is required'}, status=status.HTTP_400_BAD_REQUEST)

@permission_classes([IsAuthenticated])
class InviteMemberUserList(APIView):
    serializer_class = InviteMemberSerializer

    def get(self, request, *args, **kwargs):
        company_id = kwargs.get('company_id', None)
        agency = request.user
        if agency.is_authenticated:
            invited_user = InviteMember.objects.filter(agency=agency, is_blocked=False, status=1, user__isnull=False)
            if company_id:
                invited_user = invited_user.filter(company_id=company_id)
            serializer = self.serializer_class(invited_user, many=True, context={'request': request})
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(data={'error': 'You Are Not Authorized'}, status=status.HTTP_400_BAD_REQUEST)


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
            order_list = request.data.get('order_list',None)
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


def copy_media_logic(id,parent_id=None):
    # try:
        if id:
            dam_old = DAM.objects.filter(pk=id).first()
            dam_old.pk = None
            dam_old.parent_id = parent_id
            dam_new = dam_old.save()
            new_id = None
            print(id)
            for j in DAM.objects.filter(parent=id,type=3):
                for i in DamMedia.objects.filter(dam=j):
                    i.pk = None
                    i.dam = dam_new
                    i.save()
            for k in  DAM.objects.filter(parent=id,type=2):
                for i in DamMedia.objects.filter(dam=k):
                    i.pk = None
                    i.dam = dam_new
                    i.save()
            for l in DAM.objects.filter(parent=id,type=1):
                return copy_media_logic(l.id, dam_new.id)
            return True
    # except Exception as e:
    #     print(e)
    #     return False





@permission_classes([IsAuthenticated])
class DAMViewSet(viewsets.ModelViewSet):
    serializer_class = DAMSerializer
    queryset = DAM.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter,OrderingFilter]
    ordering_fields = ['modified','created']
    ordering = ['modified','created']
    filterset_fields = ['id','parent','type','name']
    search_fields = ['name']


    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).filter(agency=request.user)
        serializer = DamWithMediaThumbnailSerializer(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)

    def retrieve(self, request, pk=None):
        id = pk
        if id is not None:
            dam_data = self.queryset.get(id=pk)
            serializer = DamWithMediaSerializer(dam_data, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        dam_files = request.FILES.getlist('dam_files',None)
        dam_name = request.POST.getlist('dam_files_name',None)
        if serializer.is_valid():
            if serializer.validated_data['type']==3:
                for index,i in enumerate(dam_files):
                    # self.perform_create(serializer)
                    dam_id = DAM.objects.create(type=3,parent=serializer.validated_data.get('parent',None)  ,agency=serializer.validated_data['agency'])
                    DamMedia.objects.create(dam=dam_id,title=dam_name[index],media=i)
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
                for index,i in enumerate(dam_files):
                    DamMedia.objects.create(dam=dam_id,title=dam_name[index],media=i)
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
            #--- image copy from one folder to another -----#
            if type_id == 3 and type_new == 3:
                dam_media_inital = DamMedia.objects.filter(id=request.data.get('id')).first()
                if dam_media_inital:
                    dam_intial = dam_media_inital.dam
                    dam_intial.pk=None
                    dam_intial.parent = parent                                                                                                                      
                    dam_intial.type = type_new                  
                    dam_intial.save()
                    dam_media_inital.pk=None
                    dam_media_inital.dam=dam_intial
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
            if (type_id==2 and type_new ==2) or(type_id==3 and type_new ==2) :
                dam_media_inital = DamMedia.objects.filter(id=request.data.get('id')).first()
                dam_media_inital.pk=None
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
            if  type_id==2 and type_new == 3:
                dam_new = DAM.objects.create(type=3,parent=parent,agency=request.user)
                dam_media = DamMedia.objects.filter(id=id).first()
                dam_media.pk=None
                dam_media.dam=dam_new
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

                DamMedia.objects.create(dam=dam_id, media=dam_inital.media, title=dam_inital.title, description=dam_inital.description)
                dam_inital.delete()
                if dam_files:
                    for index,i in enumerate(dam_files):
                        DamMedia.objects.create(dam=dam_id,title=dam_name[index],media=i)


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
        new_title = request.data.get('new_title',None)
        dam_data=DamMedia.objects.filter(id=pk).update(title=new_title)
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
    queryset = DAM.objects.filter(parent=None)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['id', 'parent','type']
    search_fields = ['name']
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        user = request.user
        queryset = self.filter_queryset(self.get_queryset()).filter(agency=request.user)
        serializer = DamWithMediaRootSerializer(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)


@permission_classes([IsAuthenticated])
class DamMediaViewSet(viewsets.ModelViewSet):
    serializer_class = DamMediaSerializer
    queryset = DamMedia.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['dam_id', 'title','id']
    search_fields = ['title']
    http_method_names = ['get','put','delete','post']

    @action(methods=['get'], detail=False, url_path='get_multiple', url_name='get_multiple')
    def get_multiple(self, request, *args, **kwargs):
        try:
            id_list = request.GET.get('id', None)
            order_list = id_list.split(",")
            if order_list:
                data = DamMedia.objects.filter(id__in=order_list)
                serializer_data = self.serializer_class(data,many=True,context={'request':request})
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
            return Response(context,status=status.HTTP_400_BAD_REQUEST)


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
        queryset =DamMedia.objects.filter(Q(dam__agency=request.user) & (Q(dam__parent__is_trashed=False)|Q(dam__parent__isnull=True))).order_by('-created')[:4]
        serializer = DamMediaThumbnailSerializer(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)

    @action(methods=['post'], detail=False, url_path='move_collection', url_name='move_collection')
    def move_collection(self, request, *args, **kwargs):
        data = request.POST.get('dam_images', None)
        dam_intial = 0
        for i in data.split(','):
           print(request.data)
           if not request.data.get('parent',None) == 'null':
                dam_id =  DAM.objects.create(type=3,parent_id=request.data.get('parent',None),agency_id=request.data.get('user'))
                dam_media = DamMedia.objects.filter(pk=i).update(dam=dam_id)
                dam_intial += 1
           else:
                dam_id =  DAM.objects.create(type=3,agency_id=request.data.get('user'))
                dam_media = DamMedia.objects.filter(pk=i).update(dam=dam_id)
                dam_intial += 1
           if dam_intial:
            context = {
                'message': 'Media Uploaded Successfully',
                'status': status.HTTP_201_CREATED,
            }
            return Response(context)
           return Response({"message":"Unable to move"},status=status.HTTP_404_NOT_FOUND)

@permission_classes([IsAuthenticated])
class DamDuplicateViewSet(viewsets.ModelViewSet):
    serializer_class = DAMSerializer
    queryset = DAM.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['id','parent','type']
    search_fields = ['=name']
    http_method_names = ['get']


    def list(self, request, *args, **kwargs):
        user = request.user
        if request.GET.get('root'):
             queryset = self.filter_queryset(self.get_queryset()).filter(agency=request.user,parent=None)
        else:     
            queryset = self.filter_queryset(self.get_queryset()).filter(agency=request.user)
        serializer = DamWithMediaSerializer(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)

@permission_classes([IsAuthenticated])
class DraftJobViewSet(viewsets.ModelViewSet):
    serializer_class = JobsWithAttachmentsSerializer
    queryset = Job.objects.filter(status=0).order_by('-modified')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['company']
    search_fields = ['=company']


    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        draft_data = queryset.filter(user=request.user)
        serializer = self.serializer_class(draft_data, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)
        
class MemberJobListViewSet(viewsets.ModelViewSet):
    serializer_class = JobsWithAttachmentsSerializer
    queryset = Workflow_Stages.objects.all()

    def list(self, request, *args, **kwargs):
        user = request.user
        workflow_id = self.queryset.filter(approvals__user__user=user,workflow__is_trashed=False,workflow__isnull=False,is_trashed=False).values_list('workflow_id', flat=True)
        print(workflow_id)
        job_data = Job.objects.filter(workflow_id__in=list(workflow_id))
        serializer = self.serializer_class(job_data, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)



# --      --   --         --     --    my project --   --       --      --        -- #

@permission_classes([IsAuthenticated])
class MyProjectViewSet(viewsets.ModelViewSet):
    serializer_class = MyProjectSerializer
    queryset = JobApplied.objects.filter(job__is_trashed=False).exclude(job=None)
    filter_backends = [DjangoFilterBackend,SearchFilter]
    ordering_fields = ['modified','job__job_due_date','job__created','job__modified','created']
    ordering = ['job__job_due_date','job__created','job__modified','modified','created']
    filterset_fields = ['status','job__company']
    search_fields = ['=status',]
    pagination_class = FiveRecordsPagination
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        user = request.user
        queryset = self.filter_queryset(self.get_queryset())
        ordering = request.GET.get('ordering',None)
        filter_data =queryset.filter(
            pk__in=Subquery(
                queryset.filter(job__user=user,job__is_active=True).order_by('job_id').distinct('job_id').values('pk')
            )
        ).order_by(ordering)
        paginated_data = self.paginate_queryset(filter_data)
        serializer = self.serializer_class(paginated_data, many=True, context={'request': request})
        return self.get_paginated_response(data=serializer.data)


@permission_classes([IsAuthenticated])
class TestModalViewSet(viewsets.ModelViewSet):
    serializer_class = TestModalSerializer
    queryset = TestModal.objects.all()


@permission_classes([IsAuthenticated])
class DAMMediaCount(APIView):
    def get(self, request, *args, **kwargs):
        user= request.user
        fav_folder = DAM.objects.filter(type=1,agency=user,is_favourite=True).count()
        total_image = DAM.objects.filter(type=3,agency=user).count()
        total_collection =  DAM.objects.filter(type=2,agency=user).count()
        context = {'fav_folder':fav_folder,
                'total_image':total_image,
                'total_collection':total_collection
                

        }
        return Response(context,status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        records_count = DAM.objects.filter(parent=request.data['parent'],agency=request.user).count()
        context = {'message':"Folder's count get successfull",
                'count':records_count,
        }
        return Response(context,status=status.HTTP_200_OK)

@permission_classes([IsAuthenticated])
class DamMediaFilterViewSet(viewsets.ModelViewSet):
    serializer_class = DamMediaSerializer
    queryset = DamMedia.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['dam_id', 'title','id']
    search_fields = ['title']
    http_method_names = ['get','put','delete','post']


    @action(methods=['get'], detail=False, url_path='favourites', url_name='favourites')
    def favourites(self, request,pk=None, *args, **kwargs):
         id = request.GET.get('id', None)
         if id:
            print("iffffffffffffffffffffffffffffff")
            fav_folder = DAM.objects.filter(type=1,agency=request.user,is_favourite=True,parent=id)
            fav_folder_data = DamWithMediaThumbnailSerializer(fav_folder,many=True,context={'request':request})
            fav_collection = DamMedia.objects.filter(dam__parent=id,image_favourite=True,dam__agency=request.user)
            fav_collection_data = DamMediaThumbnailSerializer(fav_collection,many=True,context={'request':request})
            fav_images = DAM.objects.filter(parent=id,type=3,agency=request.user,is_favourite=True)
            fav_images_data = DamWithMediaThumbnailSerializer(fav_images,many=True,context={'request':request})
         else:
            print("elseeeeeeeeeeeeeeeeeeeeeeeeee")
            fav_folder = DAM.objects.filter(type=1,agency=request.user,is_favourite=True,parent=id)
            fav_folder_data = DamWithMediaThumbnailSerializer(fav_folder,many=True,context={'request':request})
            fav_collection = DamMedia.objects.filter(dam__parent=id,image_favourite=True,dam__agency=request.user)
            fav_collection_data = DamMediaThumbnailSerializer(fav_collection,many=True,context={'request':request})
            fav_images = DAM.objects.filter(parent=id,type=3,agency=request.user,is_favourite=True)
            fav_images_data = DamWithMediaThumbnailSerializer(fav_images,many=True,context={'request':request})
            
         context = {
            'fav_folder':fav_folder_data.data,
            'fav_collection':fav_collection_data.data,
            'fav_images':fav_images_data.data
            }
         return Response(context,status=status.HTTP_200_OK)



