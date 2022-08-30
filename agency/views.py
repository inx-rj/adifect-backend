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

from .models import WorkFlow, WorkFlowLevels, Stages, InviteMember
from .serializers import WorkFlowSerializer, WorkFlowLevelsSerializer, StagesSerializer, InviteMemberSerializer, InviteMemberRegisterSerializer
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from adifect.settings import SEND_GRID_API_key, FRONTEND_SITE_URL, LOGO_122_SERVER_PATH, BACKEND_SITE_URL
from .helper import StringEncoder
import base64
# Create your views here.
# Create your views here.



@permission_classes([IsAuthenticated])
class AgencyJobsViewSet(viewsets.ModelViewSet):

    serializer_class = JobSerializer
    queryset = Job.objects.all()
    pagination_class = FiveRecordsPagination

    def list(self, request, *args, **kwargs):
        job_data = Job.objects.filter(user=request.user.id).order_by("-modified")
        paginated_data = self.paginate_queryset(job_data)
        serializer = JobsWithAttachmentsSerializer(paginated_data, many=True,context={'request': request})
        return self.get_paginated_response(data=serializer.data)


    def retrieve(self, request, pk=None):
        id = pk
        if id is not None:
            job_data = Job.objects.get(id=id)
            serializer = JobsWithAttachmentsSerializer(job_data)
            return Response(serializer.data,  status=status.HTTP_201_CREATED)


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        image = request.FILES.getlist('image')
        if serializer.is_valid():
            serializer.fields.pop('image')
            self.perform_create(serializer)
            job_id = Job.objects.latest('id')
            for i in image:
                JobAttachments.objects.create(job=job_id,job_images=i)
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
                    JobAttachments.objects.create(job_id=instance.id,job_images=i)

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
    def list(self, request,*args,**kwargs): 
        unapplied_jobs = Job.objects.filter(user=request.user.id, status=0)
        unapplied_jobs_data = JobsWithAttachmentsSerializer(unapplied_jobs,  many=True)
        context = {
                'message': 'pending jobs',
                'status': status.HTTP_200_OK,
                'data': unapplied_jobs_data.data,
            }
        return Response(context)



class StagesViewSet(viewsets.ModelViewSet):
    serializer_class = StagesSerializer
    queryset = Stages.objects.all().order_by('-modified')

    def list(self, request, *args, **kwargs):
        user = self.request.user
        stage_data = self.queryset.filter(agency=user)
        serializer = self.serializer_class(stage_data, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def create(self, request, *args, **kwargs):
        user = self.request.user
        data = request.data
        stage_data = self.queryset.filter(agency=user)
        if stage_data.filter(stage_name=data['stage_name']).exists():
            context = {
                'message': 'Stage already exists'
            }
            return Response(context, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid()
            self.perform_create(serializer)
            serializer.save()
            context = {
                'message': 'Stage Created Successfully',
                'status': status.HTTP_201_CREATED,
                'errors': serializer.errors,
                'data': serializer.data,
            }
            return Response(context)

    def update(self, request, *args, **kwargs):
        user = self.request.user
        data = request.data
        stage_data = self.queryset.filter(agency=user)
        if data['is_name'] == False and data['is_check'] == False:
            return Response({"ERROR":"TRUE"})
        if data['is_name'] == True:
            if stage_data.filter(stage_name=data['stage_name']).exists():
                context = {
                    'message': 'Stage already exists'
                }
                return Response(context, status=status.HTTP_400_BAD_REQUEST)

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance,data=request.data, partial=partial)
        serializer.is_valid()
        self.perform_update(serializer)
        context = {
            'message': 'Stage Updated Successfully',
            'status': status.HTTP_201_CREATED,
            'errors': serializer.errors,
            'data': serializer.data,
        }
        return Response(context)


class WorkFlowLevelsViewSet(viewsets.ModelViewSet):
    serializer_class = WorkFlowLevelsSerializer
    queryset = WorkFlowLevels.objects.all().order_by('-modified')

    def list(self, request, *args, **kwargs):
        user = self.request.user
        level_data = self.queryset.filter(agency=user)
        serializer = self.serializer_class(level_data, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def create(self, request, *args, **kwargs):
        user = self.request.user
        data = request.data
        level_data = self.queryset.filter(agency=user)
        if level_data.filter(level_name=data['level_name']).exists():
            context = {
                'message': 'Level already exists'
            }
            return Response(context, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid()
            self.perform_create(serializer)
            context = {
                'message': 'Level Created Successfully',
                'status': status.HTTP_201_CREATED,
                'errors': serializer.errors,
                'data': serializer.data,
            }
            return Response(context)
    
    def update(self, request, *args, **kwargs):
        user = self.request.user
        
        data = request.data
        level_data = self.queryset.filter(agency=user)
        if data['is_name'] == False and data['is_check'] == False:
            return Response({"ERROR":"TRUE"})
        
        if data['is_name'] == True:
            if level_data.filter(level_name=data['level_name']).exists():
                context = {
                    'message': 'Level already exists'
                }
                return Response(context, status=status.HTTP_400_BAD_REQUEST)
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance,data=request.data, partial=partial)
        serializer.is_valid()
        self.perform_update(serializer)
        context = {
            'message': 'Level Updated Successfully',
            'status': status.HTTP_201_CREATED,
            'errors': serializer.errors,
            'data': serializer.data,
        }
        return Response(context)



class WorkFlowViewSet(viewsets.ModelViewSet):
    serializer_class = WorkFlowSerializer
    queryset = WorkFlow.objects.all()

    def list(self,request, *args, **kwargs):
        user = self.request.user
        workflow_data = self.queryset.filter(agency=user)
        stage_list = []
        stage_dup = list(workflow_data.values('stage', 'stage__stage_name', 'stage__description', 'stage__is_active'))
        list1 = [i for n, i in enumerate(stage_dup) if i not in stage_dup[n + 1:]]
        stage_list.append({'stage':list1})
        stage_list.append({'user':workflow_data.values('pk','user__email','user__username','user__profile_title','stage','stage__stage_name', 'stage__description', 'stage__is_active','level__id','level__level_name','level__description','level__is_active')})
        print(stage_list)
        return Response(data=stage_list, status=status.HTTP_201_CREATED)
    
    def create(self, request, *args, **kwargs):
        user = self.request.user
        data = request.data
        workflow_data = self.queryset.filter(agency=user)
        if workflow_data.filter(Q(user=data['user']) & Q(stage=data['stage'])).exists():
               if workflow_data.filter(level=data['level']).exists():
                context = {
                    'message': 'Same user with this stage and level already exists'
                }
               else:
                    serializer = self.get_serializer(data=request.data)
                    serializer.is_valid()
                    self.perform_create(serializer)
                    serializer.save()
                    context = {
                        'message': 'Workflow Created Successfully',
                        'status': status.HTTP_201_CREATED,
                        'errors': serializer.errors,
                        'data': serializer.data,
                    }
                    return Response(context)
               return Response(context, status=status.HTTP_400_BAD_REQUEST)

        elif workflow_data.filter(Q(user=data['user']) & Q(level=data['level'])).exists():
          if workflow_data.filter(stage=data['stage']).exists():
                context = {
                    'message': 'Same user with this stage and level already exists'
                }
          else:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid()
                self.perform_create(serializer)
                serializer.save()
                context = {
                    'message': 'Workflow Created Successfully',
                    'status': status.HTTP_201_CREATED,
                    'errors': serializer.errors,
                    'data': serializer.data,
                }
                return Response(context)
          return Response(context, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid()
            self.perform_create(serializer)
            serializer.save()
            context = {
                'message': 'Workflow Created Successfully',
                'status': status.HTTP_201_CREATED,
                'errors': serializer.errors,
                'data': serializer.data,
            }
            return Response(context)


    @action(methods=['delete'], detail=False, url_path='stage/(?P<stage_id>[^/.]+)', url_name='stage')
    def remove(self, request, *args, **kwargs):

        try:
            workflow_stage = self.queryset.filter(stage_id=int(kwargs.get('stage_id')))
            if workflow_stage:
                workflow_stage.delete()
                return Response(status=status.HTTP_200_OK, data={'status': 'success', 'error': False})
            else:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'status': 'error', 'error': True})


        except Exception as e:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'Error': str(e)})


class InviteMemberApi(APIView):
    serializer_class = InviteMemberSerializer

    def get(self, request, *args, **kwargs):
        queryset = InviteMember.objects.all()
        serializer = InviteMemberSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data['email']
            message = serializer.validated_data['message']
            level = serializer.validated_data['level']
            exclusive = serializer.validated_data['exclusive']
            user = CustomUser.objects.filter(email=email).first()
            agency = CustomUser.objects.filter(pk=serializer.validated_data['agency'].id).first()
            if not agency:
                return Response({'message': 'Agency does not exists','error':True}, status=status.HTTP_400_BAD_REQUEST)
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
            invite = InviteMember.objects.filter(user__email=email, agency=agency).first()
            if not user:
                if not invite:
                    invite = InviteMember.objects.create(agency=agency, status=0)
                    invite_id = InviteMember.objects.latest('id').pk
                    decodeId = StringEncoder.encode(self,invite_id)
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
                decodeId = StringEncoder.encode(self,invite.id)
                accept_invite_status = 1
                accept_invite_encode = StringEncoder.encode(self,accept_invite_status)
                reject_invite_status = 2
                reject_invite_encode = StringEncoder.encode(self,reject_invite_status)
                try:
                    subject = "Invitation link to Join Team"
                    content = Content("text/html",
                                      f'<div style=" background: rgba(36,114,252,0.06)!important;"><table style="font:Arial,sans-serif;border-collapse:collapse;width:600px; margin: 0 auto; " width="600" cellpadding="0" cellspacing="0"><tbody style = "width: 100%; float: left; text-align: center;"><tr style = "width: 100%;float: left; text-align: center;"><td style = "width: 100%;float: left; text-align: center;margin: 36px 0 0;"><div class ="email-logo"><img src="{LOGO_122_SERVER_PATH}" style="height: auto;width: 189px;"/></div><div style="margin-top:20px;padding:25px;border-radius:8px!important;background: #fff;border:1px solid #dddddd5e;margin-bottom: 50px;"><h1 style="font-family: arial;font-size: 26px !important;font-weight: bold !important;line-height: inherit !important;margin: 0;color: #000;"> Welcome to Adifect </h1><a href = "#"></a><h1 style = "color: #222222;font-size: 16px;font-weight: 600;line-height: 16px; font-family: arial;" > </h1><p style = "font-size: 16px;font-family: arial;margin: 35px 0 35px;line-height: 24px;color: #000;" > Hi, <b>{user.first_name} {user.last_name}</b> <br> {message} </p><p style = "font-size: 16px; font-family: arial; margin: 25px 0 54px;line-height: 24px; color: #000;" > {level} </p><a href = {BACKEND_SITE_URL}/agency/update-invite-member/{decodeId}/{accept_invite_encode}/{exclusive_decode} style = "padding: 16px 19px;border-radius: 4px; text-decoration: none;color: #fff;font-size: 12px; font-weight: bold; text-transform: uppercase; font-family: arial; background: #2472fc;"> Accepted </a></a><a href = {BACKEND_SITE_URL}/agency/update-invite-member/{decodeId}/{reject_invite_encode}/{exclusive_decode} style = "padding: 16px 19px;border-radius: 4px; text-decoration: none;color: #fff;font-size: 12px; font-weight: bold; text-transform: uppercase; font-family: arial; background: #2472fc;"> Rejected </a><p style = "font-size: 14px;font-family: arial;margin: 45px 0 10px;" > Contact us: 1-800-123-45-67 I mailto:info@adifect.com </p></div></td></tr></tbody></table></div>')
                    mail = Mail(from_email, to_email, subject, content)
                    mail_json = mail.get()
                    response = sg.client.mail.send.post(request_body=mail_json)
                    print(response)
                except Exception as e:
                    print(e)
            return Response({'message': 'mail Send successfully, Please check your mail'},
                            status=status.HTTP_200_OK)


class UpdateInviteMemberStatus(APIView):

    def get(self, request, *args, **kwargs):
        data = {}
        id = kwargs.get('id', None)
        encoded_id = int(StringEncoder.decode(self,id))
        status = kwargs.get('status', None)
        encoded_status = int(StringEncoder.decode(self, status))
        exculsive = kwargs.get('exculsive', None)
        encoded_exculsive =  int(StringEncoder.decode(self, exculsive))
        if id and status:
            data = InviteMember.objects.filter(pk=encoded_id)
            if data and exculsive:
                user = CustomUser.objects.filter(pk=data.first().user.id).update(is_exclusive=encoded_exculsive)
            update = data.update(status=encoded_status)
            if update:
                data = {"message": "Thank you for Accepting.", "status": "success"}
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

                if CustomUser.objects.filter(email=data['email']).exists():
                    context = {
                        'message': 'Email already exists'
                    }
                    return Response(context, status=status.HTTP_400_BAD_REQUEST)

                if CustomUser.objects.filter(username=data['username']).exists():
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
                    is_exclusive = exculsive
                )
                user.set_password(data['password'])
                user.save()
                user_status = serializer.validated_data['invite_user']
                # To get user id and update the invite table
                id = kwargs.get('invite_id', None)
                encoded_id = int(StringEncoder.decode(self, id))
                user_id = CustomUser.objects.latest('id')

                invite_id = InviteMember.objects.filter(pk=encoded_id).update(user=user, status=user_status)
                return Response({'message': 'User Registered Successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except KeyError as e:
            return Response({'message': f'{e} is required'}, status=status.HTTP_400_BAD_REQUEST)


class InviteMemberUserList(APIView):
    serializer_class = InviteMemberSerializer

    def get(self, request, *args, **kwargs):
        agency = request.user
        if agency.is_authenticated:
            invited_user = InviteMember.objects.filter(agency=agency, status=1)
            serializer = self.serializer_class(invited_user, many=True)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(data={'error': 'You Are Not Authorized'}, status=status.HTTP_400_BAD_REQUEST)





   