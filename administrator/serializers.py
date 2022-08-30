import json
import os
from pyexpat import model
from statistics import mode
from rest_framework import serializers
from authentication.models import CustomUser, CustomUserPortfolio
from .models import Category, Job, JobAttachments, JobApplied, Industry, Level, Skills, Company, JobHired, Activities, Activities, JobAppliedAttachments, ActivityAttachments
from rest_framework.fields import SerializerMethodField

from authentication.serializers import UserSerializer
from .validators import validate_file_extension


class userPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUserPortfolio
        fields = '__all__'


class EditProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'profile_title', 'profile_description', 'role', 'video', 'profile_img', 'profile_status', 'profile_status','preferred_communication_mode']


        extra_kwargs = {
            'email': {'read_only': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
   
    def __init__(self, *args, **kwargs):
        super(EditProfileSerializer, self).__init__(*args, **kwargs)
        self.fields['profile_img'].error_messages['invalid_image'] = u'Unsupported file extension....'
        
    def to_representation(self, instance):
        response = super().to_representation(instance)
        data =  CustomUserPortfolio.objects.filter(user_id=instance.id).values()
        response['portfolio'] = data
        return response


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields =  ['id', 'email', "password","username","first_name","last_name","profile_status"]

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = '__all__'

class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = '__all__'

    
class SkillsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skills
        fields = '__all__'

class JobSerializer(serializers.ModelSerializer):
    image = serializers.FileField(write_only=True,allow_empty_file=True,required=False, validators=[validate_file_extension])
    sample_image = serializers.FileField(write_only=True,allow_empty_file=True,required=False, validators=[validate_file_extension])

    class Meta:
        model = Job
        fields = '__all__'
        extra_kwargs = {
            'expected_delivery_date': {'required': True},
        }

    def create(self, validated_data):
        if validated_data.get('image'):
            validated_data.pop('image')
        if validated_data.get('sample_image'):
            validated_data.pop('sample_image')
        
        if validated_data.get('skills'):            
            skills_data = validated_data.get('skills')
            validated_data.pop('skills')
        related_jobs_data = None
        if validated_data.get('related_jobs', None):            
            related_jobs_data = validated_data.get('related_jobs')
        validated_data.pop('related_jobs')

        job = Job.objects.create(**validated_data)
        for i in skills_data:
            job.skills.add(i)
        if related_jobs_data:
            for i in related_jobs_data:
                job.related_jobs.add(i)

        job.save()
        return job

class JobAttachmentsSerializer(serializers.ModelSerializer):
     class Meta:
        model = JobAttachments
        fields = '__all__'


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

class RelatedJobsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        # fields = '__all__'
        fields = ['id','title','description']


class JobsWithAttachmentsSerializer(serializers.ModelSerializer):
    images = JobAttachmentsSerializer(many=True)
    category = CategorySerializer()
    industry = IndustrySerializer()
    level = LevelSerializer()
    skills = SkillsSerializer(many=True)
    related_jobs = RelatedJobsSerializer(many=True)
    company = CompanySerializer()
    get_jobType_details = SerializerMethodField("get_jobType_info")
    job_applied_status = SerializerMethodField("get_job_applied_status")
    
    class Meta:
        model = Job
        fields = '__all__'
        extra_kwargs = {
            'expected_delivery_date': {'required': True},
        }
    
    def get_job_applied_status(self, obj):
        request = self.context.get('request')        
        jobAppliedObj = JobApplied.objects.filter(job=obj.id,user=request.user)   
        if jobAppliedObj:
            return "True"
        else:
            return "False"
   
    def get_jobType_info(self, obj):
        if obj.job_type == '0':
            return 'Fixed'
        elif obj.job_type == '1':
            return 'Hourly'

    def get_category_info(self, obj):
        try:
            if obj.category_id is not None:
                categoryObj = Category.objects.get(id=obj.category.id)
                if categoryObj is not None:
                    category_serializer = CategorySerializer(categoryObj, many=False)
                    return category_serializer.data
                else:
                    return ''
            else:
                return ''
        except Exception as err:
            return ''
    def get_industry_info(self, obj):
        try:
            if obj.industry_id is not None:
                industryObj = Industry.objects.get(id=obj.industry.id)
                if industryObj is not None:
                    industry_serializer = IndustrySerializer(industryObj, many=False)
                    return industry_serializer.data
                else:
                    return ''
            else:
                return ''
        except Exception as err:
            return ''

    def get_level_info(self, obj):
        try:
            if obj.level_id is not None:
                levelObj = Level.objects.get(id=obj.industry.id)
                if levelObj is not None:
                    level_serializer = LevelSerializer(levelObj, many=False)
                    return level_serializer.data
                else:
                    return ''
            else:
                return ''
        except Exception as err:
            return ''

    
    def get_skill_info(self, obj):       
        try:
            if obj.skills_id is not None:
                skillObj = Skills.objects.get(id=obj.skills.id)

                if skillObj is not None:
                    skill_serializer = SkillsSerializer(skillObj, many=False)
                    return skill_serializer.data
                else:
                    return ''
            else:
                return ''
        except Exception as err:
            return ''


class ActivityAttachmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Activities
        fields = '__all__'

class ActivitiesSerializer(serializers.ModelSerializer):
    attachments = serializers.FileField(allow_empty_file=True,required=False)
    class Meta:
        model = Activities
        fields = '__all__'

    def create(self, validated_data):
        if validated_data.get('attachments'):
            validated_data.pop('attachments')
        activities = Activities.objects.create(**validated_data)
        activities.save()
        return activities
   
    def to_representation(self, instance):
        response = super().to_representation(instance)
        activities_attachments = []
        for i in ActivityAttachments.objects.filter(activities=instance):
            activities_attachments.append(i.activity_attachments.url)
        if activities_attachments:
            response['activity_attachments'] = activities_attachments
        return response

class JobAppliedSerializer(serializers.ModelSerializer):
    attachments = serializers.FileField(allow_empty_file=True,required=False)
    class Meta:
        model = JobApplied
        fields = '__all__'

    def create(self, validated_data):
        if validated_data.get('attachments'):
            validated_data.pop('attachments')
        job_applied = JobApplied.objects.create(**validated_data)
        job_applied.save()
        return job_applied
    
    def to_representation(self, instance):
        response = super().to_representation(instance)
        job_attachments = []
        for i in JobAppliedAttachments.objects.filter(job_applied=instance):
            job_attachments.append(i.job_applied_attachments.url)
        if job_attachments:
            response['job_applied_attachments'] = job_attachments
        return response

                
class JobAppliedAttachmentsSerializer(serializers.ModelSerializer):
     class Meta:
        model = JobAppliedAttachments
        fields = '__all__'


class JobFilterSerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=10,decimal_places=2, required=False)
    skills = serializers.CharField(max_length=200, required=False)
    tags = serializers.CharField(max_length=100, required=False)


class JobHiredSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobHired
        fields = '__all__'




