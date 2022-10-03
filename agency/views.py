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
from rest_framework.filters import SearchFilter
from administrator.pagination import FiveRecordsPagination
from django.db.models import Q
from django.db.models import Count, Avg
from rest_framework import generics

from .models import InviteMember, WorksFlow, Workflow_Stages, Industry, Company, DAM, DamMedia , TestModal
from .serializers import InviteMemberSerializer, \
    InviteMemberRegisterSerializer, WorksFlowSerializer, StageSerializer, IndustrySerializer, CompanySerializer, DAMSerializer, DamMediaSerializer, DamWithMediaSerializer, TestModalSerializer
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from adifect.settings import SEND_GRID_API_key, FRONTEND_SITE_URL, LOGO_122_SERVER_PATH, BACKEND_SITE_URL, TWILIO_NUMBER,TWILIO_NUMBER_WHATSAPP,SEND_GRID_FROM_EMAIL
from helper.helper import StringEncoder, send_text_message, send_skype_message, send_email,send_whatsapp_message

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
    filterset_fields = ['is_active']
    search_fields = ['=is_active']

    def get_queryset(self):
        user = self.request.user
        queryset = Company.objects.filter(agency=user).order_by('-modified')
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


    # def list(self, request, *args, **kwargs):
    #     company = self.queryset.filter(agency=request.user).order_by("-modified")
    #
    #     serializer = CompanySerializer(company, many=True, context={'request': request})
    #     return  Response(data=serializer.data)

@permission_classes([IsAuthenticated])
class AgencyJobsViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    queryset = Job.objects.filter(is_trashed=False).exclude(status=0)
    pagination_class = FiveRecordsPagination

    def list(self, request, *args, **kwargs):
        job_data = self.queryset.filter(user=request.user.id).order_by("-modified")
        paginated_data = self.paginate_queryset(job_data)
        serializer = JobsWithAttachmentsSerializer(paginated_data, many=True, context={'request': request})
        return self.get_paginated_response(data=serializer.data)

    def retrieve(self, request, pk=None):
        id = pk
        if id is not None:
            job_data = Job.objects.get(id=id)
            serializer = JobsWithAttachmentsSerializer(job_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def create(self, request, *args, **kwargs):
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
    filterset_fields = ['company']
    search_fields = ['=company']

    def list(self, request, *args, **kwargs):
        user = self.request.user
        queryset = self.filter_queryset(self.get_queryset())
        workflow_data = queryset.filter(agency=user)
        serializer = self.serializer_class(workflow_data, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    # def list(self, request, *args, **kwargs):
    #     workflow_data = self.queryset.filter(agency=request.user.id).order_by("-modified")
    #     serializer = self.serializer_class(workflow_data, many=True, context={'request': request})
    #     return Response(data=serializer.data)

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


'''
@permission_classes([IsAuthenticated])
class InviteMemberApi(APIView):
    serializer_class = InviteMemberSerializer

    def get(self, request, *args, **kwargs):
        queryset = InviteMember.objects.filter(is_trashed=False)
        serializer = InviteMemberSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data['email']
            message = serializer.validated_data['message']
            level = serializer.validated_data['level']
            exclusive = serializer.validated_data['exclusive']
            user = CustomUser.objects.filter(email=email,is_trashed=False).first()
            agency = CustomUser.objects.filter(pk=serializer.validated_data['agency'].id,is_trashed=False).first()
            if not agency:
                return Response({'message': 'Agency does not exists', 'error': True},
                                status=status.HTTP_400_BAD_REQUEST)
            if user:
                if user.is_exclusive:
                    return Response({'message': 'User Is Exculsive', 'error': True},
                                    status=status.HTTP_400_BAD_REQUEST)
            if exclusive:
                exclusive_decode = StringEncoder.encode(self, 1)
            else:
                exclusive_decode = StringEncoder.encode(self, 0)

            sg = sendgrid.SendGridAPIClient(api_key=SEND_GRID_API_key)
            from_email = Email("no-reply@sndright.com")
            to_email = To(email)
            invite = InviteMember.objects.filter(user__email=email, agency=agency,is_trashed=False).first()
            if not user:
                if not invite:
                    invite = InviteMember.objects.create(agency=agency, status=0)
                    invite_id = InviteMember.objects.latest('id').pk
                    decodeId = StringEncoder.encode(self, invite_id)
                try:
                    subject = "Invitation link to Join Team"
                    content = Content("text/html",
                                      f'<div style=" background: rgba(36,114,252,0.06)!important;"><table style="font:Arial,sans-serif;border-collapse:collapse;width:600px; margin: 0 auto; " width="600" cellpadding="0" cellspacing="0"><tbody style = "width: 100%; float: left; text-align: center;"><tr style = "width: 100%;float: left; text-align: center;"><td style = "width: 100%;float: left; text-align: center;margin: 36px 0 0;"><div class ="email-logo"><img src="{LOGO_122_SERVER_PATH}" style="height: auto;width: 189px;"/></div><div style="margin-top:20px;padding:25px;border-radius:8px!important;background: #fff;border:1px solid #dddddd5e;margin-bottom: 50px;"><h1 style="font-family: arial;font-size: 26px !important;font-weight: bold !important;line-height: inherit !important;margin: 0;color: #000;"> Welcome to Adifect </h1><a href = "#"></a><h1 style = "color: #222222;font-size: 16px;font-weight: 600;line-height: 16px; font-family: arial;" > </h1><p style = "font-size: 16px;font-family: arial;margin: 35px 0 35px;line-height: 24px;color: #000;" > Hi, <b>hii User</b> <br> {message} </p><p style = "font-size: 16px; font-family: arial; margin: 25px 0 54px;line-height: 24px; color: #000;" > {level} </p><a href = {BACKEND_SITE_URL}/agency/register-view-invite/{decodeId}/{exclusive_decode} style = "padding: 16px 19px;border-radius: 4px; text-decoration: none;color: #fff;font-size: 12px; font-weight: bold; text-transform: uppercase; font-family: arial; background: #2472fc;"> Accept Invite </a></a><p style = "font-size: 14px;font-family: arial;margin: 45px 0 10px;" > Contact us: 1-800-123-45-67 I mailto:info@adifect.com </p></div></td></tr></tbody></table></div>')
                    mail = Mail(from_email, to_email, subject, content)
                    mail_json = mail.get()
                    response = sg.client.mail.send.post(request_body=mail_json)
                except Exception as e:
                    print(e)
            if user:
                if not invite:
                    invite = InviteMember.objects.create(user=user, agency=agency, status=0)
                    invite = InviteMember.objects.latest('id')
                decodeId = StringEncoder.encode(self, invite.id)
                accept_invite_status = 1
                accept_invite_encode = StringEncoder.encode(self, accept_invite_status)
                reject_invite_status = 2
                reject_invite_encode = StringEncoder.encode(self, reject_invite_status)

                try:
                    subject = "Invitation link to Join Team"
                    content = Content("text/html",
                                      f'<div style=" background: rgba(36,114,252,0.06)!important;"><table style="font:Arial,sans-serif;border-collapse:collapse;width:600px; margin: 0 auto; " width="600" cellpadding="0" cellspacing="0"><tbody style = "width: 100%; float: left; text-align: center;"><tr style = "width: 100%;float: left; text-align: center;"><td style = "width: 100%;float: left; text-align: center;margin: 36px 0 0;"><div class ="email-logo"><img src="{LOGO_122_SERVER_PATH}" style="height: auto;width: 189px;"/></div><div style="margin-top:20px;padding:25px;border-radius:8px!important;background: #fff;border:1px solid #dddddd5e;margin-bottom: 50px;"><h1 style="font-family: arial;font-size: 26px !important;font-weight: bold !important;line-height: inherit !important;margin: 0;color: #000;"> Welcome to Adifect </h1><a href = "#"></a><h1 style = "color: #222222;font-size: 16px;font-weight: 600;line-height: 16px; font-family: arial;" > </h1><p style = "font-size: 16px;font-family: arial;margin: 35px 0 35px;line-height: 24px;color: #000;" > Hi, <b>{user.first_name} {user.last_name}</b> <br> {message} </p><p style = "font-size: 16px; font-family: arial; margin: 25px 0 54px;line-height: 24px; color: #000;" > {level} </p><a href = {BACKEND_SITE_URL}/agency/update-invite-member/{decodeId}/{accept_invite_encode}/{exclusive_decode} style = "padding: 16px 19px;border-radius: 4px; text-decoration: none;color: #fff;font-size: 12px; font-weight: bold; text-transform: uppercase; font-family: arial; background: #2472fc;"> Accepted </a></a><a href = {BACKEND_SITE_URL}/agency/update-invite-member/{decodeId}/{reject_invite_encode}/{exclusive_decode} style = "padding: 16px 19px;border-radius: 4px; text-decoration: none;color: #fff;font-size: 12px; font-weight: bold; text-transform: uppercase; font-family: arial; background: #2472fc;"> Rejected </a><p style = "font-size: 14px;font-family: arial;margin: 45px 0 10px;" > Contact us: 1-800-123-45-67 I mailto:info@adifect.com </p></div></td></tr></tbody></table></div>')
                    mail = Mail(from_email, to_email, subject, content)
                    mail_json = mail.get()
                    response = sg.client.mail.send.post(request_body=mail_json)
                except Exception as e:
                    print(e)
            return Response({'message': 'mail Send successfully, Please check your mail'},
                            status=status.HTTP_200_OK)

'''
class InviteMemberViewSet(viewsets.ModelViewSet):
    serializer_class = InviteMemberSerializer
    queryset = InviteMember.objects.all().order_by('-modified')

    def list(self, request, *args, **kwargs):
        queryset = InviteMember.objects.filter(agency=request.user, is_trashed=False, user__isnull=False).order_by('-modified')
        serializer = InviteMemberSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data.get('email',None)
            exclusive = serializer.validated_data.get('exclusive',None)
            company = serializer.validated_data.get('company',None)
            user = CustomUser.objects.filter(email=email, is_trashed=False).first()
            agency = CustomUser.objects.filter(pk=serializer.validated_data['agency'].id, is_trashed=False).first()
            if not agency:
                return Response({'message': 'Agency does not exists', 'error': True},
                                status=status.HTTP_400_BAD_REQUEST)
            if user:
                if user.role == 2:
                    return Response({'message': "You Can't Invite Agency Directly", 'error': True,'status':status.HTTP_400_BAD_REQUEST},
                                    status=status.HTTP_400_BAD_REQUEST)

                if user.is_exclusive:
                    return Response({'message': 'User Is Exculsive', 'error': True},
                                    status=status.HTTP_400_BAD_REQUEST)
            if exclusive:
                exclusive_decode = StringEncoder.encode(self, 1)
            else:
                exclusive_decode = StringEncoder.encode(self, 0)
            from_email = Email(SEND_GRID_FROM_EMAIL)
            to_email = To(email)
            invite = InviteMember.objects.filter(user__email=email, agency=agency, is_trashed=False, company=company).first()
            if not user:
                email_decode = StringEncoder.encode(self, email)
                if not invite:
                    invite = InviteMember.objects.create(agency=agency, status=0, company=company)
                    invite_id = InviteMember.objects.latest('id').pk
                    decodeId = StringEncoder.encode(self, invite_id)
                try:
                    subject = "Invitation link to Join Team"
                    content = Content("text/html",
                                      f'<div style="background: rgba(36, 114, 252, 0.06) !important"><table style="font: Arial, sans-serif;border-collapse: collapse;width: 600px;margin: 0 auto;"width="600"cellpadding="0"cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 0"><div style="padding: 34px 44px;border-radius: 8px !important;background: #fff;border: 1px solid #dddddd5e;margin-bottom: 50px;margin-top: 50px;"><div class="email-logo"><img style="width: 165px"src="{LOGO_122_SERVER_PATH}"/></div><a href="#"></a><div class="welcome-text"style="padding-top: 80px"><h1 style="font: 24px">Hello,</h1></div><div class="welcome-paragraph"><div style="padding: 10px 0px;font-size: 16px;color: #384860;">You have been invited to join Adifect! Please click the link below to<br />create your account.</div><div style="padding: 20px 0px;font-size: 16px;color: #384860;">Sincerely,<br />The Adifect Team</div></div><div style="padding-top: 40px"class="create-new-account"><a href="{FRONTEND_SITE_URL}/signup-invite/{decodeId}/{exclusive_decode}/{email_decode}"><button style="height: 56px;padding: 15px 44px;background: #2472fc;border-radius: 8px;border-style: none;color: white;font-size: 16px;">Create New Account</button></a></div><div style="padding: 50px 0px"class="email-bottom-para"><div style="padding: 20px 0px;font-size: 16px;color: #384860;">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect?<a href="#"><span style="text-decoration: underline"> Unsubscribe.</span></a></div><div style="font-size: 16px; color: #384860">© 2022 Adifect</div></div></div></td></tr></tbody</table></div>')
                    data = send_email(from_email, to_email, subject, content)
                    if data:
                        return Response({'message': 'mail Send successfully, Please check your mail'},
                                        status=status.HTTP_200_OK)
                    else:
                        return Response({'message': 'Something Went Wrong'}, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    print(e)
                    return Response({'message': 'Something Went Wrong'}, status=status.HTTP_400_BAD_REQUEST)
            if user:
                if not invite:
                    invite = InviteMember.objects.create(user=user, agency=agency, status=0, company=company)
                    invite = InviteMember.objects.latest('id')
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
                                          f'<div style="background: rgba(36, 114, 252, 0.06) !important"><table style="font: Arial, sans-serif;border-collapse: collapse;width: 600px;margin: 0 auto;"width="600" cellpadding="0" cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 0"><div style="padding: 34px 44px;border-radius: 8px !important;background: #fff;border: 1px solid #dddddd5e;margin-bottom: 50px;margin-top: 50px;"><div class="email-logo"><img style="width: 165px"src="{LOGO_122_SERVER_PATH}"/></div><a href="#"></a><div class="welcome-text" style="padding-top: 80px"><h1 style="font:24px;color: #000;">Hello, {user.first_name} {user.last_name}</h1></div><div class="welcome-paragraph"><div style="padding: 10px 0px;font-size: 16px;color: #384860;">You have been invited to join Adifect! Please click the  below links.</div><div style="padding: 20px 0px;font-size: 16px color: #384860;">Sincerely,<br />The Adifect Team</div></div><div style="display: flex"><div style="padding-top: 40px; width: 50%"class="create-new-account"><a href={BACKEND_SITE_URL}/agency/update-invite-member/{decodeId}/{accept_invite_encode}/{exclusive_decode}><button style="height: 56px;cursor: pointer;padding: 15px 44px;background: #2472fc;border-radius: 8px;border-style: none;color: white;font-size: 16px;width: 90%;cursor: pointer;">Accept</button></a></div><div style="padding-top: 40px; width: 50%"class="create-new-account"><a href={BACKEND_SITE_URL}/agency/update-invite-member/{decodeId}/{reject_invite_encode}/{exclusive_decode}><button style="height: 56px;padding: 15px 44px;background: #2472fc;border-radius: 8px;border-style: none;color: white;font-size: 16px;width: 90%;cursor: pointer;">Reject</button></a></div></div><div style="padding: 50px 0px"class="email-bottom-para"><div style="padding: 20px 0px;font-size: 16px;color: #384860;">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect? <a href="#"><span style="text-decoration: underline"> Unsubscribe.</span></a></div><div style="font-size: 16px; color: #384860">© 2022 Adifect </div></div></div></td></tr></tbody></table></div>')

                        data = send_email(from_email, to_email, subject, content)
                        if data:
                            return Response({'message': 'mail Send successfully, Please check your mail'},
                                            status=status.HTTP_200_OK)
                        else:
                            return Response({'message': 'Something Went Wrong'}, status=status.HTTP_400_BAD_REQUEST)

                    except Exception as e:
                        print(e)
                        return Response({'message': 'Something Went Wrong'})
            return Response({'message': 'success'},
                            status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)

        context = {
            'message': 'Deleted Succesfully',
            'status': status.HTTP_204_NO_CONTENT,
            'errors': False,
        }
        return Response(context)

# @permission_classes([IsAuthenticated])
# class InviteMemberApi(APIView):
#     serializer_class = InviteMemberSerializer

#     def get(self, request, *args, **kwargs):
#         queryset = InviteMember.objects.filter(is_trashed=False,user__isnull=False)
#         serializer = InviteMemberSerializer(queryset, many=True)
#         return Response(serializer.data)

#     def post(self, request, *args, **kwargs):
#         serializer = self.serializer_class(data=request.data)
#         if serializer.is_valid(raise_exception=True):
#             email = serializer.validated_data['email']
#             exclusive = serializer.validated_data['exclusive']
#             user = CustomUser.objects.filter(email=email, is_trashed=False).first()
#             agency = CustomUser.objects.filter(pk=serializer.validated_data['agency'].id, is_trashed=False).first()
#             if not agency:
#                 return Response({'message': 'Agency does not exists', 'error': True},
#                                 status=status.HTTP_400_BAD_REQUEST)
#             if user:
#                 if user.is_exclusive:
#                     return Response({'message': 'User Is Exculsive', 'error': True},
#                                     status=status.HTTP_400_BAD_REQUEST)
#             if exclusive:
#                 exclusive_decode = StringEncoder.encode(self, 1)
#             else:
#                 exclusive_decode = StringEncoder.encode(self, 0)
#             from_email = Email(SEND_GRID_FROM_EMAIL)
#             to_email = To(email)
#             invite = InviteMember.objects.filter(user__email=email, agency=agency, is_trashed=False).first()
#             if not user:
#                 if not invite:
#                     invite = InviteMember.objects.create(agency=agency, status=0)
#                     invite_id = InviteMember.objects.latest('id').pk
#                     decodeId = StringEncoder.encode(self, invite_id)
#                 try:
#                     subject = "Invitation link to Join Team"
#                     content = Content("text/html",
#                                       f'<div style="background: rgba(36, 114, 252, 0.06) !important"><table style="font: Arial, sans-serif;border-collapse: collapse;width: 600px;margin: 0 auto;"width="600"cellpadding="0"cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 0"><div style="padding: 34px 44px;border-radius: 8px !important;background: #fff;border: 1px solid #dddddd5e;margin-bottom: 50px;margin-top: 50px;"><div class="email-logo"><img style="width: 165px"src="{LOGO_122_SERVER_PATH}"/></div><a href="#"></a><div class="welcome-text"style="padding-top: 80px"><h1 style="font: 24px">Hello,</h1></div><div class="welcome-paragraph"><div style="padding: 10px 0px;font-size: 16px;color: #384860;">You have been invited to join Adifect!Please click the link below to<br />create your account.</div><div style="padding: 20px 0px;font-size: 16px;color: #384860;">Sincerely,<br />The Adifect Team</div></div><div style="padding-top: 40px"class="create-new-account"><a href="{BACKEND_SITE_URL}/agency/register-view-invite/{decodeId}/{exclusive_decode}"><button style="height: 56px;padding: 15px 44px;background: #2472fc;border-radius: 8px;border-style: none;color: white;font-size: 16px;">Create New Account</button></a></div><div style="padding: 50px 0px"class="email-bottom-para"><div style="padding: 20px 0px;font-size: 16px;color: #384860;">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect?<a href="#"><span style="text-decoration: underline"> Unsubscribe.</span></a></div><div style="font-size: 16px; color: #384860">© 2022 Adifect</div></div></div></td></tr></tbody</table></div>')
#                     data = send_email(from_email, to_email, subject, content)
#                     if data:
#                         return Response({'message': 'mail Send successfully, Please check your mail'},
#                                         status=status.HTTP_200_OK)
#                     else:
#                         return Response({'message': 'Something Went Wrong'}, status=status.HTTP_400_BAD_REQUEST)
#                 except Exception as e:
#                     print(e)
#                     return Response({'message': 'Something Went Wrong'}, status=status.HTTP_400_BAD_REQUEST)
#             if user:
#                 if not invite:
#                     invite = InviteMember.objects.create(user=user, agency=agency, status=0)
#                     invite = InviteMember.objects.latest('id')
#                 decodeId = StringEncoder.encode(self, invite.id)
#                 accept_invite_status = 1
#                 accept_invite_encode = StringEncoder.encode(self, accept_invite_status)
#                 reject_invite_status = 2
#                 reject_invite_encode = StringEncoder.encode(self, reject_invite_status)
#                 if user.preferred_communication_mode == '3':
#                     to = user.preferred_communication_id
#                     twilio_number = TWILIO_NUMBER
#                     data = send_text_message(f'You have been invited to join Adifect by {agency.username}',
#                                              twilio_number, to)
#                     if data:
#                         return Response({'message': 'message Send successfully, Please check your SMS'})
#                     else:
#                         return Response({'message': 'Something Went Wrong'}, status=status.HTTP_400_BAD_REQUEST)
#                 elif user.preferred_communication_mode == '2':
#                     receiver = user.preferred_communication_id
#                     data = send_skype_message(receiver, f'You have been invited to join Adifect by {agency.username}')
#                     if data:
#                         return Response({'message': 'message Send successfully, Please check your skype'})
#                     return Response({'message': 'Something Went Wrong'})
#                 elif user.preferred_communication_mode == '1':
#                     to = user.preferred_communication_id
#                     twilio_number_whatsapp = TWILIO_NUMBER_WHATSAPP
#                     data = send_whatsapp_message(twilio_number_whatsapp,
#                                                  f'You have been invited to join Adifect by {agency.username}', to)
#                     if data:
#                         return Response({'message': 'message sent successfully,please check your whatsapp'})
#                     else:
#                         return Response({'message': 'Something went wrong'})
#                 elif user.preferred_communication_mode == '0':
#                     try:
#                         subject = "Invitation link to Join Team"
#                         content = Content("text/html",
#                                           f'<div style=" background: rgba(36,114,252,0.06)!important;"><table style="font:Arial,sans-serif;border-collapse:collapse;width:600px; margin: 0 auto; " width="600" cellpadding="0" cellspacing="0"><tbody style = "width: 100%; float: left; text-align: center;"><tr style = "width: 100%;float: left; text-align: center;"><td style = "width: 100%;float: left; text-align: center;margin: 36px 0 0;"><div class ="email-logo"><img src="{LOGO_122_SERVER_PATH}" style="height: auto;width: 189px;"/></div><div style="margin-top:20px;padding:25px;border-radius:8px!important;background: #fff;border:1px solid #dddddd5e;margin-bottom: 50px;"><h1 style="font-family: arial;font-size: 26px !important;font-weight: bold !important;line-height: inherit !important;margin: 0;color: #000;"> Welcome to Adifect </h1><a href = "#"></a><h1 style = "color: #222222;font-size: 16px;font-weight: 600;line-height: 16px; font-family: arial;" > </h1><p style = "font-size: 16px;font-family: arial;margin: 35px 0 35px;line-height: 24px;color: #000;" > Hi, <b>{user.first_name} {user.last_name}</b> <br><div class="welcome-paragraph"><div style="padding: 10px 0px;font-size: 16px;color: #384860;">You have been invited to join Adifect by {agency.username}!Please click the link below to.</div><div style="padding: 20px 0px;font-size: 16px;color: #384860;">Sincerely,<br />The Adifect Team</div></div> </p><p style = "font-size: 16px; font-family: arial; margin: 25px 0 54px;line-height: 24px; color: #000;" ></p><a href = {BACKEND_SITE_URL}/agency/update-invite-member/{decodeId}/{accept_invite_encode}/{exclusive_decode} style = "padding: 16px 19px;border-radius: 4px; text-decoration: none;color: #fff;font-size: 12px; font-weight: bold; text-transform: uppercase; font-family: arial; background: #2472fc;"> Accepted </a></a><a href = {BACKEND_SITE_URL}/agency/update-invite-member/{decodeId}/{reject_invite_encode}/{exclusive_decode} style = "padding: 16px 19px;border-radius: 4px; text-decoration: none;color: #fff;font-size: 12px; font-weight: bold; text-transform: uppercase; font-family: arial; background: #2472fc;"> Rejected </a><p style = "font-size: 14px;font-family: arial;margin: 45px 0 10px;" > Contact us: 1-800-123-45-67 I mailto:info@adifect.com </p></div></td></tr></tbody></table></div>')

#                         data = send_email(from_email, to_email, subject, content)
#                         if data:
#                             return Response({'message': 'mail Send successfully, Please check your mail'},
#                                             status=status.HTTP_200_OK)
#                         else:
#                             return Response({'message': 'Something Went Wrong'}, status=status.HTTP_400_BAD_REQUEST)

#                     except Exception as e:
            #             print(e)
            #             return Response({'message': 'Something Went Wrong'})
            # return Response({'message': 'success'},
            #                 status=status.HTTP_200_OK)


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
                    email_verified = True
                )
                user.set_password(data['password'])
                user.save()
                # user_status = serializer.validated_data['invite_user']
                # To get user id and update the invite table
                id = kwargs.get('invite_id', None)
                encoded_id = int(StringEncoder.decode(self, id))
                user_id = CustomUser.objects.latest('id')

                invite_id = InviteMember.objects.filter(pk=encoded_id, is_trashed=False).update(user=user,
                                                                                                status=1)
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
            invited_user = InviteMember.objects.filter(agency=agency, is_trashed=False, status=1, user__isnull=False)
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


class DAMViewSet(viewsets.ModelViewSet):
    serializer_class = DAMSerializer
    queryset = DAM.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['id']
    search_fields = ['=id', ]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = DamWithMediaSerializer(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        dam_files = request.FILES.getlist('dam_files')

        if serializer.is_valid():
            self.perform_create(serializer)
            dam_id = DAM.objects.latest('id')
            for i in dam_files:
                DamMedia.objects.create(dam=dam_id, media=i)
            context = {
                'message': 'Media Uploaded Successfully',
                'status': status.HTTP_201_CREATED,
                'errors': serializer.errors,
                'data': serializer.data,
            }
            return Response(context)
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


@permission_classes([IsAuthenticated])
class DraftJobViewSet(viewsets.ModelViewSet):
    serializer_class = JobsWithAttachmentsSerializer
    queryset = Job.objects.filter(status=0)

    def list(self, request, *args, **kwargs):
        data = self.queryset.filter(user=request.user).exclude(user__role=1)
        serializer = self.serializer_class(data, many=True,context={'request': request})
        return Response(data=serializer.data)

@permission_classes([IsAuthenticated])
class TestModalViewSet(viewsets.ModelViewSet):
    serializer_class = TestModalSerializer
    queryset = TestModal.objects.all()
