# from locale import DAY_1
from sqlite3 import DatabaseError
import datetime
from django.shortcuts import render
from .serializers import EditProfileSerializer, CategorySerializer, JobSerializer, JobAttachmentsSerializer, \
    JobAppliedSerializer, LevelSerializer, JobsWithAttachmentsSerializer, SkillsSerializer, \
    JobFilterSerializer, RelatedJobsSerializer, \
    JobAppliedAttachmentsSerializer, UserListSerializer, PreferredLanguageSerializer, JobTasksSerializer, \
    JobTemplateSerializer, JobTemplateWithAttachmentsSerializer, JobTemplateAttachmentsSerializer, \
    QuestionSerializer, AnswerSerializer, SearchFilterSerializer, UserSkillsSerializer, JobActivitySerializer, \
    JobActivityChatSerializer, UserPortfolioSerializer, SubmitJobWorkSerializer, MemberApprovalsSerializer, \
    JobsWithAttachmentsThumbnailSerializer, JobActivityUserSerializer
from authentication.models import CustomUser, CustomUserPortfolio
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import viewsets
from .models import Category, Job, JobAttachments, JobApplied, Level, Skills, \
    JobAppliedAttachments, PreferredLanguage, JobTasks, JobTemplate, JobTemplateAttachments, \
    Question, Answer, UserSkills, JobActivity, JobActivityChat, JobTemplateTasks, JobActivityAttachments, SubmitJobWork, \
    JobWorkAttachments, MemberApprovals, JobWorkActivity, JobWorkActivityAttachments
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import Http404, JsonResponse
from .pagination import FiveRecordsPagination, FourRecordsPagination
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
import operator
from functools import reduce
import os
from django.core.exceptions import ValidationError
from authentication.serializers import UserSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
import json
from agency.models import Industry, Company, WorksFlow, Workflow_Stages, InviteMember, DamMedia, DAM
from agency.serializers import IndustrySerializer, CompanySerializer, WorksFlowSerializer, StageSerializer, \
    InviteMemberSerializer, MyProjectSerializer
from rest_framework.decorators import action
from sendgrid.helpers.mail import Mail, Email, To, Content
from adifect.settings import SEND_GRID_API_key, FRONTEND_SITE_URL, LOGO_122_SERVER_PATH, BACKEND_SITE_URL, \
    TWILIO_NUMBER, TWILIO_NUMBER_WHATSAPP, SEND_GRID_FROM_EMAIL
from helper.helper import StringEncoder, send_text_message, send_skype_message, send_email, send_whatsapp_message
from authentication.manager import IsAdmin, IsAdminMember, IsApproverMember
import datetime as dt
from django.db.models import Subquery


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

    # pagination_class = FiveRecordsPagination

    def get(self, request, *args, **kwargs):
        queryset = CustomUser.objects.filter(email=self.request.user.email, is_trashed=False)
        serializer = EditProfileSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
        # paginated_data = FiveRecordsPagination(queryset)
        # serializer = EditProfileSerializer(paginated_data, many=True,context={'request':request})
        # return self.get_paginated_response(data=serializer.data)

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
        user.sub_title = request.data.get('sub_title', None)
        user.Language = request.data.get('Language', None)
        user.website = request.data.get('website', None)
        video = request.data.get('video', None)
        user.preferred_communication_mode = request.data.get('preferred_communication_mode', None)
        user.preferred_communication_id = request.data.get('preferred_communication_id', None)
        user.availability = request.data.get('availability', None)
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



class IndustryViewSet(viewsets.ModelViewSet):
    serializer_class = IndustrySerializer
    queryset = Industry.objects.filter(is_trashed=False).order_by('-modified')

# @permission_classes([IsAdmin | IsApproverMember])
@permission_classes([IsAuthenticated])
class LevelViewSet(viewsets.ModelViewSet):
    serializer_class = LevelSerializer
    queryset = Level.objects.filter(is_trashed=False).order_by('-modified')


@permission_classes([IsAuthenticated])
class SkillsViewSet(viewsets.ModelViewSet):
    serializer_class = SkillsSerializer
    queryset = Skills.objects.filter(is_trashed=False).order_by('-modified')


@permission_classes([IsAdmin])
class UserListViewSet(viewsets.ModelViewSet):
    serializer_class = UserListSerializer
    queryset = CustomUser.objects.all().order_by('date_joined')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).exclude(id=request.user.id).order_by('date_joined')
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        user_id = request.data.get('user', None)
        user = CustomUser.objects.filter(id=user_id).first()
        if user:
            if request.user.role == 0:
                serializer = self.get_serializer(
                    user, data=request.data, partial=partial)
                if serializer.is_valid():
                    self.perform_update(serializer)
                context = {
                    'message': 'Updated Successfully',
                    'status': status.HTTP_200_OK,
                    'errors': serializer.errors,
                    'data': serializer.data,
                }
            else:
                context = {
                    'message': 'you are not Authorize',
                    'status': status.HTTP_400_BAD_REQUEST,
                    'errors': True,
                    'data': '',
                }
        else:
            context = {
                'message': 'User Does Not Exist',
                'status': status.HTTP_400_BAD_REQUEST,
                'errors': True,
                'data': '',
            }
        return Response(context)


def dam_images_list(dam_images, job_id):
    if dam_images:
        exceeded_files = []
        for i in dam_images:
            dam_inital = DamMedia.objects.get(id=i)
            if not JobAttachments.objects.filter(job=job_id, dam_media_id=dam_inital).exists():
                dam_inital.job_count += 1
                dam_inital.save()

            if dam_inital.limit_usage_toggle == 'true':
                if dam_inital.limit_usage < dam_inital.limit_used:
                    print("limit exceeded")
                    exceeded_files.append(dam_inital)
                else:
                    JobAttachments.objects.create(job=job_id, job_images=dam_inital.media, dam_media_id=dam_inital)
                    dam_inital.limit_used += 1
                    dam_inital.save()
            else:
                JobAttachments.objects.create(job=job_id, job_images=dam_inital.media, dam_media_id=dam_inital)
                dam_inital.limit_used += 1
                dam_inital.save()
            if dam_inital.limit_usage_toggle == 'true' and dam_inital.limit_usage <= dam_inital.limit_used:
                dam_inital.usage_limit_reached = True
                dam_inital.save()

        return Response({'exceeded files': exceeded_files}, status=status.HTTP_400_BAD_REQUEST)


def dam_sample_images_list(dam_sample_images, job_id):
    if dam_sample_images:
        exceeded_files = []
        for i in dam_sample_images:
            dam_inital = DamMedia.objects.get(id=i)
            if not JobAttachments.objects.filter(Q(job=job_id) & Q(dam_media_id=dam_inital)).exists():
                dam_inital.job_count += 1
                dam_inital.save()
            if dam_inital.limit_usage_toggle == 'true':
                if dam_inital.limit_usage < dam_inital.limit_used:
                    exceeded_files.append(dam_inital)
                else:
                    JobAttachments.objects.create(job=job_id, work_sample_images=dam_inital.media,
                                                  dam_media_id=dam_inital)
                    dam_inital.limit_used += 1
                    dam_inital.save()
            else:
                JobAttachments.objects.create(job=job_id, work_sample_images=dam_inital.media, dam_media_id=dam_inital)
                dam_inital.limit_used += 1
                dam_inital.save()

            if dam_inital.limit_usage_toggle == 'true' and dam_inital.limit_usage <= dam_inital.limit_used:
                dam_inital.usage_limit_reached = True
                dam_inital.save()

        return Response({'exceeded files': exceeded_files}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
class JobViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    queryset = Job.objects.all()
    job_template_attach = JobTemplateAttachmentsSerializer
    pagination_class = FiveRecordsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['company','user']


    def list(self, request, *args, **kwargs):
        user_role = request.user.role
        if user_role == 0:
            job_data = self.filter_queryset(self.get_queryset()).exclude(status=0).order_by('-modified')
            # job_data = self.filter_queryset(self.get_queryset()).filter(user=request.user).exclude(status=0).order_by('-modified')
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
                    print(template_name)
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


            #----- FOR IN HOUSE MEMBER ------#
            if job_id.is_house_member:
                for i in job_id.house_member.all():
                    JobApplied.objects.create(job=job_id,status=2,user=i.user.user,is_seen=True)

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


def validate_job_attachments(images):
    error = 0
    for img in images:
        ext = os.path.splitext(img.name)[1]
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.svg']
        if not ext.lower() in valid_extensions:
            error += 1
    return error


@permission_classes([IsAuthenticated])
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
        attachments = request.FILES.getlist('image')
        data = request.data
        if serializer.is_valid():
            if self.queryset.filter(Q(job=data['job']) & Q(user=data['user']) & Q(job__is_active=False)).exists():
                context = {
                    'message': 'Job already applied Or Closed',
                }
                return Response(context, status=status.HTTP_400_BAD_REQUEST)
            else:
                attachment_error = validate_attachment(attachments)
                if attachment_error != 0:
                    return Response({'message': "Invalid Attachment"}, status=status.HTTP_400_BAD_REQUEST)
                self.perform_create(serializer)
                status_job = serializer.validated_data.get('status', None)
                test_status = None
                if not status_job:
                    test_status = JobActivity.Type.Proposal
                if status_job == 0:
                    test_status = JobActivity.Type.Proposal
                if status_job == 2:
                    test_status = JobActivity.Type.Accept
                if status_job == 1:
                    test_status = JobActivity.Type.Reject
                if test_status:
                    JobActivity.objects.create(job_id=data['job'], activity_type=test_status, user=request.user)
                job_applied_id = JobApplied.objects.latest('id')
                if data.get('question', None):
                    Question.objects.create(
                        question=data['question'],
                        job_applied=job_applied_id,
                        user_id=data['user'],
                    )
                for i in attachments:
                    JobAppliedAttachments.objects.create(job_applied=job_applied_id, job_applied_attachments=i)
                context = {
                    'message': 'Job Applied Successfully',
                    'status': status.HTTP_201_CREATED,
                    'errors': serializer.errors,
                    'data': serializer.data,
                }

                proposed_price = request.data.get('proposed_price', None)
                proposed_due_date = request.data.get('proposed_due_date', None)
                color = 'color:#ff3333;'

                if not proposed_price:
                    color = ''

                agency = serializer.validated_data.get('job')
                from_email = Email(SEND_GRID_FROM_EMAIL)
                to_email = To(agency.user.email)
                skills = ''
                for i in agency.skills.all():
                    skills += f'<div style="margin:0px 0px 0px 0px;height: 44px;float:left;"><button style="background-color: rgba(36,114,252,0.08);border-radius: ' \
                              f'30px;font-style: normal;font-weight: 600;font-size: 12px;line-height: 18px;text-align: ' \
                              f'center;border: none;color: #2472fc;margin-right: 4px;padding: 8px 10px 8px 10px;">' \
                              f'{i.skill_name}</button></div>'
                try:
                    subject = "Job proposal"
                    content = Content("text/html",
                                      f'<div style="background:rgba(36,114,252,.06)!important"><table style="font:Arial,sans-serif;border-collapse:collapse;width:600px;margin:0 auto" width="600" cellpadding="0" cellspacing="0"><tbody><tr><td style="width:100%;margin:36px 0 0"><div style="padding:34px 44px;border-radius:8px!important;background:#fff;border:1px solid #dddddd5e;margin-bottom:50px;margin-top:50px"><div class="email-logo"><img style="width:165px" src="{LOGO_122_SERVER_PATH}"></div><a href="#"></a><div class="welcome-text" style="padding-top:80px"><h1 style="font:24px">Hello, {agency.user.get_full_name()}</h1></div><div class="welcome-paragraph"><div style="padding:10px 0;font-size:16px;color:#384860">You have a new Job Proposal for the job below:</div><div style="border: 1px solid rgba(36,114,252,.16);border-radius:8px;float: left;margin-bottom: 15px;"><div style="padding:20px"><div><h1 style="font:24px">{agency.title}</h1></div><div style="font-size:16px;line-height:19px;color:#a0a0a0">Posted on: <span>06-02-2022</span></div><div style="padding:13px 0;font-size:16px;color:#384860">{agency.description[:200]}</div><div style="font-size:16px;line-height:19px;color:#384860;font-weight:700;width:100%;float:left;margin-bottom: 10px;"><span style="margin-right:6px;;float: left;">Original Price :</span><span style="margin-left: 0px;">${agency.price}</span></div><div style="font-size:16px;line-height:19px;color:#384860;font-weight:700;width:100%;float:left;margin-bottom: 10px;"><span style="margin-right:6px;float: left;">Original due date :</span><span style="margin-left: 0px">{agency.job_due_date}</span></div><div style="font-size:16px;line-height:19px;color:#384860;font-weight:700;width:100%;float:left;margin-bottom: 10px;"><span style="margin-right:6px;float: left;">Proposed Price :</span><span style="margin-left: 0px;{color}">${proposed_price if proposed_price else agency.price}</span></div><div style="font-size:16px;line-height:19px;color:#384860;font-weight:700;width:100%;float:left;margin-bottom: 10px;"><span style="margin-right:6px;float: left;">Proposed due date :</span><span style="margin-left: 0px;{color}">{proposed_due_date if proposed_price else agency.job_due_date}</span></div><div style="float:left;width:100% !important;">{skills}</div></div></div><div style="padding:10px 0;font-size:16px;color:#384860">Please click the link below to view the Job Proposal.</div><div style="padding:20px 0;font-size:16px;color:#384860">Sincerely,<br>The Adifect Team</div></div><div style="padding-top:40px"><a href="{FRONTEND_SITE_URL}/?redirect=jobs/details/{agency.id}"><button style="height:56px;padding:15px 44px;background:#2472fc;border-radius:8px;border-style:none;color:#fff;font-size:16px;cursor:pointer">View Job Proposal</button></a></div><div style="padding:50px 0" class="email-bottom-para"><div style="padding:20px 0;font-size:16px;color:#384860">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect? <a href="#"><span style="text-decoration:underline">Unsubscribe.</span></a></div><div style="font-size:16px;color:#384860">© 2022 Adifect</div></div></div></td></tr></tbody></table></div>')
                    data = send_email(from_email, to_email, subject, content)
                except Exception as e:
                    print("error")
                    print(e)
                data = None
            return Response(context)
        else:
            return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        attachments = request.FILES.getlist('image')
        data = request.data
        if serializer.is_valid():
            attachment_error = validate_attachment(attachments)
            if attachment_error != 0:
                return Response({'message': "Invalid Attachment"}, status=status.HTTP_400_BAD_REQUEST)
            self.perform_create(serializer)
            if data.get('question', None):
                Question.objects.create(
                    question=data['question'],
                    job_applied=instance,
                    user_id=data['user'],
                )
            for i in attachments:
                JobAppliedAttachments.objects.create(job_applied=instance, job_applied_attachments=i)
            context = {
                'message': 'Job Applied Successfully',
                'status': status.HTTP_201_CREATED,
                'errors': serializer.errors,
                'data': serializer.data,
            }
            status_job = serializer.validated_data.get('status', None)
            test_status = None
            if not status_job:
                test_status = JobActivity.Type.Proposal
            if status_job == 0:
                test_status = JobActivity.Type.Proposal
            if status_job == 2:
                test_status = JobActivity.Type.Accept
            if status_job == 1:
                test_status = JobActivity.Type.Reject
            if status_job == 4:
                test_status = JobActivity.Type.Completed
            if test_status:
                JobActivity.objects.create(job=instance.job, activity_type=test_status, user=request.user)
            proposed_price = request.data.get('proposed_price', None)
            proposed_due_date = request.data.get('proposed_due_date', None)
            color = 'color:#ff3333;'

            if not proposed_price:
                color = ''

            agency = serializer.validated_data.get('job')
            from_email = Email(SEND_GRID_FROM_EMAIL)
            to_email = To(agency.user.email)
            skills = ''
            for i in agency.skills.all():
                skills += f'<div style="margin:0px 0px 0px 0px;height: 44px;float:left;"><button style="background-color: rgba(36,114,252,0.08);border-radius: ' \
                          f'30px;font-style: normal;font-weight: 600;font-size: 12px;line-height: 18px;text-align: ' \
                          f'center;border: none;color: #2472fc;margin-right: 4px;padding: 8px 10px 8px 10px;">' \
                          f'{i.skill_name}</button></div>'
            try:
                subject = "Job proposal"
                content = Content("text/html",
                                  f'<div style="background:rgba(36,114,252,.06)!important"><table style="font:Arial,sans-serif;border-collapse:collapse;width:600px;margin:0 auto" width="600" cellpadding="0" cellspacing="0"><tbody><tr><td style="width:100%;margin:36px 0 0"><div style="padding:34px 44px;border-radius:8px!important;background:#fff;border:1px solid #dddddd5e;margin-bottom:50px;margin-top:50px"><div class="email-logo"><img style="width:165px" src="{LOGO_122_SERVER_PATH}"></div><a href="#"></a><div class="welcome-text" style="padding-top:80px"><h1 style="font:24px">Hello, {agency.user.get_full_name()}</h1></div><div class="welcome-paragraph"><div style="padding:10px 0;font-size:16px;color:#384860">You have a new Job Proposal for the job below:</div><div style="border: 1px solid rgba(36,114,252,.16);border-radius:8px;float: left;margin-bottom: 15px;"><div style="padding:20px"><div><h1 style="font:24px">{agency.title}</h1></div><div style="font-size:16px;line-height:19px;color:#a0a0a0">Posted on: <span>06-02-2022</span></div><div style="padding:13px 0;font-size:16px;color:#384860">{agency.description[:200]}</div><div style="font-size:16px;line-height:19px;color:#384860;font-weight:700;width:100%;float:left;margin-bottom: 10px;"><span style="margin-right:6px;;float: left;">Original Price :</span><span style="margin-left: 0px;">${agency.price}</span></div><div style="font-size:16px;line-height:19px;color:#384860;font-weight:700;width:100%;float:left;margin-bottom: 10px;"><span style="margin-right:6px;float: left;">Original due date :</span><span style="margin-left: 0px">{agency.job_due_date}</span></div><div style="font-size:16px;line-height:19px;color:#384860;font-weight:700;width:100%;float:left;margin-bottom: 10px;"><span style="margin-right:6px;float: left;">Proposed Price :</span><span style="margin-left: 0px;{color}">${proposed_price if proposed_price else agency.price}</span></div><div style="font-size:16px;line-height:19px;color:#384860;font-weight:700;width:100%;float:left;margin-bottom: 10px;"><span style="margin-right:6px;float: left;">Proposed due date :</span><span style="margin-left: 0px;{color}">{proposed_due_date if proposed_price else agency.job_due_date}</span></div><div style="float:left;width:100% !important;">{skills}</div></div></div><div style="padding:10px 0;font-size:16px;color:#384860">Please click the link below to view the Job Proposal.</div><div style="padding:20px 0;font-size:16px;color:#384860">Sincerely,<br>The Adifect Team</div></div><div style="padding-top:40px"><a href="{FRONTEND_SITE_URL}/?redirect=jobs/details/{agency.id}"><button style="height:56px;padding:15px 44px;background:#2472fc;border-radius:8px;border-style:none;color:#fff;font-size:16px;cursor:pointer">View Job Proposal</button></a></div><div style="padding:50px 0" class="email-bottom-para"><div style="padding:20px 0;font-size:16px;color:#384860">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect? <a href="#"><span style="text-decoration:underline">Unsubscribe.</span></a></div><div style="font-size:16px;color:#384860">© 2022 Adifect</div></div></div></td></tr></tbody></table></div>')
                data = send_email(from_email, to_email, subject, content)
            except Exception as e:
                print(e)
            data = None
        else:
            context = {
                'message': 'You cannot update the proposal',
                'errors': serializer.errors,
            }
        return Response(context)


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
            applied_data = JobApplied.objects.filter(user=request.user, is_trashed=False).values_list('job_id',
                                                                                                      flat=True)
            latest_job = Job.objects.exclude(id__in=list(applied_data),is_house_member=False)
            latest_job = latest_job.exclude(status=0).filter(job_due_date__gte=dt.datetime.today())
            user_role = request.user.role
            if not user_role == 0:
                latest_job = latest_job.exclude(is_active=0)
            latest_job = latest_job.latest('id')
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


@permission_classes([IsAuthenticated])
class JobActivityViewSet(viewsets.ModelViewSet):
    serializer_class = JobActivitySerializer
    queryset = JobActivity.objects.all()
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['job', 'user', 'job__user', ]

    # search_fields = ['=status', ]
    # pagination_class = FiveRecordsPagination
    # http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).filter(job__user=request.user)
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            if serializer.validated_data['activity_status'] == 1:
                attachment = request.FILES.getlist('chat_attachments')
                if attachment:
                    latest_chat = JobActivityChat.objects.latest('id')
                    for i in attachment:
                        JobActivityAttachments.objects.create(job_activity_chat=latest_chat, chat_attachment=i)
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


# @permission_classes([IsAuthenticated])
# class JobHiredViewSet(viewsets.ModelViewSet):
#     serializer_class = JobHiredSerializer
#     queryset = JobHired.objects.filter(is_trashed=False)
#     parser_classes = (MultiPartParser, FormParser, JSONParser)
#     filter_backends = [DjangoFilterBackend, SearchFilter]
#     filterset_fields = ['status']
#     search_fields = ['=status', ]


@permission_classes([IsAuthenticated])
class RelatedJobsAPI(APIView):

    def get(self, request, *args, **kwargs):
        if kwargs['company_id']:
            queryset = Job.objects.filter(user=request.user, status=2, company_id=kwargs['company_id'])
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
    filterset_fields = ['job', 'is_complete']
    search_fields = ['=job', 'title']


def dam_images_templates(dam_images, job_template_id):
    if dam_images:
        exceeded_files = []
        for i in dam_images:
            dam_inital = DamMedia.objects.get(id=i)
            if not JobAttachments.objects.filter(job=job_template_id, dam_media_id=dam_inital).exists():
                dam_inital.job_count += 1
                dam_inital.save()

            if dam_inital.limit_usage_toggle == 'true':
                if dam_inital.limit_usage < dam_inital.limit_used:
                    print("limit exceeded")
                    exceeded_files.append(dam_inital)

                else:
                    JobTemplateAttachments.objects.create(job_template=job_template_id,
                                                          job_template_images=dam_inital.media)
                    dam_inital.limit_used += 1
                    dam_inital.save()
            else:
                JobTemplateAttachments.objects.create(job_template=job_template_id,
                                                      job_template_images=dam_inital.media)
                dam_inital.limit_used += 1
                dam_inital.save()
            if dam_inital.limit_usage_toggle == 'true' and dam_inital.limit_usage <= dam_inital.limit_used:
                dam_inital.usage_limit_reached = True
                dam_inital.save()
        return Response({'exceeded files': exceeded_files}, status=status.HTTP_400_BAD_REQUEST)


def dam_sample_template_images_list(dam_sample_work, job_template_id):
    if dam_sample_work:
        exceeded_files = []
        for i in dam_sample_work:
            dam_inital = DamMedia.objects.get(id=i)
            if not JobAttachments.objects.filter(job=job_template_id, dam_media_id=dam_inital).exists():
                dam_inital.job_count += 1
                dam_inital.save()
            if type(dam_inital.limit_usage) == int:
                if dam_inital.limit_usage < dam_inital.limit_used:
                    print("limit exceeded")
                    exceeded_files.append(dam_inital)
                else:
                    JobTemplateAttachments.objects.create(job_template=job_template_id,
                                                          work_sample_images=dam_inital.media)
                    dam_inital.limit_used += 1
                    dam_inital.save()
            else:
                JobTemplateAttachments.objects.create(job_template=job_template_id, work_sample_images=dam_inital.media)
                dam_inital.limit_used += 1
                dam_inital.save()
            if type(dam_inital.limit_usage) == int and dam_inital.limit_usage <= dam_inital.limit_used:
                dam_inital.usage_limit_reached = True
                dam_inital.save()
        return Response({'exceeded files': exceeded_files}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
class JobTemplatesViewSet(viewsets.ModelViewSet):
    serializer_class = JobTemplateSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    queryset = JobTemplate.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['company']
    search_fields = ['=company', ]

    # pagination_class = FiveRecordsPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        job_data = queryset.filter(user=request.user).order_by('-modified')
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
    queryset = Company.objects.all().order_by('-modified')
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['-modified', 'created']
    filterset_fields = ['is_active', 'agency', 'is_blocked']
    search_fields = ['=is_active', '=agency']


@permission_classes([IsAuthenticated])
class WorkflowViewSet(viewsets.ModelViewSet):
    serializer_class = WorksFlowSerializer
    queryset = WorksFlow.objects.filter(is_trashed=False).order_by('-modified')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['company', 'is_blocked']
    search_fields = ['=company']

    def list(self, request, *args, **kwargs):
        user = self.request.user
        workflow_data = self.filter_queryset(self.get_queryset())
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
                                                    is_observer=i['is_observer'], is_all_approval=i['is_all_approval'],
                                                    workflow=workflow_latest, order=i['order'],
                                                    approval_time=i['approval_time'],is_nudge=i['is_nudge'],nudge_time=i['nudge_time'])
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
                                                                approval_time=i['approval_time'],is_nudge=i['is_nudge'],nudge_time=i['nudge_time'])
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
                                                              approval_time=i['approval_time'],is_nudge=i['is_nudge'],nudge_time=i['nudge_time'])
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
                    return Response(context, status=status.HTTP_201_CREATED)
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
            return Response(context, status=status.HTTP_400_BAD_REQUES)
        except Exception as e:
            print(e)
            context = {
                'message': "Something Went Wrong",
                'status': status.HTTP_400_BAD_REQUEST,
                'errors': "Error",
                'data': [],
            }
            return Response(context, status=status.HTTP_400_BAD_REQUEST)

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

    @action(methods=['put'], detail=False, url_path='update_blocked/(?P<pk>[^/.]+)', url_name='update_blocked')
    def update_blocked(self, request, pk=None, *args, **kwargs):
        self.queryset.filter(id=pk).update(is_blocked=request.data['is_blocked'])
        context = {
            'message': 'Updated Succesfully',
            'status': status.HTTP_200_OK,
        }
        return Response(context, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
class JobProposal(APIView):
    serializer_class = JobAppliedSerializer

    def get(self, request, pk, format=None):
        job_id = pk
        if job_id:
            query_set = JobApplied.objects.filter(job_id=job_id).exclude(status=JobApplied.Status.HIRE)
            serializer = self.serializer_class(query_set, many=True, context={'request': request})
            data_query = serializer.data
            data = {'message': 'sucess', 'data': data_query, 'status': status.HTTP_200_OK, 'error': False}
        else:
            data = {'message': 'job_id not found', 'status': status.HTTP_404_NOT_FOUND, 'error': True}
        return Response(data=data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        initial_status = request.data.get('status', None)
        job_applied_id = request.data.get('id', None)

        if job_applied_id and initial_status:
            job_proposal = JobApplied.objects.filter(pk=job_applied_id)
            update_proposal = job_proposal.update(status=initial_status, Accepted_proposal_date=datetime.datetime.now())
            test_status = None
            job_details = job_proposal.first()
            if initial_status == 2:
                test_status = JobActivity.Type.Accept

            if initial_status == 1:
                test_status = JobActivity.Type.Reject

            if initial_status == 4:
                test_status = JobActivity.Type.Completed
            if test_status:
                JobActivity.objects.create(job=job_details.job, activity_type=test_status, user=job_details.user)
            if not JobActivity.objects.filter(job=job_details.job, activity_type=JobActivity.Type.Accept):
                JobActivity.objects.create(job=job_details.job, activity_type=5)
            # ------------------ EMAIL Section ---------------------------------------#
            if int(initial_status) == 2 and update_proposal:
                from_email = Email(SEND_GRID_FROM_EMAIL)
                to_email = To(job_details.user.email)
                skills = ''
                for i in job_details.job.skills.all():
                    skills += f'<div style="float: left; margin-right: 6px; height: 43px;"><button style="background-color: rgba(36,114,252,0.08);border-radius: ' \
                              f'30px;font-style: normal;font-weight: 600;font-size: 12px;line-height: 18px;text-align: ' \
                              f'center;border: none;color: #2472fc;padding: 8px 10px 8px 10px;">' \
                              f'{i.skill_name}</button></div>'
                try:
                    subject = "Your Job Proposal has been accepted"
                    content = Content("text/html",
                                      f'<div style="background:rgba(36,114,252,.06)!important"><table style="font:Arial,sans-serif;border-collapse:collapse;width:600px;margin:0 auto" width="600" cellpadding="0" cellspacing="0"><tbody><tr><td style="width:100%;margin:36px 0 0"><div style="padding:34px 44px;border-radius:8px!important;background:#fff;border:1px solid #dddddd5e;margin-bottom:50px;margin-top:50px"><div class="email-logo"><img style="width:165px" src="{LOGO_122_SERVER_PATH}"></div><a href="#"></a><div class="welcome-text" style="padding-top:80px"><h1 style="font:24px">Congratulations! 🎉</h1></div><div class="welcome-paragraph"><div style="padding:10px 0;font-size:16px;color:#384860">Your Job Proposal has been accepted!</div><div style="box-shadow:0 4px 40px rgb(36 114 252 / 6%);border-radius:0 8px 8px 0;margin-top:10px;display:flex"><div style="width:7px;background-color:#2472fc;border-radius:50px"></div><div><div style="padding: 0 20px;height: 100%;border-radius: 0;"><div><h1 style="font:24px">{job_details.job.title}</h1></div><div style="padding:13px 0;font-size:16px;color:#384860">{job_details.job.description}</div><div><button style="background-color:rgba(36,114,252,.08);border-radius:30px;font-style:normal;font-weight:600;font-size:15px;line-height:18px;text-align:center;border:none;color:#2472fc;padding:8px 20px 8px 20px">In Progress</button></div><div style="font-size:16px;line-height:19px;color:rgba(0,0,0,.7);font-weight:700;padding:15px 0">Due on:<span style="padding:0 12px">{job_details.job.job_due_date}</span></div><div style="font-size:16px;line-height:19px;color:rgba(0,0,0,.7);font-weight:700;padding-bottom:17px">Assigned to:<span style="padding:0 12px;color:#2472fc">{job_details.user.get_full_name()}</span></div><div style="float: left;width: 100%;">{skills}</div></div></div></div><div style="padding: 10px 0 40px;font-size:16px;color:#384860;float: left;width: 100%;">Please click the link below to view your new job.</div><div style="padding:20px 0;font-size:16px;color:#384860">Sincerely,<br>The Adifect Team</div></div><div style="padding-top:40px"><a href="{FRONTEND_SITE_URL}/jobs/details/{job_details.job.id}"><button style="height:56px;padding:15px 80px;background:#2472fc;border-radius:8px;border-style:none;color:#fff;font-size:16px;cursor:pointer">View Job</button></a></div><div style="padding:50px 0" class="email-bottom-para"><div style="padding:20px 0;font-size:16px;color:#384860">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect? <a href="#"><span style="text-decoration:underline">Unsubscribe.</span></a></div><div style="font-size:16px;color:#384860">© 2022 Adifect</div></div></div></td></tr></tbody></table></div>')
                    # content = Content("text/html",
                    #                   f'<div style="background:rgba(36,114,252,.06)!important"><table style="font:Arial,sans-serif;border-collapse:collapse;width:600px;margin:0 auto" width="600" cellpadding="0" cellspacing="0"><tbody><tr><td style="width:100%;background:#fff;margin:36px 0 0"><div style="padding:34px 44px;border-radius:8px!important;background:#fff;border:1px solid #dddddd5e;margin-bottom:50px;margin-top:50px"><div class="email-logo"><img style="width:165px" src="{LOGO_122_SERVER_PATH}"></img></div><a href="#"></a><div class="welcome-text" style="padding-top:80px"><h1 style="font:24px">Congratulations! 🎉</h1></div><div class="welcome-paragraph"><div style="padding:10px 0;font-size:16px;color:#384860">Your Job Proposal has been accepted!</div><div style="box-shadow:0 4px 40px rgb(36 114 252 / 6%);border-radius:0 8px 8px 0;margin-top:10px;display:flex"><div style="width:13px;background-color:#2472fc;border-radius:50px"></div><div><div style="padding:20px"><div><h1 style="font:24px">{job_details.job.title}</h1></div><div style="padding:13px 0;font-size:16px;color:#384860">{job_details.job.description}</div><div><button style="background-color:rgba(36,114,252,.08);border-radius:30px;font-style:normal;font-weight:600;font-size:15px;line-height:18px;text-align:center;border:none;color:#2472fc;padding:8px 20px 8px 20px">In Progress</button></div><div style="font-size:16px;line-height:19px;color:rgba(0,0,0,.7);font-weight:700;padding:15px 0">Due on:<span style="padding:0 12px">{job_details.job.job_due_date}</span></div><div style="font-size:16px;line-height:19px;color:rgba(0,0,0,.7);font-weight:700;padding-bottom:17px">Assigned to:<span style="padding:0 12px;color:#2472fc">{job_details.user.get_full_name()}</span></div><div style="display:flex">{skills}</div></div></div></div></div><div style="padding:10px 0;font-size:16px;color:#384860">Please click the link below to view your new job.</div><div style="padding:20px 0;font-size:16px;color:#384860"></div>Sincerely,<br>The Adifect Team</div><div style="padding-top:40px"><a href="{FRONTEND_SITE_URL}/jobs/details/{job_details.job.id}"><button  style="height:56px;padding:15px 80px;background:#2472fc;border-radius:8px;border-style:none;color:#fff;font-size:16px;cursor:pointer">View Job</button></a></div><div style="padding:50px 0" class="email-bottom-para"><div style="padding:20px 0;font-size:16px;color:#384860">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect?<a href="#"><span style="text-decoration:underline">Unsubscribe.</span></a></div><div style="font-size:16px;color:#384860">© 2022 Adifect</div></div></div></td></tr></tbody></table></div>')
                    data = send_email(from_email, to_email, subject, content)
                except Exception as e:
                    print(e)
                    data = None
            # ---------------------------------- end -------------------------------#
            if update_proposal:
                return Response({'message': 'Your proposal is updated successfully.', 'status': status.HTTP_200_OK},
                                status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Something Went Wrong ', 'status': status.HTTP_200_OK},
                                status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Status Or Id Missing', 'error': True, 'status': status.HTTP_404_NOT_FOUND},
                        status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, format=None):
        if pk:
            update = JobApplied.objects.filter(job_id=pk).update(is_seen=True)
            if update:
                context = {
                    'message': 'Updated successfully',
                    'status': status.HTTP_200_OK,
                    'errors': False,
                }
                return Response(context, status=status.HTTP_200_OK)
            context = {
                'message': 'Something Went Wrong',
                'status': status.HTTP_400_BAD_REQUEST,
                'errors': True,
            }

        return Response(context, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
class ProposalUnseenCount(APIView):
    def get(self, request, pk, format=None):
        job_id = pk
        if job_id:
            query_set = JobApplied.objects.filter(job_id=job_id, is_seen=False).count()
            data = {'message': 'success', 'not_seen_count': query_set,
                    'status': status.HTTP_200_OK, 'error': False}
        else:
            data = {'message': 'job_id not found', 'status': status.HTTP_404_NOT_FOUND, 'error': True}
        return Response(data=data, status=status.HTTP_200_OK)


class StagesViewSet(viewsets.ModelViewSet):
    serializer_class = StageSerializer
    queryset = Workflow_Stages.objects.filter(is_trashed=False).order_by('-modified')


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    queryset = Question.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['question']
    search_fields = ['=question']

    def list(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        queryset = self.filter_queryset(self.get_queryset())
        # messages = queryset.filter(Q(user=user) | Q(job_applied__job__user=user)).order_by('-modified')
        messages = queryset.order_by('-modified')
        serializer = QuestionSerializer(messages, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        if pk is not None:
            # questions = self.queryset.filter(Q(job_applied__job_id=pk) & (Q(user=request.user) | Q(job_applied__job__user=request.user))).order_by('-modified')
            questions = self.queryset.filter(job_applied__job_id=pk).order_by('-modified')
            serializer = QuestionSerializer(questions, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        data = request.data
        if serializer.is_valid():
            if JobApplied.objects.filter(id=data['job_applied']).exists():
                self.perform_create(serializer)
                context = {
                    'message': 'Message sent successfully',
                    'data': serializer.data
                }
                return Response(context, status=status.HTTP_200_OK)

            else:
                return Response({'message': "Bad Request"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class OldestFirstQuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    queryset = Question.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['question']
    search_fields = ['=question']

    def list(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        queryset = self.filter_queryset(self.get_queryset())
        messages = queryset.filter((Q(user=user) | Q(job_applied__job__user=user)) & Q(is_trashed=False)).order_by(
            'modified')
        serializer = QuestionSerializer(messages, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer

    def list(self, request, *args, **kwargs):

        # messages = self.queryset.filter((
        #     Q(question__user=request.user) | Q(job_applied__job__user=request.user)) & Q(is_trashed=False)).order_by('modified')
        messages = self.queryset.order_by('modified')
        serializer = AnswerSerializer(messages, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = AnswerSerializer(data=request.data)
        data = request.data

        if serializer.is_valid():
            if data['type'] == "question":
                if data['user']:
                    if JobApplied.objects.filter(Q(id=data['job_applied']) & Q(user=data['user'])).exists():
                        self.perform_create(serializer)
                        context = {
                            'message': 'Message sent successfully',
                            'data': serializer.data
                        }
                        return Response(context, status=status.HTTP_200_OK)
                    else:
                        return Response({'message': "Bad Request"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'message': "Bad Request"}, status=status.HTTP_400_BAD_REQUEST)

            if data['type'] == "answer":
                if data['agency']:
                    if JobApplied.objects.filter(Q(id=data['job_applied']) & Q(job__user=data['agency'])).exists():
                        self.perform_create(serializer)
                        ans_data = serializer.validated_data.get('question')
                        Question.objects.filter(id=ans_data.id).update(status=1)
                        context = {
                            'message': 'Message sent successfully',
                            'data': serializer.data
                        }
                        return Response(context, status=status.HTTP_200_OK)
                    else:
                        return Response({'message': "Bad Request"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'message': "Bad Request"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'message': "Bad Request"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------------- job update  ------------------------------------------#

class JobStatusUpdate(APIView):
    def get(self, request, *args, **kwargs):
        job_id = kwargs.get('Job_id')
        is_active = kwargs.get('status')
        if job_id and (is_active or is_active == 0):
            job_update = Job.objects.filter(pk=job_id).update(is_active=is_active)
            if job_update:
                context = {
                    'message': "Job Updated Successfully",
                    'status': status.HTTP_200_OK,
                    'error': False
                }
            else:
                context = {
                    'message': "Something Went Wrong",
                    'status': status.HTTP_400_BAD_REQUEST,
                    'error': True
                }
            return Response(context)
        context = {
            'message': "Job_id Or Status Is Missing",
            'status': status.HTTP_400_BAD_REQUEST,
            'error': True
        }
        return Response(context)


class QuestionFilterAPI(APIView):
    queryset = Question.objects.all()

    def post(self, request, *args, **kwargs):
        job_id = request.data.get('job_id', None)
        order_by = request.data.get('order_by', None)
        status1 = request.data.get('status', None)
        question_search = request.data.get('question', None)
        if status1 or status1 == 0:
            status1 = str(status1)
        user = request.user
        if question_search:
            question_filter_data = self.queryset.filter(
                (Q(user=user) | Q(job_applied__job__user=user)) & Q(job_applied__job_id=job_id) & Q(
                    question__icontains=question_search)).order_by('-modified')
            second_serializer = QuestionSerializer(question_filter_data, many=True)
            context = {
                'data': second_serializer.data,
                'message': 'success',
                'error': False,
                'status': status.HTTP_200_OK
            }
            return Response(context)
        if order_by == "oldest":
            # ------ for oldest ----#
            messages = self.queryset
            if status1 == '0':
                # ------ all questions ----#
                messages = self.queryset.filter(
                    (Q(user=user) | Q(job_applied__job__user=user)) & Q(job_applied__job_id=job_id))
            if status1 == '1':
                # ------ answered questions ------#
                messages = self.queryset.filter(
                    (Q(user=user) | Q(job_applied__job__user=user)) & Q(job_applied__job_id=job_id) & Q(status=1))
            if status1 == '2':
                # ---- unaswered questions -------#
                messages = self.queryset.filter(
                    (Q(user=user) | Q(job_applied__job__user=user)) & Q(job_applied__job_id=job_id) & Q(status=2))
            messages = messages.order_by('modified')
            serializer = QuestionSerializer(messages, many=True, context={'request': request})
            context = {
                'data': serializer.data,
                'message': 'success',
                'error': False,
                'status': status.HTTP_200_OK
            }
            return Response(context)
        if order_by == 'newest':
            # ------- for newest -----#
            messages = self.queryset
            if status1 == '0':
                # ------ all questions ----#
                messages = self.queryset.filter(
                    (Q(user=user) | Q(job_applied__job__user=user)) & Q(job_applied__job_id=job_id))
            if status1 == '1':
                # ------ answered questions ------#
                messages = self.queryset.filter(
                    (Q(user=user) | Q(job_applied__job__user=user)) & Q(job_applied__job_id=job_id) & Q(status=1))
            if status1 == '2':
                # ---- unaswered questions -------#
                messages = self.queryset.filter(
                    (Q(user=user) | Q(job_applied__job__user=user)) & Q(job_applied__job_id=job_id) & Q(status=2))
            messages = messages.order_by('-modified')
            serializer = QuestionSerializer(messages, many=True, context={'request': request})
            context = {
                'data': serializer.data,
                'message': 'success',
                'error': False,
                'status': status.HTTP_200_OK
            }
            return Response(context)
        return Response({'message': "Something Went Wrong", 'status': status.HTTP_200_OK, 'error': True},
                        status=status.HTTP_400_BAD_REQUEST)


# --------------------------------------------- jobdetails muskesh ------------------------#

class JobShareDetails(APIView):
    def post(self, request, *args, **kwargs):
        job_id = request.data.get('id', None)
        email = request.data.get('email', None)
        if job_id and email:
            user = CustomUser.objects.filter(email=email).first()
            job_details = Job.objects.filter(pk=job_id).first()
            if job_details:
                skills = ''
                for i in job_details.skills.all():
                    skills += f'<div style="/* width:100%; */float:left;margin-right: 8px;margin-bottom: 5px;"><button style="background-color: rgba(36,114,252,0.08);border-radius: ' \
                              f'30px;font-style: normal;font-weight: 600;font-size: 14px;line-height: 18px;text-align: ' \
                              f'center;border: none;color: #2472fc;padding: 8px 20px 8px 20px;">' \
                              f'{i.skill_name}</button></div> '
                from_email = Email(SEND_GRID_FROM_EMAIL)
                to_email = To(email)
                not_user = ''
                try:
                    subject = "Shared Job details"
                    content = Content("text/html",
                                      f'<div style="background: rgba(36, 114, 252, 0.06) !important"><table style="font: Arial, sans-serif; border-collapse: collapse;width: 600px;margin: 0 auto;"width="600" cellpadding="0" cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 0"><div style="padding: 34px 44px;border-radius: 8px !important;background: #fff;border: 1px solid #dddddd5e;margin-bottom: 50px;margin-top: 50px;"><div class="email-logo"><img style="width: 165px" src="{LOGO_122_SERVER_PATH}"></div><a href="#"></a><div class="welcome-text"style="padding-top: 50px"><h1 style="font: 24px;color:#000000"> Hello {user.get_full_name() if user else not_user},</h1></div><div class="welcome-paragraph"><div style="padding: 10px 0px;font-size: 16px;color: #384860;">  You have been invited for this Job:</div><div style="box-shadow: 0px 4px 40px rgb(36 114 252 / 6%);border-radius: 0px 8px 8px 0;margin-top: 10px;display: flex;"><div style="width: 13px;background-color: rgb(36, 114, 252);border-radius: 50px;"></div><div><div style="padding: 20px 0"><div><h1 style="font: 24px;color:#000000">{job_details.title}</h1></div><div style="padding: 13px 0px;font-size: 16px;color: #384860;">{job_details.description[:200]}</div><div></div><div  style="font-size: 16px;line-height: 19px;color: rgba(0, 0, 0, 0.7);font-weight: bold;padding: 15px 0px;">Due on:<span style="padding: 0px 12px">{job_details.job_due_date}</span></div><div style="/* display:flex; */width: 100%;float: left;">{skills}</div></div></div></div><div style="padding:10px 0px;font-size:16px;color:#384860;float: left;width: 100%;">Please click the link below to view the new updates.</div><div style="padding:20px 0px;font-size:16px;color:#384860;float: left;width: 100%;margin-bottom: 30px ">Sincerely,<br />The Adifect Team</div></div><div style="padding-top: 40px"><a href="{FRONTEND_SITE_URL}/?redirect=guest-job/{StringEncoder.encode(self, job_details.id)}"<button style="height: 56px;padding: 15px 44px;background: #2472fc;border-radius: 8px;border-style: none;color: white;font-size: 16px; text-decoration: none;">View Job</button></a></div><div style="padding: 50px 0px"class="email-bottom-para"><div style="padding: 20px 0px;font-size: 16px;color: #384860;">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect? <a href="#"><span style="text-decoration: underline">Unsubscribe.</span></a></div><div style="font-size: 16px; color: #384860">© 2022 Adifect</div></div></div></td></tr></tbody></table></div>')
                    data = send_email(from_email, to_email, subject, content)
                    if data:
                        return Response({'message': 'mail Send successfully, Please check your mail'},
                                        status=status.HTTP_200_OK)
                    else:

                        return Response({'message': 'Something Went Wrong'}, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    print(e)
        return Response({'message': 'Something went wrong'}, status=status.HTTP_200_OK)

        # if not user:
        #     try:
        #         subject = "Shared Job details"
        #         content = Content("text/html",
        #                           f'<div style="background: rgba(36, 114, 252, 0.06) !important"><table style="font: Arial, sans-serif; border-collapse: collapse;width: 600px;margin: 0 auto;"width="600" cellpadding="0" cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 0"><div style="padding: 34px 44px;border-radius: 8px !important;background: #fff;border: 1px solid #dddddd5e;margin-bottom: 50px;margin-top: 50px;"><div class="email-logo"><img style="width: 165px" src="{LOGO_122_SERVER_PATH}"></div><a href="#"></a><div class="welcome-text"style="padding-top: 80px"><h1 style="font: 24px;color:#000000"> Hello ,</h1></div><div class="welcome-paragraph"><div style="padding: 10px 0px;font-size: 16px;color: #384860;">  You have been invited for this Job:</div><div style="box-shadow: 0px 4px 40px rgb(36 114 252 / 6%);border-radius: 0px 8px 8px 0;margin-top: 10px;display: flex;"><div style="width: 13px;background-color: rgb(36, 114, 252);border-radius: 50px;"></div><div><div style="padding: 20px"><div><h1 style="font: 24px;color:#000000">{job_details.title}</h1></div><div style="padding: 13px 0px;font-size: 16px;color: #384860;">{job_details.description[:200]}</div><div></div><div  style="font-size: 16px;line-height: 19px;color: rgba(0, 0, 0, 0.7);font-weight: bold;padding: 15px 0px;">Due on:<span style="padding: 0px 12px">{job_details.job_due_date}</span></div><div style="display: flex">{skills}</div></div></div></div><div style="padding: 10px 0px;font-size: 16px;color: #384860;">Please click the link below to view the new updates.</div><div style="padding: 20px 0px;font-size: 16px;color: #384860;"></div>Sincerely,<br />The Adifect Team</div><div style="padding-top: 40px"><a href="{FRONTEND_SITE_URL}/jobs/details/{job_details.id}"<button style="height: 56px;padding: 15px 44px;background: #2472fc;border-radius: 8px;border-style: none;color: white;font-size: 16px;">View Job</button></a></div><div style="padding: 50px 0px"class="email-bottom-para"><div style="padding: 20px 0px;font-size: 16px;color: #384860;">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect? <a href="#"><span style="text-decoration: underline">Unsubscribe.</span></a></div><div style="font-size: 16px; color: #384860">© 2022 Adifect</div></div></div></td></tr></tbody></table></div>')
        #         data = send_email(from_email, to_email, subject, content)
        #         if data:
        #             return Response({'message': 'mail Send successfully, Please check your mail'},
        #                             status=status.HTTP_200_OK)
        #         else:
        #
        #             return Response({'message': 'Something Went Wrong'}, status=status.HTTP_400_BAD_REQUEST)
        #     except Exception as e:
        #         print(e)


# -------------------------------------------- end -------------------------------#
@permission_classes([IsAuthenticated])
class AgencyJoblistViewSet(viewsets.ModelViewSet):
    serializer_class = EditProfileSerializer
    queryset = CustomUser.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = CustomUser.objects.filter(role=2, is_trashed=False)
        serializer = EditProfileSerializer(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)


@permission_classes([IsAuthenticated])
class AdminJobListViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    queryset = Job.objects.all()
    job_template_attach = JobTemplateAttachmentsSerializer
    pagination_class = FiveRecordsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['user']
    search_fields = ['=user', ]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        job_data = queryset.exclude(status=0).order_by('-modified')
        paginated_data = self.paginate_queryset(job_data)
        serializer = JobsWithAttachmentsSerializer(paginated_data, many=True, context={'request': request})
        return self.get_paginated_response(data=serializer.data)


# ----------------------------------- end update ------------------------------------------#
@permission_classes([IsAuthenticated])
class UserSkillsViewSet(viewsets.ModelViewSet):
    serializer_class = UserSkillsSerializer
    queryset = UserSkills.objects.all().order_by('-modified')
    filterset_fields = ['user']
    search_fields = ['=user', ]

    def create(self, request, *args, **kwargs):
        # serializer.is_valid(raise_exception=True)
        skills = request.data.get('skills')
        user = request.data.get('user', None)
        context = {}
        if user:
            UserSkills.objects.filter(user_id=user).delete()
            for i in skills:
                UserSkills.objects.create(user_id=user, skills_id=i)
            context = {
                'message': 'skills Added Successfully',
                'status': status.HTTP_201_CREATED,
                'error': False
            }
        else:
            context = {
                'message': 'Something Went Wrong',
                'status': status.HTTP_201_CREATED,
                'error': True
            }
        return Response(context)


# @permission_classes([IsAuthenticated])
class JobInviteViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    queryset = Job.objects.all

    def retrieve(self, request, pk=None):
        id = pk
        if id is not None:
            job_data = Job.objects.get(id=pk)
            serializer = UmauthenticatedUserJobViewSerializer(job_data, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)


@permission_classes([IsAdmin])
class AgencyListViewSet(viewsets.ModelViewSet):
    serializer_class = UserListSerializer
    queryset = CustomUser.objects.all().order_by('-date_joined')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['id', 'username', 'first_name']
    search_fields = ['=username', '=first_name']
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).filter(role=2, is_trashed=False)
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)


@permission_classes([IsAdmin])
class AgencyJobListViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    queryset = Job.objects.all()
    job_template_attach = JobTemplateAttachmentsSerializer
    pagination_class = FiveRecordsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['user', 'title', 'company']
    search_fields = ['=user', '=title', '=company']
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        job_data = queryset.exclude(status=0).order_by('-modified')
        job_count = job_data.count()
        paginated_data = self.paginate_queryset(job_data)
        serializer = JobsWithAttachmentsSerializer(paginated_data, many=True, context={'request': request})
        job_id = job_data.values_list('id', flat=True)
        applied = JobApplied.objects.filter(job_id__in=list(job_id), job__is_trashed=False, status=2).order_by(
            'job_id').distinct('job_id').values_list('id', flat=True).count()
        # return self.get_paginated_response(data=serializer.data)
        Context = {
            'Total_Job_count': job_count,
            'In_progress_jobs': applied,
            'data': serializer.data,
        }
        return self.get_paginated_response(Context)
        # return Response(Context)


@permission_classes([IsAdmin])
class AgencyWorkflowViewSet(viewsets.ModelViewSet):
    serializer_class = WorksFlowSerializer
    queryset = WorksFlow.objects.filter(is_trashed=False).order_by('-modified')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    # pagination_class = FiveRecordsPagination
    filterset_fields = ['company', 'agency', 'name']
    search_fields = ['=agency', '=name']
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # paginated_data = self.paginate_queryset(queryset)
        serializer = WorksFlowSerializer(queryset, many=True, context={'request': request})
        # return self.get_paginated_response(data=serializer.data)
        return Response(data=serializer.data)


@permission_classes([IsAdmin])
class AgencyCompanyListViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    queryset = Company.objects.filter(is_trashed=False).order_by('-modified')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    # pagination_class = FiveRecordsPagination
    filterset_fields = ['agency']
    search_fields = ['=agency', '=name']
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # paginated_data = self.paginate_queryset(queryset)
        serializer = CompanySerializer(queryset, many=True, context={'request': request})
        # return self.get_paginated_response(data=serializer.data)
        return Response(data=serializer.data)


@permission_classes([IsAdmin])
class AgencyInviteListViewSet(viewsets.ModelViewSet):
    serializer_class = InviteMemberSerializer
    queryset = InviteMember.objects.all().exclude(user=None).order_by('-modified')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    # pagination_class = FiveRecordsPagination
    filterset_fields = ['agency', 'user', 'company']
    search_fields = ['=agency', '=user']
    http_method_names = ['get', 'put', 'patch']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # paginated_data = self.paginate_queryset(queryset)
        # serializer = InviteMemberSerializer(paginated_data, many=True, context={'request': request})
        # return self.get_paginated_response(data=serializer.data)
        serializer = InviteMemberSerializer(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_blocked = request.data['is_blocked']
        instance.save()
        print(request.data['is_blocked'])
        context = {
            'message': 'Updated Succesfully',
            'status': status.HTTP_200_OK,
        }
        return Response(context)


#########                           job block by admin(M.B)                      #########

@permission_classes([IsAdmin])
class JobBlock(APIView):
    def post(self, request, *args, **kwargs):
        job_id = request.data.get('job_id', None)
        status1 = request.data.get('status', None)
        if job_id and (status1 or status1 == False):
            job = Job.objects.filter(id=job_id).update(is_blocked=status1)
            if job:
                data = {"message": "Job status updated successfully", "status": "success", "error": False}
                return Response(data, status=status.HTTP_200_OK)
            data = {"message": "Something Went Wrong", "status": "failed", "error": True}
        else:
            data = {"data": "Job id Or Status Is Missing", "status": "error", "error": True}
        return Response(data, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAdmin])
class CreatorListViewSet(viewsets.ModelViewSet):
    serializer_class = UserListSerializer
    queryset = CustomUser.objects.filter(role=1).order_by('date_joined')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    pagination_class = FiveRecordsPagination
    filterset_fields = ['id', 'username', 'first_name']
    search_fields = ['=username', '=first_name']
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        paginated_data = self.paginate_queryset(queryset)
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return self.get_paginated_response(data=serializer.data)


@permission_classes([IsAdmin])
class CreatorJobListViewSet(viewsets.ModelViewSet):
    queryset = JobApplied.objects.all()
    pagination_class = FiveRecordsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['user']
    search_fields = ['=user']
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        paginated_data = self.paginate_queryset(queryset)
        job_id = queryset.values_list('job_id', flat=True)
        job_data = Job.objects.filter(id__in=list(job_id))
        serializer = JobsWithAttachmentsSerializer(job_data, many=True, context={'request': request})
        Context = {
            'status': status.HTTP_200_OK,
            'data': serializer.data,
            'error': False
        }
        return self.get_paginated_response(Context)


class UserPortfolioViewset(viewsets.ModelViewSet):
    serializer_class = UserPortfolioSerializer
    queryset = CustomUserPortfolio.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    pagination_class = FourRecordsPagination
    filterset_fields = ['id', 'user']
    search_fields = ['id', 'user']
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        paginated_data = self.paginate_queryset(queryset)
        serializer = self.serializer_class(paginated_data, many=True, context={'request': request})
        return self.get_paginated_response(data=serializer.data)


class AgencyJobDetailsViewSet(viewsets.ModelViewSet):
    serializer_class = MyProjectSerializer
    queryset = JobApplied.objects.filter(job__is_trashed=False)
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    # ordering_fields = ['modified', 'job__job_due_date', 'job__created', 'job__modified']
    # ordering = ['job__job_due_date', 'job__created', 'job__modified', 'modified']
    filterset_fields = ['status', 'job__company', 'job__user']
    search_fields = ['=status', ]
    pagination_class = FiveRecordsPagination
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        ordering = request.GET.get('ordering', None)
        filter_data = queryset.filter(
            pk__in=Subquery(
                queryset.order_by('job_id').distinct('job_id').values('pk')
            )
        ).order_by(ordering)
        serializer = MyProjectSerializer(filter_data, many=True, context={'request': request})
        return Response(data=serializer.data)


class AdminCompanyBlock(APIView):
    def post(self, request, *args, **kwargs):
        company_id = request.data.get('company_id', None)
        status1 = request.data.get('status', None)
        context = {}
        if (company_id and status1) or (company_id and status1 == False):
            company = Company.objects.filter(id=company_id).update(is_blocked=status1)
            job = Job.objects.filter(company=company_id).update(is_blocked=status1)
            workflow = WorksFlow.objects.filter(company=company_id).update(is_blocked=status1)
            if company:
                context = {'message': 'Company status updated Successfully',
                           'error': False,
                           'status': status.HTTP_200_OK
                           }
                return Response(context, status=status.HTTP_200_OK)


        else:
            context = {'message': 'Something Went Wrong',
                       'error': True,
                       'status': status.HTTP_400_BAD_REQUEST
                       }
        return Response(context)


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
# --------------------------------------------------------------- new Job Submit ------------------------------------------------------------#

def JobWorkSubmitEmail(user, work,approved=None,moved=None):
    try:
        if not work.job_applied.user.profile_img:
            profile_image = ''
        else:
            profile_image = work.job_applied.user.profile_img.url
        img_url = ''
        if approved:
            message = f'You work is approved by {approved.approver.user.user.username} for Stage-{int(approved.workflow_stage.order)+1} '
        else:
            message = 'You have Submitted this work for Approval!'
        if moved:
            message = f'You work is Moved for Stage-{int(moved.workflow_stage.order)+1} '

        for j in JobWorkAttachments.objects.filter(job_work=work):
            img_url += f'<img style="width: 100.17px;height:100px;margin: 10px 10px 0px 0px;border-radius: 16px;" src="{j.work_attachments.url}" />'
        subject = "Job Work Submit"
        content = Content("text/html",
                          f'<div style="background: rgba(36, 114, 252, 0.06) !important"><table style="font: Arial, sans-serif;border-collapse: collapse;width: 600px;margin: 0 auto;"width="600"cellpadding="0"cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 0"><div style="padding: 34px 44px;border-radius: 8px !important;background: #fff;border: 1px solid #dddddd5e;margin-bottom: 50px;margin-top: 50px;"><div class="email-logo"><img style="width: 165px"src="{LOGO_122_SERVER_PATH}"/></div><a href="#"></a><div class="welcome-text" style="padding-top: 80px"><h1 style="font: 24px">Hello {user.username},</h1></div><div class="welcome-paragraph"><div style="padding: 10px 0px;font-size: 16px;color: #384860;">{message} Please view the asset below or click the link to be navigated to the Adifect site.</div><div style="background-color: rgba(36, 114, 252, 0.1);border-radius: 8px;"><div style="padding: 20px"><div style="display: flex;align-items: center;"><img style="width: 40px;height: 40px;border-radius: 50%;" src="{profile_image}" /><span style="font-size: 14px;color: #2472fc;font-weight: 700;margin-bottom: 0px;padding: 10px 14px;">{work.job_applied.user.username} delivered the work</span><span style="font-size: 12px;color: #a0a0a0;font-weight: 500;padding: 10px 14px;margin-bottom: 0px;">{work.created.strftime("%B %d, %Y %H:%M:%p")}</span></div><div style="font-size: 16px;color: #000000;padding-left: 54px;">{work.message}</div><div style="padding: 11px 54px 0px">{img_url}</div><div style="display: flex"></div></div></div><div style="padding: 20px 0px;font-size: 16px;color: #384860;"></div>Sincerely,<br />The Adifect Team</div><div style="padding-top: 40px"class="create-new-account"><a href="{FRONTEND_SITE_URL}/?redirect=jobs/details/{work.job_applied.job.id}"><button style="height: 56px;padding: 15px 44px;background: #2472fc;border-radius: 8px;border-style: none;color: white;font-size: 16px;">View Asset on Adifect</button></a></div><div style="padding: 50px 0px"class="email-bottom-para"><div style="padding: 20px 0px;font-size: 16px;color: #384860;">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect? <a href="#"><span style="text-decoration: underline">Unsubscribe.</span></a></div><div style="font-size: 16px; color: #384860">© 2022 Adifect</div></div></div></td></tr></tbody></table></div>')
        data = send_email(Email(SEND_GRID_FROM_EMAIL), user.email, subject, content)
    except Exception as e:
        print("herrere")
        print(e)


def JobWorkApprovalEmail(approver, work):
    try:
        if not work.job_applied.user.profile_img:
            profile_image = ''
        else:
            profile_image = work.job_applied.user.profile_img.url
        img_url = ''
        for j in JobWorkAttachments.objects.filter(job_work=work):
            img_url += f'<img style="width: 100.17px;height:100px;margin: 10px 10px 0px 0px;border-radius: 16px;" src="{j.work_attachments.url}"/>'
        subject = "Job Work Approver Submit"
        content = Content("text/html",
                          f'<div style="background: rgba(36, 114, 252, 0.06) !important"><table style="font: Arial, sans-serif;border-collapse: collapse;width: 600px;margin: 0 auto;"width="600"cellpadding="0"cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 0"><div style="padding: 34px 44px;border-radius: 8px !important;background: #fff;border: 1px solid #dddddd5e;margin-bottom: 50px;margin-top: 50px;"><div class="email-logo"><img style="width: 165px"src="{LOGO_122_SERVER_PATH}"/></div><a href="#"></a><div class="welcome-text" style="padding-top: 80px"><h1 style="font: 24px">Hello {approver.username},</h1></div><div class="welcome-paragraph"><div style="padding: 10px 0px;font-size: 16px;color: #384860;">You have a new Approval that needs your attention! Please view the asset below or click the link to be navigated to the Adifect site.</div><div style="background-color: rgba(36, 114, 252, 0.1);border-radius: 8px;"><div style="padding: 20px"><div style="display: flex;align-items: center;"><img style="width: 40px;height: 40px;border-radius: 50%;" src="{profile_image}" /><span style="font-size: 14px;color: #2472fc;font-weight: 700;margin-bottom: 0px;padding: 10px 14px;">{work.job_applied.user.username} delivered the work</span><span style="font-size: 12px;color: #a0a0a0;font-weight: 500;margin-bottom: 0px;padding: 10px 14px;">{work.created.strftime("%B %d, %Y %H:%M:%p")}</span></div><div style="font-size: 16px;color: #000000;padding-left: 54px;">{work.message}</div><div style="padding: 11px 54px 0px">{img_url}</div><div style="display: flex"></div></div></div><div style="padding: 20px 0px;font-size: 16px;color: #384860;"></div>Sincerely,<br />The Adifect Team</div><div style="padding-top: 40px"class="create-new-account"><a href="{FRONTEND_SITE_URL}/?redirect=jobs/details/{work.job_applied.job.id}"><button style="height: 56px;padding: 15px 44px;background: #2472fc;border-radius: 8px;border-style: none;color: white;font-size: 16px;">View Asset on Adifect</button></a></div><div style="padding: 50px 0px"class="email-bottom-para"><div style="padding: 20px 0px;font-size: 16px;color: #384860;">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect? <a href="#"><span style="text-decoration: underline">Unsubscribe.</span></a></div><div style="font-size: 16px; color: #384860">© 2022 Adifect</div></div></div></td></tr></tbody></table></div>')
        data = send_email(Email(SEND_GRID_FROM_EMAIL), approver.email, subject, content)
    except Exception as e:
        print(e)


def JobWorkEditEmail(user, work):
    try:
        if not work.job_applied.user.profile_img:
            profile_image = ''
        else:
            profile_image = work.job_applied.user.profile_img.url
        img_url = ''
        for j in JobWorkAttachments.objects.filter(job_work=work):
            img_url += f'<img style="width: 100.17px;height:100px;margin: 10px 10px 0px 0px;border-radius: 16px;" src="{j.work_attachments.url}" />'
        subject = "Job Work Submit"
        content = Content("text/html",
                          f'<div style="background: rgba(36, 114, 252, 0.06) !important"><table style="font: Arial, sans-serif;border-collapse: collapse;width: 600px;margin: 0 auto;"width="600"cellpadding="0"cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 0"><div style="padding: 34px 44px;border-radius: 8px !important;background: #fff;border: 1px solid #dddddd5e;margin-bottom: 50px;margin-top: 50px;"><div class="email-logo"><img style="width: 165px"src="{LOGO_122_SERVER_PATH}"/></div><a href="#"></a><div class="welcome-text" style="padding-top: 80px"><h1 style="font: 24px">Hello {user.username},</h1></div><div class="welcome-paragraph"><div style="padding: 10px 0px;font-size: 16px;color: #384860;">You have received request for edit this work. Please view the asset below or click the link to be navigated to the Adifect site.</div><div style="background-color: rgba(36, 114, 252, 0.1);border-radius: 8px;"><div style="padding: 20px"><div><img style="width: 40px;height: 40px;border-radius: 50%;" src="{profile_image}" /><span style="font-size: 14px;color: #2472fc;font-weight: 700;margin-bottom: 0px;padding: 0px 14px;">{work.job_applied.user.username} delivered the work</span><span style="font-size: 12px;color: #a0a0a0;font-weight: 500;margin-bottom: 0px;">{work.created.strftime("%B %d, %Y %H:%M:%p")}</span></div><div style="font-size: 16px;color: #000000;padding-left: 54px;">{work.message}</div><div style="padding: 11px 54px 0px">{img_url}</div><div style="display: flex"></div></div></div><div style="padding: 20px 0px;font-size: 16px;color: #384860;"></div>Sincerely,<br />The Adifect Team</div><div style="padding-top: 40px"class="create-new-account"><a href="{FRONTEND_SITE_URL}/jobs/details/{work.job_applied.job.id}"><button style="height: 56px;padding: 15px 44px;background: #2472fc;border-radius: 8px;border-style: none;color: white;font-size: 16px;">View Asset on Adifect</button></a></div><div style="padding: 50px 0px"class="email-bottom-para"><div style="padding: 20px 0px;font-size: 16px;color: #384860;">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect? <a href="#"><span style="text-decoration: underline">Unsubscribe.</span></a></div><div style="font-size: 16px; color: #384860">© 2022 Adifect</div></div></div></td></tr></tbody></table></div>')
        data = send_email(Email(SEND_GRID_FROM_EMAIL), user.email, subject, content)
    except Exception as e:
        print(e)


@permission_classes([IsAuthenticated])
class JobWorkSubmitViewSet(viewsets.ModelViewSet):
    serializer_class = SubmitJobWorkSerializer
    queryset = SubmitJobWork.objects.all()
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['job_applied__job']

    # search_fields = ['=status', ]
    # pagination_class = FiveRecordsPagination
    # http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # ----- work flow for approvals detail -----#
            job = serializer.validated_data['job_applied'].job
            self.perform_create(serializer)
            latest_work = SubmitJobWork.objects.latest('id')
            attachment = request.FILES.getlist('work_attachments')
            activity_attachment = request.FILES.getlist('work_activity_attachments')
            activity = JobActivity.objects.create(job=job, activity_status=2,
                                                  user=serializer.validated_data['job_applied'].user)
            work_activity = JobWorkActivity.objects.create(job_activity_chat=activity, job_work=latest_work,
                                                           work_activity='submit_approval',
                                                           message_work=latest_work.message)
            if attachment:
                for ind, i in enumerate(attachment):
                    JobWorkAttachments.objects.create(job_work=latest_work, work_attachments=i)
                    JobWorkActivityAttachments.objects.create(work_activity=work_activity,
                                                              work_attachment=activity_attachment[ind])
            JobWorkSubmitEmail(latest_work.job_applied.user, latest_work)
            JobApplied.objects.filter(pk=serializer.validated_data['job_applied'].id).update(status=3)

            if job.workflow:
                workflow = job.workflow
                # ----- stage 1 --------#

                if workflow.stage_workflow.all():
                    first_stage = workflow.stage_workflow.all().order_by('order')[0]
                    # if MemberApprovals.objects.filter(workflow_stage=first_stage, status=2):
                    #     return Response({'message': 'Your Work Is Rejected', 'error': True})
                    created = 0
                    for j in first_stage.approvals.all():
                        created = MemberApprovals.objects.create(job_work=latest_work, approver=j,
                                                                 workflow_stage=first_stage)
                        JobWorkApprovalEmail(j.user.user, latest_work)
                    if created:
                        activity = JobActivity.objects.create(job=job, activity_status=3,
                                                              user=serializer.validated_data['job_applied'].user)
                        JobWorkActivity.objects.create(job_activity_chat=activity, job_work=latest_work,
                                                       work_activity='moved', workflow_stage=first_stage)
                # ------------ end -------#
            context = {
                'message': 'Job Successfully Submitted',
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

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            attachment = request.FILES.getlist('work_attachments')
            activity_attachment = request.FILES.getlist('work_activity_attachments')
            JobWorkAttachments.objects.filter(job_work=instance).delete()
            activity = JobActivity.objects.create(job=instance.job_applied.job, activity_status=2,
                                                  user=instance.job_applied.user)
            work_activity = JobWorkActivity.objects.create(job_activity_chat=activity, job_work=instance,
                                                           work_activity='submit_approval')
            for ind, i in enumerate(attachment):
                JobWorkAttachments.objects.create(job_work=instance, work_attachments=i)
                JobWorkActivityAttachments.objects.create(work_activity=work_activity,
                                                          work_attachment=activity_attachment[ind])
            JobWorkSubmitEmail(instance.job_applied.user, instance)

            stages_id_list = set(
                MemberApprovals.objects.filter(job_work=instance, workflow_stage__is_approval=True).values_list(
                    'workflow_stage', flat=True))
            if stages_id_list:
                revision_stage = Workflow_Stages.objects.filter(id__in=stages_id_list).order_by('order').first()
                revision_member = MemberApprovals.objects.filter(job_work=instance, workflow_stage=revision_stage)
                for i in revision_member:
                    JobWorkApprovalEmail(i.approver.user.user, instance)
                update = revision_member.update(status=0)
                if update:
                    activity = JobActivity.objects.create(job=instance.job_applied.job,
                                                          activity_status=3,
                                                          user=instance.job_applied.user)
                    JobWorkActivity.objects.create(job_activity_chat=activity, job_work=instance,
                                                   work_activity='moved', workflow_stage=revision_stage)

            else:
                rejected_member = MemberApprovals.objects.filter(job_work=instance, status=2).first()
                for i in rejected_member.workflow_stage.approvals.all():
                    JobWorkApprovalEmail(i.user.user, instance)
                update = MemberApprovals.objects.filter(job_work=instance,
                                                        workflow_stage=rejected_member.workflow_stage).update(
                    status=0)
                if update:
                    activity = JobActivity.objects.create(job=instance.job_applied.job,
                                                          activity_status=3,
                                                          user=instance.job_applied.user)
                    JobWorkActivity.objects.create(job_activity_chat=activity, job_work=instance,
                                                   work_activity='moved', workflow_stage=rejected_member.workflow_stage)

            context = {
                'message': 'Job Successfully Submitted',
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


@permission_classes([IsAuthenticated])
class MemberApprovalViewSet(viewsets.ModelViewSet):
    serializer_class = MemberApprovalsSerializer
    queryset = MemberApprovals.objects.all()
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['approver__user__user', 'status', 'job_work__job_applied__job']

    # search_fields = ['=status', ]
    # pagination_class = FiveRecordsPagination
    # http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        if serializer.is_valid():
            # ------------- response by member -----#
            self.perform_update(serializer)
            if serializer.validated_data['status']:
                # ----------------- create activity ------------------#
                if serializer.validated_data['status'] == 1:
                    activity = JobActivity.objects.create(job=instance.job_work.job_applied.job, activity_status=3,
                                                          user=instance.job_work.job_applied.user)
                    work_activity = JobWorkActivity.objects.create(job_activity_chat=activity, job_work=instance.job_work,
                                                   work_activity='approved', approver=instance,
                                                   workflow_stage=instance.workflow_stage)
                    if instance.job_work.job_submit_Work.all():
                        for i in instance.job_work.job_submit_Work.all():
                            JobWorkActivityAttachments.objects.create(work_activity=work_activity,
                                                                      work_attachment=i.work_attachments)
                    JobWorkSubmitEmail(instance.job_work.job_applied.user, instance.job_work,instance)
                    # SubmitJobWork.objects.filter(pk=instance.job_work.id).update(status=1)

                if serializer.validated_data['status'] == 2:
                    activity = JobActivity.objects.create(job=instance.job_work.job_applied.job, activity_status=3,
                                                          user=instance.job_work.job_applied.user)
                    work_activity = JobWorkActivity.objects.create(job_activity_chat=activity, job_work=instance.job_work,
                                                   work_activity='rejected', approver=instance,
                                                   workflow_stage=instance.workflow_stage)
                    SubmitJobWork.objects.filter(pk=instance.job_work.id).update(status=2)
                    MemberApprovals.objects.filter(job_work=instance.job_work,
                                                   workflow_stage=instance.workflow_stage).update(status=2)
                    if instance.job_work.job_submit_Work.all():
                        for i in instance.job_work.job_submit_Work.all():
                            JobWorkActivityAttachments.objects.create(work_activity=work_activity,
                                                                      work_attachment=i.work_attachments)

                    JobWorkEditEmail(instance.job_work.job_applied.user, instance.job_work)

            stage_id_list = []

            # --- checking for stages and move to next stage if conditions met -----#
            if not MemberApprovals.objects.filter(job_work=instance.job_work, status=2,
                                                  workflow_stage=instance.workflow_stage):
                total_stage_count = instance.job_work.job_applied.job.workflow.stage_workflow.all().count()
                for i in instance.job_work.job_applied.job.workflow.stage_workflow.all():
                    member_count = i.approvals.all().count()
                    if i.is_all_approval:
                        stage_clear = MemberApprovals.objects.filter(job_work=instance.job_work, workflow_stage=i,
                                                                     status=1).count()
                        if stage_clear == member_count:
                            stage_id_list.append(i.id)
                            # for j in i.approvals.all():
                            #     MemberApprovals.objects.create(job_work=instance.job_work, approver=j, workflow_stage=i)
                            # else:
                            #     # print("here no aproval clear")
                            #     if MemberApprovals.objects.filter(job_work=instance.job_work, workflow_stage=i):
                            #         stage_id_list.append(i.id)
                    else:
                        stage_clear = MemberApprovals.objects.filter(job_work=instance.job_work, workflow_stage=i,
                                                                     status=1).count()
                        if stage_clear:
                            stage_id_list.append(i.id)
                        # else:
                        #     if MemberApprovals.objects.filter(job_work=instance.job_work, workflow_stage=i):
                        #         print("here enter at not one least")
                        #         stage_id_list.append(i.id)
                        # for j in i.approvals.all():
                # ----- move to next stage -------#
                if stage_id_list:
                    new_stage = instance.job_work.job_applied.job.workflow.stage_workflow.exclude(
                        id__in=stage_id_list).order_by('order')
                    if new_stage:
                        if not MemberApprovals.objects.filter(job_work=instance.job_work, workflow_stage=new_stage[0],
                                                              status=0):
                            created = 0
                            for j in new_stage[0].approvals.all():
                                created = MemberApprovals.objects.create(job_work=instance.job_work, approver=j,
                                                                         workflow_stage=new_stage[0])
                                JobWorkApprovalEmail(j.user.user, instance.job_work)
                            if created:
                                JobWorkSubmitEmail(instance.job_work.job_applied.user, instance.job_work,None,created)
                                activity = JobActivity.objects.create(job=instance.job_work.job_applied.job,
                                                                      activity_status=3,
                                                                      user=instance.job_work.job_applied.user)
                                JobWorkActivity.objects.create(job_activity_chat=activity, job_work=instance.job_work,
                                                               work_activity='moved', workflow_stage=new_stage[0])
                # ------------- update task status if complete -------#
                if len(stage_id_list) == total_stage_count:
                    SubmitJobWork.objects.filter(pk=instance.job_work.id).update(status=1)
                    if instance.job_work.task is not None:
                        JobTasks.objects.filter(pk=instance.job_work.task).update(is_complete=True)

            context = {
                'message': 'Job Work Status Updated Succesfully',
                'status': status.HTTP_200_OK,
                'errors': serializer.errors,
                'data': serializer.data,
            }
            return Response(context, status=status.HTTP_200_OK)
        context = {
            'message': 'Error',
            'status': status.HTTP_400_BAD_REQUEST,
            'errors': serializer.errors,
        }
        return Response(context, status=status.HTTP_400_BAD_REQUEST)


'''
class JobWorkStatus(APIView):
    queryset = MemberApprovals.objects.all()

    def post(self, request, *args, **kwargs):
        job = request.data.get('job', None)
        user = request.data.get('user', None)

        if job and user:
           if JobApplied.objects.filter(Q(job_id=job) & Q(user_id=user) & Q(Q(status=2) | Q(status=3))):
                if SubmitJobWork.objects.filter(job_applied__job_id=job, job_applied__user_id=user, status=0):
                    context = {'Disable': True,
                               'error': False,
                               'status': status.HTTP_200_OK
                               }
                    return Response(context, status=status.HTTP_200_OK)
                else:
                    context = {'Disable': False,
                               'error': False,
                               'status': status.HTTP_200_OK
                               }
                    return Response(context, status=status.HTTP_200_OK)
           context = {'Disable': True,
                   'error': False,
                   'status': status.HTTP_200_OK
                   }
           return Response(context, status=status.HTTP_200_OK)
'''


class JobWorkStatus(APIView):
    queryset = MemberApprovals.objects.all()

    def post(self, request, *args, **kwargs):
        job = request.data.get('job', None)
        user = request.data.get('user', None)
        if job and user:
            task_id = JobTasks.objects.filter(job_id=job).values_list('id', flat=True)
            if JobApplied.objects.filter(Q(job_id=job) & Q(user_id=user) & Q(Q(status=2) | Q(status=3))):
                condition_first = SubmitJobWork.objects.filter(job_applied__job_id=job, job_applied__user_id=user,
                                                               status=0).values_list('task_id', flat=True)

                if len(list(task_id)) == 0:
                    task_id='0'
                if condition_first:
                    if len(list(task_id)) == len(list(condition_first)):
                        context = {'Disable': True,
                                   'error': False,
                                   'status': status.HTTP_200_OK
                                   }
                        return Response(context, status=status.HTTP_200_OK)
                    else:
                        context = {'Disable': False,
                                   'error': False,
                                   'status': status.HTTP_200_OK
                                   }
                        return Response(context, status=status.HTTP_200_OK)
                else:
                    context = {'Disable': False,
                               'error': False,
                               'status': status.HTTP_200_OK
                               }
                    return Response(context, status=status.HTTP_200_OK)
            context = {'Disable': True,
                       'error': False,
                       'status': status.HTTP_200_OK
                       }
            return Response(context, status=status.HTTP_200_OK)


class JobCompletedStatus(APIView):
    queryset = MemberApprovals.objects.all()

    def post(self, request, *args, **kwargs):
        job = request.data.get('job', None)
        if job:
            user_list = JobApplied.objects.filter(Q(job_id=job) & Q(Q(status=2) | Q(status=3))).values_list('user')
            completed_user_list = []
            task_id = JobTasks.objects.filter(job_id=job).values_list('id')
            for i in list(user_list):
                if task_id:
                    work = SubmitJobWork.objects.filter(job_applied__job_id=job, job_applied__user_id=i, status=1)
                    if len(list(work.values_list('task_id'))) == len(task_id):
                        completed_user_list.append({'user_id': work.first().job_applied.user.id,
                                                    'username': work.first().job_applied.user.get_full_name(),
                                                    'job_applied': work.first().job_applied.id})
                else:
                    work = SubmitJobWork.objects.filter(job_applied__job_id=job, job_applied__user_id=i, status=1)
                    if work:
                        completed_user_list.append({'user_id': work.first().job_applied.user.id,
                                                    'username': work.first().job_applied.user.get_full_name(),
                                                    'job_applied': work.first().job_applied.id})

            context = {'message': 'Completed Job Task User List',
                       'error': False,
                       'status': status.HTTP_200_OK,
                       'Data': completed_user_list
                       }
            return Response(context)
        else:
            context = {'message': 'No Job Found',
                       'error': True,
                       'status': status.HTTP_404_NOT_FOUND,
                       }
            return Response(context)


class JobActivityUserList(APIView):
    def get(self, request, *args, **kwargs):
        job_id = kwargs.get('job_id')
        if job_id:
            data = JobActivity.objects.filter(job_id=job_id, user__isnull=False)
            data_serilizer = JobActivityUserSerializer(data, many=True, context={'request': request})
            context = {
                'message': "Data Found",
                'status': status.HTTP_200_OK,
                'data': data_serilizer.data,
                'error': False
            }
        else:
            context = {
                'message': "Job Not Found",
                'status': status.HTTP_400_BAD_REQUEST,
                'error': True
            }
        return Response(context)


@permission_classes([IsAuthenticated])
class JobCompletedViewSet(viewsets.ModelViewSet):
    serializer_class = JobAppliedSerializer
    queryset = JobApplied.objects.filter(is_trashed=False)
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['job', 'status', 'user']

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        data = request.data
        if serializer.is_valid():
            self.perform_update(serializer)
            status_job = serializer.validated_data.get('status', None)
            test_status = None
            if status_job == 4:
                test_status = JobActivity.Type.Completed
            if test_status:
                JobActivity.objects.create(job=instance.job, activity_type=test_status, user=instance.user)
            work_attachment = JobWorkAttachments.objects.filter(job_work__job_applied=instance, job_work__status=1)
            if work_attachment:
                for i in work_attachment:
                    dam = DAM.objects.create(agency=instance.job.user, type=3, applied_creator=instance.user,company=instance.job.company)
                    try:
                        dam_media = DamMedia.objects.create(dam=dam, title=str(i.work_attachments.name).split('/')[-1],
                                                            media=i.work_attachments,tags=instance.job.tags)
                        if instance.job.skills is not None:
                            dam_media.skills.add(*instance.job.skills.all())
                            dam_media.save()

                    except Exception as e:
                        print(e)
            agency_user = instance.job.user.email
            from_email = Email(SEND_GRID_FROM_EMAIL)
            to_email = To(agency_user)
            skills = ''
            for i in instance.job.skills.all():
                skills += f'<div><button style="background-color:rgba(36,114,252,.08);border-radius:30px;font-style:normal;font-weight:600;font-size:15px;line-height:18px;text-align:center;border:none;color:#2472fc;padding:8px 20px 8px 20px">{i.skill_name}</button></div>'
            try:
                subject = "Job Completed."
                content = Content("text/html",
                                  f'<div style="background:rgba(36,114,252,.06)!important"><table style="font:Arial,sans-serif;border-collapse:collapse;width:600px;margin:0 auto" width="600" cellpadding="0" cellspacing="0"><tbody><tr><td style="width:100%;margin:36px 0 0"><div style="padding:34px 44px;border-radius:8px!important;background:#fff;border:1px solid #dddddd5e;margin-bottom:50px;margin-top:50px"><div class="email-logo"><img style="width:165px" src="{LOGO_122_SERVER_PATH}"></div><a href="#"></a><div class="welcome-text" style="padding-top:80px"><h1 style="font:24px">Congratulations! 🎉</h1></div><div class="welcome-paragraph"><div style="padding:10px 0;font-size:16px;color:#384860">You have a job that has just been completed!</div><div style="box-shadow:0 4px 40px rgb(36 114 252 / 6%);border-radius:0 8px 8px 0;margin-top:10px;display:flex"><div style="width:13px;background-color:#59cf65;border-radius:50px"></div><div><div style="padding:20px"><div><h1 style="font:24px">{instance.job.title}</h1></div><div style="padding:13px 0;font-size:16px;color:#384860">{instance.job.description}</div><div><button style="background-color:rgba(36,114,252,.08);border-radius:30px;font-style:normal;font-weight:600;font-size:15px;line-height:18px;text-align:center;border:none;color:#59cf65;padding:8px 20px 8px 20px">{instance.get_status_display()}</button></div><div style="font-size:16px;line-height:19px;color:rgba(0,0,0,.7);font-weight:700;padding:15px 0">Due on:<span style="padding:0 12px">{instance.job.job_due_date}</span></div><div style="display:flex"><div>{skills}<div style="padding:0 7px"></div><div></div></div></div></div></div><div style="padding:10px 0;font-size:16px;color:#384860">Please click the link below to view the completed job.</div><div style="padding:20px 0;font-size:16px;color:#384860"></div>Sincerely,<br>The Adifect Team</div><div style="padding-top:40px"><a href="{FRONTEND_SITE_URL}/?redirect=jobs/details/{instance.job.id}"><button style="height:56px;padding:15px 44px;background:#2472fc;border-radius:8px;border-style:none;color:#fff;font-size:16px">View Completed Job</button></div><div style="padding:50px 0" class="email-bottom-para"><div style="padding:20px 0;font-size:16px;color:#384860">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect?<a href="#"><span style="text-decoration:underline">Unsubscribe.</span></a></div><div style="font-size:16px;color:#384860">© 2022 Adifect</div></div></div></td></tr></tbody></table></div>')
                data = send_email(from_email, to_email, subject, content)
            except Exception as e:
                print(e)
            
            user = instance.user.email
            from_email = Email(SEND_GRID_FROM_EMAIL)
            to_email = To(user)
            try:
                subject = "Job Completed."
                content = Content("text/html",
                                  f'<div style="background:rgba(36,114,252,.06)!important"><table style="font:Arial,sans-serif;border-collapse:collapse;width:600px;margin:0 auto" width="600" cellpadding="0" cellspacing="0"><tbody><tr><td style="width:100%;margin:36px 0 0"><div style="padding:34px 44px;border-radius:8px!important;background:#fff;border:1px solid #dddddd5e;margin-bottom:50px;margin-top:50px"><div class="email-logo"><img style="width:165px" src="{LOGO_122_SERVER_PATH}"></div><a href="#"></a><div class="welcome-text" style="padding-top:80px"><h1 style="font:24px">Congratulations! 🎉</h1></div><div class="welcome-paragraph"><div style="padding:10px 0;font-size:16px;color:#384860">You have a job that has just been completed!</div><div style="box-shadow:0 4px 40px rgb(36 114 252 / 6%);border-radius:0 8px 8px 0;margin-top:10px;display:flex"><div style="width:13px;background-color:#59cf65;border-radius:50px"></div><div><div style="padding:20px"><div><h1 style="font:24px">{instance.job.title}</h1></div><div style="padding:13px 0;font-size:16px;color:#384860">{instance.job.description}</div><div><button style="background-color:rgba(36,114,252,.08);border-radius:30px;font-style:normal;font-weight:600;font-size:15px;line-height:18px;text-align:center;border:none;color:#59cf65;padding:8px 20px 8px 20px">{instance.get_status_display()}</button></div><div style="font-size:16px;line-height:19px;color:rgba(0,0,0,.7);font-weight:700;padding:15px 0">Due on:<span style="padding:0 12px">{instance.job.job_due_date}</span></div><div style="display:flex"><div>{skills}<div style="padding:0 7px"></div><div></div></div></div></div></div><div style="padding:10px 0;font-size:16px;color:#384860">Please click the link below to view the completed job.</div><div style="padding:20px 0;font-size:16px;color:#384860"></div>Sincerely,<br>The Adifect Team</div><div style="padding-top:40px"><a href="{FRONTEND_SITE_URL}/?redirect=jobs/details/{instance.job.id}"><button style="height:56px;padding:15px 44px;background:#2472fc;border-radius:8px;border-style:none;color:#fff;font-size:16px">View Completed Job</button></div><div style="padding:50px 0" class="email-bottom-para"><div style="padding:20px 0;font-size:16px;color:#384860">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect?<a href="#"><span style="text-decoration:underline">Unsubscribe.</span></a></div><div style="font-size:16px;color:#384860">© 2022 Adifect</div></div></div></td></tr></tbody></table></div>')
                data = send_email(from_email, to_email, subject, content)

            except Exception as e:
                print(e)

            context = {
                'message': 'Job Completed',
                'status': status.HTTP_201_CREATED,
                'errors': serializer.errors,
                'data': serializer.data,
            }
        else:
            context = {
                'message': 'You cannot update the proposal',
                'errors': serializer.errors,
            }
        return Response(context)
