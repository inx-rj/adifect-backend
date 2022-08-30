from locale import DAY_1
from sqlite3 import DatabaseError
from django.shortcuts import render
from .serializers import EditProfileSerializer,CategorySerializer,JobSerializer, JobAttachmentsSerializer, JobAppliedSerializer, IndustrySerializer, LevelSerializer, JobsWithAttachmentsSerializer, SkillsSerializer, JobFilterSerializer, CompanySerializer, JobHiredSerializer, ActivitiesSerializer, RelatedJobsSerializer, JobAppliedAttachmentsSerializer, UserListSerializer
from authentication.models import CustomUser, CustomUserPortfolio
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import viewsets
from .models import Category, Job, JobAttachments, JobApplied, Industry, Level, Skills, Company, JobHired, Activities, JobAppliedAttachments, ActivityAttachments
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import Http404, JsonResponse
from .pagination import FiveRecordsPagination
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
import operator
from functools import reduce
import os
from django.core.exceptions import ValidationError
from authentication.serializers import UserSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
# Create your views here.

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def validate_attachment(attachments):
    error =0
    for i in attachments:
        ext = os.path.splitext(i.name)[1] 
        valid_extensions =  ['.jpg', '.jpeg', '.png', '.doc', '.docx', '.mp4', '.pdf', '.xlsx','.csv']
        if not ext.lower() in valid_extensions:
            error +=1
    return error


@permission_classes([IsAuthenticated])
class ProfileEdit(APIView):
    serializer_class = EditProfileSerializer

    def get(self, request, *args, **kwargs):
        queryset = CustomUser.objects.filter(email=self.request.user.email)
        serlizer = EditProfileSerializer(queryset,many=True)   
        return Response(serlizer.data)

    def post(self,request,*args,**kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_data = serializer.validated_data
        user = CustomUser.objects.get(id=request.user.id)
        try:
            profile_image = request.FILES["profile_img"]
        except:
            profile_image = None
        user.profile_title=request.data.get('profile_title')
        user.profile_description=request.data.get('profile_description')
        user.profile_status=request.data.get('profile_status',None)
        user.first_name=request.data.get('first_name', None)
        user.last_name= request.data.get('last_name', None)
        video = request.data.get('video',None)
        user.preferred_communication_mode = request.data.get('preferred_communication_mode', None)
        portfolio = request.FILES.getlist('portfolio')
        remove_profile_img = request.data.get('remove_image', None) 
        remove_profile_video = request.data.get('remove_video', None)
        remove_portfolio_ids = request.data.getlist('remove_portfolio', None)

        if profile_image:
            user.profile_img= profile_image
        if remove_profile_img:
            user.profile_img= None
        if video:
            user.video= video
        if remove_profile_video:
            user.video= None
        if remove_portfolio_ids:
            for id in remove_portfolio_ids:
                CustomUserPortfolio.objects.filter(id=id).delete()
        if portfolio:
            portfolio_error = validate_portfolio_images(portfolio)
            if portfolio_error != 0:
                return Response({'message': "Invalid portfolio images"}, status=status.HTTP_400_BAD_REQUEST)
            for img in portfolio:
                CustomUserPortfolio.objects.create(user_id=request.user.id,portfolio_images=img)
                print(img)
              
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
        response = Response(context,status=status.HTTP_200_OK)
        return response


def validate_portfolio_images(images):
    error =0
    for img in images:
        ext = os.path.splitext(img.name)[1] 
        valid_extensions = ['.jpg', '.jpeg', '.png']
        if not ext.lower() in valid_extensions:
            error +=1
    return error
     
class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.all().order_by('-modified')

class IndustryViewSet(viewsets.ModelViewSet):
    serializer_class = IndustrySerializer
    queryset = Industry.objects.all().order_by('-modified')

class LevelViewSet(viewsets.ModelViewSet):
    serializer_class = LevelSerializer
    queryset = Level.objects.all().order_by('-modified')

class SkillsViewSet(viewsets.ModelViewSet):
    serializer_class = SkillsSerializer
    queryset = Skills.objects.all().order_by('-modified')


class UserListViewSet(viewsets.ModelViewSet):
    serializer_class = UserListSerializer
    queryset = CustomUser.objects.all()


class JobViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    queryset = Job.objects.all()
    pagination_class = FiveRecordsPagination
    
    def list(self,request, *args, **kwargs):
        job_data = Job.objects.all().order_by('-modified')
        paginated_data = self.paginate_queryset(job_data)
        serializer = JobsWithAttachmentsSerializer(paginated_data, many=True, context={'request': request})
        return self.get_paginated_response(data=serializer.data)

    def retrieve(self, request, pk=None):
        id = pk
        print(id)
        if id is not None:
            job_data = Job.objects.get(id=id)
            serializer = JobsWithAttachmentsSerializer(job_data, context={'request': request})
            return Response(serializer.data,  status=status.HTTP_201_CREATED)

    def create(self, request, *args, **kwargs):
        print(request.POST)
        serializer = self.get_serializer(data=request.data)
        image = request.FILES.getlist('image')
        sample_image = request.FILES.getlist('sample_image')
        if serializer.is_valid():
            serializer.fields.pop('image')
            serializer.fields.pop('sample_image')
            self.perform_create(serializer)

            job_id = Job.objects.latest('id')                   
            for i in image:
                JobAttachments.objects.create(job=job_id,job_images=i)
            for i in sample_image:
                JobAttachments.objects.create(job=job_id,work_sample_images=i)
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
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            if remove_image_ids:
                for id in remove_image_ids:
                    JobAttachments.objects.filter(id=id).delete()
            if image:
                serializer.fields.pop('image')   
                for i in image:
                    JobAttachments.objects.create(job_id=instance.id,job_images=i)
            if sample_image:
                serializer.fields.pop('sample_image')
                for i in sample_image:
                    JobAttachments.objects.create(job_id=instance.id,work_sample_images=i)
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
        for i in JobAttachments.objects.filter(job_id=instance.id):
            i.delete()
        self.perform_destroy(instance)
        
        context = {
            'message': 'Deleted Succesfully',
            'status': status.HTTP_204_NO_CONTENT,
            'errors': False,
        }
        return Response(context)



class JobAppliedViewSet(viewsets.ModelViewSet):
    serializer_class = JobAppliedSerializer
    queryset = JobApplied.objects.all()
    parser_classes = (MultiPartParser, FormParser, JSONParser)
  
    def list(self,request, *args, **kwargs):
        user = self.request.user
        job_applied_data = self.queryset.filter(user=user)
        serializer = self.serializer_class(job_applied_data, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)



    def create(self, request, *args, **kwargs):
        print(request.data)
        serializer = self.get_serializer(data=request.data)
        attachments = request.FILES.getlist('job_applied_attachments')
        data = request.data

        print(attachments)
        if serializer.is_valid():               
            if self.queryset.filter(Q(job=data['job']) & Q(user=data['user'])).exists():
                context = {
                        'message': 'Job already applied',
                    }
                return Response(context, status=status.HTTP_400_BAD_REQUEST)
            else:
                serializer.fields.pop('attachments')
                attachment_error = validate_attachment(attachments)
                if attachment_error != 0:
                    return Response({'message': "Invalid Attachment"}, status=status.HTTP_400_BAD_REQUEST)
                self.perform_create(serializer)
                job_applied_id = JobApplied.objects.latest('id')

                for i in attachments:
                    JobAppliedAttachments.objects.create(job_applied=job_applied_id,job_applied_attachments=i)
                context = {
                    'message': 'Job Applied Successfully',
                    'status': status.HTTP_201_CREATED,
                    'errors': serializer.errors,
                    'data': serializer.data,
                }

                return Response(context)
        else:
            return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class ActivitiesViewSet(viewsets.ModelViewSet):
    serializer_class = ActivitiesSerializer
    queryset = Activities.objects.all()
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def list(self,request, *args, **kwargs):
        activity_data = self.queryset.all()
        serializer = self.serializer_class(activity_data, many=True, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def create(self, request, *args, **kwargs):
        print(request.data)
        serializer = self.get_serializer(data=request.data)
        attachments = request.FILES.getlist('activity_attachments')

        if serializer.is_valid():               
                serializer.fields.pop('attachments')
                self.perform_create(serializer)
                activity_id = Activities.objects.latest('id')
                attachment_error = validate_attachment(attachments)
                if attachment_error != 0:
                    return Response({'message': "Invalid Attachment"}, status=status.HTTP_400_BAD_REQUEST)
                for i in attachments:
                    ActivityAttachments.objects.create(activities=activity_id,activity_attachments=i)
                context = {
                    'message': 'Message Sent Successfully',
                    'status': status.HTTP_201_CREATED,
                    'errors': serializer.errors,
                    'data': serializer.data,
                }

                return Response(context)
        else:
            return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class JobFilterApi(APIView):
    serializer_class = JobFilterSerializer
    def post(self,request,*args,**kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            request_data = serializer.validated_data
            price = request.data.get('price',None)
            skills = request.data.get('skills',None)
            tags = request.data.get('tags',None)
            jobs_filter_data = Job.objects.filter()
            if tags:
                q = tags.split(",")
                query = reduce(operator.or_, (Q(tags__icontains = item) for item in q))
                jobs_filter_data = jobs_filter_data.filter(
                    query
                )
            if skills:
                q =  skills.split(",")
                query = reduce(operator.or_, (Q(skills__skill_name__icontains = item) for item in q))
                jobs_filter_data = jobs_filter_data.filter(
                    query
                )
            if price:
                jobs_filter_data = jobs_filter_data.filter(price=price  
                )
            job_data = JobsWithAttachmentsSerializer(jobs_filter_data,many=True, context={'request': request})
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

    def get(self, request,*args,**kwargs):
        try:
            applied_data = JobApplied.objects.filter(user=self.request.user).values_list('job_id', flat=True)
            latest_job = Job.objects.exclude(id__in=list(applied_data)).latest('id')
            print("hittt")
            print(latest_job)
            data = JobsWithAttachmentsSerializer(latest_job,context={'request': request})    
            context = {
                    'message': 'Latest Job get Succesfully',
                    'status': status.HTTP_200_OK,
                    'true':True,
                    'data': data.data,
                }
            return Response(context)
        except Exception as E:
            print(E)
            context = {
                'false':False,
                'message': 'No jobs to show',
            }
            return Response(context)

class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    queryset = Company.objects.all().order_by('-modified')


@permission_classes([IsAuthenticated])

class JobHiredViewSet(viewsets.ModelViewSet):
    serializer_class = JobHiredSerializer
    queryset = JobHired.objects.all()
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status']
    search_fields = ['=status',]


# @permission_classes([IsAuthenticated])
class RelatedJobsAPI(APIView):

    def get(self, request, *args,**kwargs):
        if kwargs['title']:
            titles = kwargs['title'].split(' ')
            title_qs = reduce(operator.or_, (Q(title__icontains=x) for x in titles))
            queryset = Job.objects.filter(title_qs)            
            if queryset:
                serializer = RelatedJobsSerializer(queryset,many=True)   
                context = {
                    'message': 'Related Jobs',
                    'status': status.HTTP_200_OK,
                    'data': serializer.data,
                }
            else:
                context = {
                'message': 'No data found',
                'status': status.HTTP_200_OK,
                'data': "",
            }
            return Response(context)
        else:
            context = {
                'message': 'No data found',
                'status': status.HTTP_200_OK,
                'data': "",
            }
        return Response(context)



######  API for other PROJECT (Analytics)  ########
import paramiko
# import sys
class GetDataAPI(APIView):
    def post(self, request):
        print(request.data)
        context = {
                'message': "Data get Successfully",
                'status': status.HTTP_200_OK,
                'data': request.data,
            }
        return Response(context)


######  API for other PROJECT (Analytics)  ########
class PostDataAPI(APIView):
    def get(self, request):
        dbt_package = 'dbt-snowflake,dbt-bigquery' 
        host = '164.92.71.86'
        port = 22
        username = 'root'
        password = 'H#:OH$@;jh35;ohjq3r4a'
        gitUserName = 'vijaystudio45'
        gitOgrName = "Pivot-Computing"
        # gitOgrName = "vijaystudio45"
        gitToken = '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'
        gitRepo = 'analytics'

        DBUSERNAME = "doadmin"
        DBPASSWORD = "AVNS_SFVTUNdNyRG3cLNJ28Z"
        DBHOST = "vinod-db-postgresql-sfo3-86894-do-user-11542114-0.b.db.ondigitalocean.com:25060"
        DATABASENAME = "defaultdb"
        SECRET_KEY = "f$%5rw(n!g5y96jwp0(#zfuc)l%a*mi32i4qt2mz0jdt7^rs_h"

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=username, password=password)
        
        stdin, stdout, stderr = ssh.exec_command("sudo apt-get update && sudo apt-get -y install python3-pip")

        if dbt_package:
            packages = dbt_package.split(",")
            for package in packages:   
                stdin, stdout, stderr = ssh.exec_command("pip install package")

        stdin, stdout, stderr = ssh.exec_command("cd /var/ && mkdir www") 

        # Need to remove after setup.
        stdin, stdout, stderr = ssh.exec_command("cd /var/www && rm -rf analytics")

        stdin, stdout, stderr = ssh.exec_command("cd /var/www && git clone https://gitUserName:"+gitToken+"@github.com/"+gitOgrName+"/"+gitRepo+".git")

        stdin, stdout, stderr = ssh.exec_command("cd /var/www/"+gitRepo+"/ && pip3 install virtualenv && virtualenv venv")

        stdin, stdout, stderr = ssh.exec_command("cd /var/www/"+gitRepo+"/ && . venv/bin/activate && pip3 install -r requirements.txt")

        stdin, stdout, stderr = ssh.exec_command("cd /var/www/"+gitRepo+"/ && touch .env")

        # envFileContent = "DEBUG=True\nCORS_ORIGIN_ALLOW_ALL=True\nCORS_ALLOWED_ORIGINS=http://localhost:3000\nDEVELOPMENT_SERVER=True\nDATABASE_URL=postgres://"+DBUSERNAME+":"+DBPASSWORD+"@"+DBHOST+"/"+DATABASENAME+"\nSECRET_KEY="+SECRET_KEY+"\nREDIS_URL=redis://localhost:6379/1"

        envFileContent = "DEBUG=True\nCORS_ORIGIN_ALLOW_ALL=True\nCORS_ALLOWED_ORIGINS=http://localhost:3000\nDEVELOPMENT_SERVER=True\nDATABASE_URL=psql://"+DBUSERNAME+":"+DBPASSWORD+"@"+DBHOST+"/"+DATABASENAME+"\nSECRET_KEY="+SECRET_KEY+"\nREDIS_URL=redis://localhost:6379/1"


        ftp = ssh.open_sftp()
        my_file = ftp.file("/var/www/"+gitRepo+"/.env", 'w') # 'w' will open the file for editing - it will truncate whatever was there before
        my_file.write(envFileContent) # write whatever you wish to the file
        my_file.flush()
        ftp.close()

        stdin, stdout, stderr = ssh.exec_command("cd /var/www/"+gitRepo+"/ && pip3 install python-dotenv")

        stdin, stdout, stderr = ssh.exec_command("cd /var/www/"+gitRepo+"/ && sudo apt-get -y update")
        stdin, stdout, stderr = ssh.exec_command("cd /var/www/"+gitRepo+"/ && sudo apt-get -y install nginx")
        stdin, stdout, stderr = ssh.exec_command("cd /var/www/"+gitRepo+"/ && pip3 install -U pipenv")
        stdin, stdout, stderr = ssh.exec_command("cd /var/www/"+gitRepo+"/ && sudo apt install -y redis-server")
        stdin, stdout, stderr = ssh.exec_command("cd /var/www/"+gitRepo+"/ && sudo systemctl restart redis.service")

        stdin, stdout, stderr = ssh.exec_command("cd /var/www/"+gitRepo+"/ && pipenv shell")

        stdin, stdout, stderr = ssh.exec_command("cd /var/www/"+gitRepo+"/ && python3 manage.py makemigrations")

        stdin, stdout, stderr = ssh.exec_command("cd /var/www/"+gitRepo+"/ && python3 manage.py migrate")

        stdin, stdout, stderr = ssh.exec_command("cd /var/www/"+gitRepo+"/ && python3 manage.py runserver 0.0.0.0:8000")
        
        output = stdout.read()
        print(output)
        # ssh.close()
        context = {
                'message': "Success",
                'status': status.HTTP_200_OK,
                'data': output,
            }
        return Response(context)

class TestApi(APIView):
    def get(self, request):
         from django.db import connection, reset_queries
         devices = JobApplied.objects.all()
         print(devices)
         print(connection.queries)
         reset_queries()
         device_second = JobApplied.objects.all().values('user_id','links')
         print(device_second)
         print(connection.queries)
         reset_queries()
         context = {
             'message': "Success",
             'status': status.HTTP_200_OK,
         }
         return Response(context)



