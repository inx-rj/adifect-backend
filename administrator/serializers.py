import json
import os
from pyexpat import model
from statistics import mode
from rest_framework import serializers
from authentication.models import CustomUser, CustomUserPortfolio
from .models import Category, Job, JobAttachments, JobApplied, Level, Skills, JobHired, Activities, \
    Activities, JobAppliedAttachments, ActivityAttachments, PreferredLanguage, JobTasks, JobTemplate, \
    JobTemplateAttachments, Question, Answer,UserSkills
from rest_framework.fields import SerializerMethodField
# from agency.serializers import CompanySerializer
from authentication.serializers import UserSerializer
from .validators import validate_file_extension
from langcodes import Language


class userPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUserPortfolio
        fields = '__all__'


class EditProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'profile_title', 'profile_description', 'role', 'video',
                  'profile_img', 'profile_status', 'profile_status', 'preferred_communication_mode',
                  'preferred_communication_id','availability']

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
        data = CustomUserPortfolio.objects.filter(user_id=instance.id).values()
        response['portfolio'] = data
        return response


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', "username", "first_name", "last_name","role" ,"date_joined","is_blocked","profile_img", "profile_status"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


# class IndustrySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Industry
#         fields = '__all__'


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = '__all__'


class SkillsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skills
        fields = '__all__'


class JobSerializer(serializers.ModelSerializer):
    image = serializers.FileField(write_only=True, allow_empty_file=True, required=False,
                                  validators=[validate_file_extension])
    sample_image = serializers.FileField(write_only=True, allow_empty_file=True, required=False,
                                         validators=[validate_file_extension])
    workflow_name = SerializerMethodField("get_worksflow_name")

    class Meta:
        model = Job
        fields = '__all__'
        extra_kwargs = {
            'expected_delivery_date': {'required': True},
            'skills': {'required': False},
        }

    def get_worksflow_name(self, obj):
        try:
            if obj.workflow:
                return obj.workflow.name
            return ''
        except:
            return ''

    def create(self, validated_data):
        if validated_data.get('image'):
            validated_data.pop('image')
        if validated_data.get('sample_image'):
            validated_data.pop('sample_image')

        if validated_data.get('skills'):
            skills_data = validated_data.get('skills')
            validated_data.pop('skills')
        else:
            validated_data.pop('skills')
            skills_data = None

        job = Job.objects.create(**validated_data)
        if skills_data:
            for i in skills_data:
                job.skills.add(i)


        job.save()
        return job


class JobAttachmentsSerializer(serializers.ModelSerializer):
    job_image_name = SerializerMethodField("get_image_name")
    work_sample_image_name = SerializerMethodField("get_work_sample_image_name")
    class Meta:
        model = JobAttachments
        fields = '__all__'

    def get_image_name(self, obj):
        if obj.job_images:
            return str(obj.job_images).split('/')[-1]
        return None

    def get_work_sample_image_name(self, obj):
        if obj.work_sample_images:
            return str(obj.work_sample_images).split('/')[-1]
        return None




# class CompanySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Company
#         fields = '__all__'


class RelatedJobsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        # fields = '__all__'
        fields = ['id', 'title', 'description']


class JobTasksSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobTasks
        fields = '__all__'


class JobsWithAttachmentsSerializer(serializers.ModelSerializer):
    images = JobAttachmentsSerializer(many=True)
    # category = CategorySerializer()
    # industry = IndustrySerializer()
    jobtasks_job = JobTasksSerializer(many=True)
    level = LevelSerializer()
    skills = SkillsSerializer(many=True)
    # related_jobs = RelatedJobsSerializer(many=True)
    # company = CompanySerializer()
    get_jobType_details = SerializerMethodField("get_jobType_info")
    job_applied_status = SerializerMethodField("get_job_applied_status")
    workflow_name = SerializerMethodField("get_worksflow_name")
    company_name = SerializerMethodField("get_company_name")
    industry_name = SerializerMethodField("get_industry_name")
    username = SerializerMethodField("get_username")
    job_applied_id = SerializerMethodField("get_job_applied_id")

    class Meta:
        model = Job
        fields = '__all__'
        extra_kwargs = {
            'expected_delivery_date': {'required': True},
        }

    def get_job_applied_status(self, obj):
        request = self.context.get('request')
        jobAppliedObj = JobApplied.objects.filter(job=obj.id, user=request.user)
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

    def get_company_name(self,obj):
        try:
            if obj.company:
                return obj.company.name
            else:
                return ''
        except Exception as err:
            return ''

    def get_industry_name(self,obj):
        try:
            if obj.industry:
                return obj.industry.industry_name
            else:
                return ''
        except Exception as err:
            return ''
    
    def get_username(self,obj):
        try:
            if obj.user:
                return obj.user.username
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

    def get_worksflow_name(self, obj):
        try:
            if obj.workflow:
                return obj.workflow.name
            return ''
        except:
            return ''
    
    def get_job_applied_id(self, obj):
        request = self.context.get('request')
        jobAppliedObj = JobApplied.objects.filter(job=obj.id, user=request.user).first()
        if jobAppliedObj:
           return jobAppliedObj.id
        else:
            return "False"


class ActivityAttachmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Activities
        fields = '__all__'


class ActivitiesSerializer(serializers.ModelSerializer):
    attachments = serializers.FileField(allow_empty_file=True, required=False)

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

class JobAppliedAttachmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobAppliedAttachments
        fields = '__all__'

class JobAppliedSerializer(serializers.ModelSerializer):
    full_name = SerializerMethodField("get_fullname")
    profile_img = serializers.SerializerMethodField("get_profile_img")

    class Meta:
        model = JobApplied
        fields = '__all__'
    def get_fullname(self, obj):
        try:
            if obj.user:
                return obj.user.get_full_name()
            else:
                return ''
        except Exception as err:
            return ''

    def get_profile_img(self, obj):
        try:
            if obj.user:
                profile = obj.user.profile_img.url
                return profile
            else:
                return ''
        except Exception as err:
            return ''        

    def create(self, validated_data):
        job_applied = JobApplied.objects.create(**validated_data)
        job_applied.save()
        return job_applied

    def to_representation(self, instance):
        response = super().to_representation(instance)
        job_attachments = []
        job_attachments_name = []
        for i in JobAppliedAttachments.objects.filter(job_applied=instance):
            job_attachments.append(i.job_applied_attachments.url)
            job_attachments_name.append(str(i.job_applied_attachments.name).split('/')[-1])

        if job_attachments:
            response['job_applied_attachments'] = job_attachments
            response['job_applied_attachments_name'] = job_attachments_name
        return response




class JobFilterSerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    skills = serializers.CharField(max_length=200, required=False)
    tags = serializers.CharField(max_length=100, required=False)


class JobHiredSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobHired
        fields = '__all__'


class PreferredLanguageSerializer(serializers.ModelSerializer):
    language = SerializerMethodField("get_language")
    proficiency = SerializerMethodField("get_proficiency")

    class Meta:
        model = PreferredLanguage
        fields = '__all__'

    def get_language(self, obj):
        if obj.ln_code:
            return Language.get(obj.ln_code).display_name()
        else:
            return ""

    def get_proficiency(self, obj):
        if obj:
            return obj.get_ln_proficiency_display()
        else:
            return ''




class JobTemplateSerializer(serializers.ModelSerializer):
    image = serializers.FileField(write_only=True, allow_empty_file=True, required=False,
                                  validators=[validate_file_extension])
    sample_image = serializers.FileField(write_only=True, allow_empty_file=True, required=False,
                                         validators=[validate_file_extension])
    workflow_name = SerializerMethodField("get_worksflow_name")

    class Meta:
        model = JobTemplate
        fields = '__all__'
        extra_kwargs = {
            'expected_delivery_date': {'required': True},
        }
    def get_job_type(self,obj):
        if obj.job_type:
            return str(obj.job_type)
        return ''

    def get_worksflow_name(self, obj):
        if obj.workflow:
            return obj.workflow.name
        return ''

    def create(self, validated_data):
        if validated_data.get('image'):
            validated_data.pop('image')
        if validated_data.get('sample_image'):
            validated_data.pop('sample_image')

        if validated_data.get('skills'):
            skills_data = validated_data.get('skills')
            validated_data.pop('skills')
        job = JobTemplate.objects.create(**validated_data)
        if skills_data:
            for i in skills_data:
                job.skills.add(i)
            job.save()
        return job


class JobTemplateAttachmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobTemplateAttachments
        fields = '__all__'


class JobTemplateWithAttachmentsSerializer(serializers.ModelSerializer):
    job_template_images = JobTemplateAttachmentsSerializer(many=True)
    level = LevelSerializer()
    skills = SkillsSerializer(many=True)
    # company = CompanySerializer()
    get_jobType_details = SerializerMethodField("get_jobType_info")
    workflow_name = SerializerMethodField("get_worksflow_name")
    status = SerializerMethodField("get_status")
    company_name = SerializerMethodField("get_company_name")
    job_type = SerializerMethodField("get_job_type")
    industry_name = SerializerMethodField("get_industry_name")

    class Meta:
        model = JobTemplate
        fields = '__all__'
        extra_kwargs = {
            'expected_delivery_date': {'required': True},
        }


    def get_job_type(self, obj):
        if obj.job_type:
            return str(obj.job_type)
        else:
            return ''

    def get_jobType_info(self, obj):
        if obj:
            return obj.get_job_type_display()
        else:
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

    def get_worksflow_name(self, obj):
        if obj.workflow:
            return obj.workflow.name
        return ''

    def get_status(self,obj):
        return obj.get_status_display()

    def get_company_name(self,obj):
        try:
            if obj.company:
                return obj.company.name
            else:
                return ''
        except Exception as err:
            return ''

    def get_industry_name(self,obj):
        try:
            if obj.industry:
                return obj.industry.industry_name
            else:
                return ''
        except Exception as err:
            return ''

class AnswerSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField("getUsername")

    class Meta:
        model = Answer
        fields = '__all__'


    def getUsername(self, obj):
        if obj.agency is not None:
            return obj.agency.username
        if  obj.job_applied is not None:
            return obj.job_applied.user.username
        return ''

class QuestionSerializer(serializers.ModelSerializer):
    answer_question = AnswerSerializer(many=True,required=False)
    def getUsername(self, obj):
        return obj.user.username

    username = serializers.SerializerMethodField("getUsername")
    class Meta:
        model = Question
        fields = '__all__'



class UserSkillsSerializer(serializers.ModelSerializer):
    # skills = SkillsSerializer(required=False)
    skill_name = serializers.SerializerMethodField("get_skill_name")
    class Meta:
        model = UserSkills
        fields = '__all__'

    def get_skill_name(self,obj):
        if obj.skills is not None:
            return obj.skills.skill_name
        return ''






class SearchFilterSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=200, required=False)

