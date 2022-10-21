# Django Rest Framework
import json
from rest_framework import serializers
from authentication.models import CustomUser
from administrator.models import Category, Job, JobAttachments, JobApplied, Industry, Level, Skills, Company
from rest_framework.fields import SerializerMethodField
from administrator.validators import validate_file_extension
from administrator.serializers import SkillsSerializer


class JobAttachmentsSerializer(serializers.ModelSerializer):
     class Meta:
        model = JobAttachments
        fields = '__all__'


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id','category_name', 'slug', 'description', 'is_active', 'created_at', 'updated_at')


class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = ('id','industry_name', 'slug', 'description','is_active', 'created_at', 'updated_at')


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ('id','level_name', 'slug', 'description','is_active', 'created_at', 'updated_at')


class SkillsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skills
        fields = ('id','skill_name', 'slug', 'is_active', 'created', 'modified')

#
# class JobSerializer(serializers.ModelSerializer):
#     image = serializers.FileField(write_only=True,allow_empty_file=True,required=False, validators=[validate_file_extension])
#
#     class Meta:
#         model = Job
#         fields = '__all__'
#         extra_kwargs = {
#             'expected_delivery_date': {'required': True},
#         }


class JobsWithAttachmentsSerializer(serializers.ModelSerializer):
    images = JobAttachmentsSerializer(many=True)
    category = CategorySerializer()
    level = LevelSerializer()
    skills = SkillsSerializer(many=True)

    get_jobType_details = SerializerMethodField("get_jobType_info")
    
    class Meta:
        model = Job
        fields = ['title','description','images','job_type','category','level','skills','price','tags','status','expected_delivery_date','user']
        extra_kwargs = {
            'expected_delivery_date': {'required': True},
        }
   
    def get_jobType_info(self, obj):
        if obj.job_type == '0':
            return 'Fixed'
        elif obj.job_type == '1':
            return 'Hourly'


 
    
class PublicJobViewSerializer(serializers.ModelSerializer):
    skills = SkillsSerializer(many=True)
    class Meta:
        model = Job
        fields = ['id','title','created','description','skills','tags']