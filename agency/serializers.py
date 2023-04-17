import json
import os
from pyexpat import model
from statistics import mode

from django.db import transaction
from rest_framework import serializers

from community.models import Channel
from .models import InviteMember, WorksFlow, Workflow_Stages, Industry, Company, DAM, DamMedia, TestModal, AgencyLevel, \
    Audience, AudienceChannel
from rest_framework.fields import SerializerMethodField

from authentication.serializers import UserSerializer
from authentication.models import CustomUser
from administrator.models import Job,JobApplied
from administrator.serializers import JobSerializer, UserListSerializer,SkillsSerializer,JobsWithAttachmentsSerializer
from django.core.exceptions import ValidationError


class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = '__all__'

    def validate_industry_name(self, value):
        exist_industry = None
        if self.instance:
            exist_industry = Industry.objects.exclude(id=self.instance.id).filter(industry_name=value, is_trashed=False)
        else:
            exist_industry = Industry.objects.filter(industry_name=value, is_trashed=False)
        if exist_industry:
            raise ValidationError("Industry Already Exist")
        return value


class CompanySerializer(serializers.ModelSerializer):
    is_assigned_workflow = SerializerMethodField("get_assigned_workflow")
    agency_name = SerializerMethodField("get_agency_name")
    industry_name = SerializerMethodField("get_industry_name")
    company_id = SerializerMethodField("get_company_id")

    class Meta:
        model = Company
        fields = '__all__'
        extra_kwargs = {'agency': {'required': True}}

    def validate(self, data):
        exist_company = None
        if 'name' in data and data['name']:
            if self.instance:
                exist_company = Company.objects.exclude(id=self.instance.id).filter(name__iexact=data['name'],
                                                                                    agency=self.instance.agency,
                                                                                    is_trashed=False)
            else:
                exist_company = Company.objects.filter(name__iexact=data['name'], agency=data['agency'], is_trashed=False)
            if exist_company:
                raise ValidationError("Company Already Exist")
        return data

    def get_assigned_workflow(self, obj):
        try:
            if obj:
                # reverse relation
                if obj.workflow_company.all():
                    return True
                else:
                    return False
            else:
                return ''
        except Exception as err:
            return ''

    def get_agency_name(self, obj):
            if obj.agency is not None:
                    return obj.agency.username
            return ''

    def get_industry_name(self, obj):
        if obj.industry:
            return obj.industry.industry_name
        return ''
    
    def get_company_id(self, obj):
        if obj is not None:
            return obj.id
        return ""


class WorksFlowSerializer(serializers.ModelSerializer):
    assigned_job = SerializerMethodField("get_assigned_job")
    company_name = SerializerMethodField("get_company_name")

    class Meta:
        model = WorksFlow
        fields = '__all__'
        extra_kwargs = {'company': {'required': True}}

    def validate(self, data):
        exist_WorksFlow = None
        if self.instance:
            exist_WorksFlow = WorksFlow.objects.exclude(id=self.instance.id).filter(name__iexact=data['name'],
                                                                                    agency=self.instance.agency,
                                                                                    is_trashed=False)
        else:
            exist_WorksFlow = WorksFlow.objects.filter(name__iexact=data['name'], agency=data['agency'],
                                                       is_trashed=False)
        if exist_WorksFlow:
            raise ValidationError("Works Flow With This Name Already Exist")
        return data

    def get_assigned_job(self, obj):
        try:
            if obj:
                # reverse relation
                if obj.job_workflow.all():
                    return True
                else:
                    return False
            else:
                return ''
        except Exception as err:
            return ''

    def get_company_name(self, obj):
        try:
            if obj.company:
                return obj.company.name
            else:
                return ''
        except Exception as err:
            return ''



class InviteMemberSerializer(serializers.ModelSerializer):
    # email = serializers.EmailField(write_only=True)
    user_id = SerializerMethodField("get_user_id")
    user_name = SerializerMethodField("get_user_name")
    user_email = SerializerMethodField("get_user_email")
    user_image = SerializerMethodField("get_user_image")
    user_first_name = SerializerMethodField("get_first_name")
    user_last_name = SerializerMethodField("get_last_name")
    levels = serializers.IntegerField(write_only=True, required=True)
    level = SerializerMethodField("get_level")
    exclusive = serializers.BooleanField(write_only=True, default=False)
    company_name = SerializerMethodField('get_company_name')
    user_full_name = SerializerMethodField("get_user_full_name")

    class Meta:
        model = InviteMember
        fields = '__all__'

    def get_user_id(self, obj):
        try:
            if obj.user:
                return obj.user.user.id
            else:
                return ''
        except Exception as err:
            return ''

    def get_user_name(self, obj):
        try:
            if obj.user:
                return obj.user.user.username
            else:
                return ''
        except Exception as err:
            return ''

    def get_user_email(self, obj):
        try:
            if obj.user:
                return obj.user.user.email
            else:
                return ''
        except Exception as err:
            return ''

    def get_user_image(self, obj):
        try:
            if obj.user:
                return self.get_image_url(obj.user.user.profile_img.url)
            else:
                return ''
        except Exception as err:
            return ''

    def get_first_name(self, obj):
        try:
            if obj.user:
                return obj.user.user.first_name
            else:
                return ''
        except Exception as err:
            return ''

    def get_last_name(self, obj):
        try:
            if obj.user:
                return obj.user.user.last_name
            else:
                return ''
        except Exception as err:
            return ''

    def get_level(self, obj):
        try:
            if obj.user:
                return obj.user.levels
            else:
                return ''
        except Exception as err:
            return ''

    def get_image_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj)

    def get_company_name(self, obj):
        try:
            if obj.company:
                return obj.company.name
            else:
                return ''
        except Exception as err:
            return ''

    def get_user_full_name(self, obj):
        try:
            if obj.user:
                return obj.user.user.get_full_name()
            else:
                return ''
        except Exception as err:
            return ''


class InviteMemberRegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    username = serializers.CharField(max_length=20, required=True, allow_blank=False)
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    invite_user = serializers.ChoiceField(choices=((0, 'False'), (1, 'True')), default=0)

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'password', 'confirm_password',
                  'email', 'role', 'invite_user')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    ###  override the error message ####
    def __init__(self, *args, **kwargs):
        super(InviteMemberRegisterSerializer, self).__init__(*args, **kwargs)
        self.fields['username'].error_messages['blank'] = 'UserName Required'
        # self.fields['username'].error_messages['unique']= 'UserName Required'
        self.fields['password'].error_messages['blank'] = 'Password Required'
        self.fields['confirm_password'].error_messages['blank'] = 'Confirm Password Required'
        self.fields['email'].error_messages['blank'] = 'Email Required'
        self.fields['email'].error_messages['unique'] = 'Email Already Exist'

    # Object Level Validation
    def validate(self, data):
        user_name = data.get('username')
        email = data.get('email')
        if CustomUser.objects.filter(username__iexact=user_name).exists() and CustomUser.objects.filter(
                email__iexact=email).exists():
            raise serializers.ValidationError("User Name and email must be unique")
        if CustomUser.objects.filter(username__iexact=user_name).exists():
            raise serializers.ValidationError("User Name already taken")
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Email already exist")
        return data


class StageSerializer(serializers.ModelSerializer):
    observer_detail = SerializerMethodField("get_observer_detail")
    approvals_details = SerializerMethodField("get_approvals_details")

    class Meta:
        model = Workflow_Stages
        fields = '__all__'

    def get_observer_detail(self, obj):
        if obj.observer:
            user_serializer = InviteMemberSerializer(obj.observer.all(), many=True)
            return user_serializer.data
        return ''

    def get_approvals_details(self, obj):
        if obj.approvals:
            user_serializer = InviteMemberSerializer(obj.approvals.all(), many=True)
            return user_serializer.data
        return ''


class DAMSerializer(serializers.ModelSerializer):
    dam_files = serializers.FileField(allow_empty_file=True, required=False)
    

    class Meta:
        model = DAM
        fields = '__all__'

    def create(self, validated_data):
        if validated_data.get('dam_files'):
            validated_data.pop('dam_files')

        dam = DAM.objects.create(**validated_data)
        dam.save()
        return dam


class DamMediaSerializer(serializers.ModelSerializer):
    skill =SerializerMethodField("get_skill")
    files_name = SerializerMethodField("get_files_name")
    files_size = SerializerMethodField("get_files_size")
    upload_by = SerializerMethodField("get_user_name")
    is_favourite =  SerializerMethodField("get_is_favourite")
    company = SerializerMethodField("get_company")
    get_file_extension = SerializerMethodField("get_files_extension")
    type = SerializerMethodField("get_type")
    root = SerializerMethodField("get_is_root")

    
    # description =  SerializerMethodField("get_description")
    class Meta:
        model = DamMedia
        fields = '__all__'


    def get_skill(self,obj):
        if obj.skills:
            skill = SkillsSerializer(obj.skills.all(),many=True)
            return skill.data
        return ''

    def get_is_root(self, obj):
        if obj.dam.parent:
            return obj.dam.parent_id
        else:
            return "Null"



    def get_type(self,obj):
        if obj.dam is not None:
            if obj.dam.type is not None:
                return obj.dam.type
        return ''

    def get_files_name(self, obj):
        if obj:
            if obj.media is not  None:
                return str(obj.media.name).split('/')[-1]
            else:
                return ''
        return ''
    
    def get_files_extension(self, obj):
        if obj:
            if obj.media is not None:
                return str(obj.media.name).split('.')[-1]
            else:
                return ''
        return ''

    def get_files_size(self, obj):
        if obj:
            if obj.media is not  None:
                return str(obj.media.size)
            else:
                return ''
        return

    def get_user_name(self, obj):
        if obj.dam is not None:
            if obj.dam.agency is not None:
                return obj.dam.agency.get_full_name()
        return ''

    def get_is_favourite(self,obj):
        if obj.dam is not None:
                return obj.dam.is_favourite
        return False

    def get_company(self,obj):
        if obj.dam.company is not None:
                return obj.dam.company.id
        return ""
    # def get_description(self,obj):
    #     if obj.description is not None:
    #         return obj.description
    #     else:
    #         return ""

class DamMediaThumbnailSerializer(serializers.ModelSerializer):
    files_name = SerializerMethodField("get_files_name")
    files_size = SerializerMethodField("get_files_size")
    upload_by = SerializerMethodField("get_user_name")
    is_favourite =  SerializerMethodField("get_is_favourite")
    file_type = SerializerMethodField("get_file_type")
    class Meta:
        model = DamMedia
        exclude = ('media',)
        # fields = ['id','dam','thumbnail','title','description','files_name','files_size','upload_by','is_favourite']

    def get_files_name(self, obj):
        if obj:
            if obj.media is not  None:
                return str(obj.media.name).split('/')[-1]
            else:
                return ''
        return ''

    def get_files_size(self, obj):
        if obj:
            if obj.media is not  None:
                return str(obj.media.size)
            else:
                return ''
        return

    def get_user_name(self, obj):
        if obj.dam is not None:
            if obj.dam.agency is not None:
                return obj.dam.agency.get_full_name()
        return ''

    def get_is_favourite(self,obj):
        if obj.dam is not None:
                return obj.dam.is_favourite
        return False
    
    def get_file_type(self, obj):
        if obj:
             return obj.dam.type
            
        return True


#-------------------------------------------- dam ---------------------------------------------#
# location_storage = ''


# def recursor(obj, count):
#     global location_storage
#     if count == 0:
#         location_storage = ''
#     if obj.type == 1 or obj.type == 2:
#         if obj.parent is None:
#             location_storage += f'/{obj.name}'
#             return location_storage
#         else:
#             location_storage += '/' + str(obj.name)
#             recursor(obj.parent, 1)
#     if obj.type == 3:
#         if obj.parent is None:
#             location_storage += ''
#             return location_storage
#         else:
#             location_storage += ''
#             recursor(obj.parent, 1)
#     return location_storage


# def re_order(sentence):
#     words = sentence.split('/')
#     # then reverse the split string list and join using space
#     reverse_sentence = '/'.join(reversed(words))
#     return reverse_sentence


class DamWithMediaRootSerializer(serializers.ModelSerializer):
    dam_media = DamMediaSerializer(many=True, required=False)
    # location = SerializerMethodField("get_location")
    is_parent = SerializerMethodField("get_is_parent")
    parent =  SerializerMethodField("get_parent")
    upload_by = SerializerMethodField("get_user_name")
    company = SerializerMethodField("get_company_name")
    total_obj = SerializerMethodField("get_total_object")
    company_id = SerializerMethodField("get_company_id")
    root = SerializerMethodField("get_root")
    
    class Meta:
        model = DAM
        fields = '__all__'

    def get_user_name(self,obj):
        if obj.agency is not None:
            return obj.agency.get_full_name()
        return ''


    def get_parent(self,obj):
        if obj.parent is not None:
            return obj.parent_id
        else:
            return obj.id
    def get_root(self,obj):
        if obj.parent is not None:
            return obj.parent_id
        else:
            return "Null"  
   
    #
    # def get_location(self, obj):
    #     if obj:
    #         return re_order(recursor(obj, 0))
    #     return ''

    def get_is_parent(self, obj):
        if obj.parent is not None:
            if obj.parent.parent is None:
                return False
            else:
                return obj.parent.parent.id
        else:
            return False
    def get_company_name(self,obj):
        if obj.company is not None:
            return obj.company.name
        return ''
    
    def get_total_object(self, obj):
        if obj:
            return DAM.objects.filter(parent=obj).count()
        return ''
    def get_company_id(self, obj):
        if obj.company is not None:
            return obj.company.id
        return ""

class DamWithMediaSerializer(serializers.ModelSerializer):
    dam_media = DamMediaSerializer(many=True, required=False)
    # location = SerializerMethodField("get_location")
    is_parent = SerializerMethodField("get_is_parent")
    parent =  SerializerMethodField("get_parent")
    upload_by = SerializerMethodField("get_user_name")
    company = SerializerMethodField("get_company_name")
    total_obj = SerializerMethodField("get_total_object")
    root = SerializerMethodField("get_root")
    company_id = SerializerMethodField("get_company_id")
    
    class Meta:
        model = DAM
        fields = '__all__'

    def get_parent(self,obj):
        if obj.parent is not None:
            return obj.parent_id
        else:
            return False
    # def get_location(self, obj):
    #     if obj:
    #         return re_order(recursor(obj, 0))
    #     return ''

    def get_is_parent(self, obj):
        if obj.parent is not None:
            if obj.parent.parent is None:
                return False
            else:
                return obj.parent.parent.id
        else:
            return False
        
    def get_root(self,obj):
        if obj.parent is not None:
             return obj.parent.id
        else:
            return "Null"

    def get_user_name(self,obj):
        if obj.agency is not None:
            return obj.agency.get_full_name()
        return ''
    def get_company_name(self,obj):
        if obj.company is not None:
            return obj.company.name
        return ''
    
    def get_company_id(self,obj):
        if obj.company is not None:
            return obj.company.id
        return ''

    # def get_parent(self,obj):
    #     if obj.name is not None:
    #         return obj.name
    #     else:
    #         return False
    def get_total_object(self, obj):
        if obj:
            return DAM.objects.filter(parent=obj).count()
        return ''

class DamWithMediaThumbnailSerializer(serializers.ModelSerializer):
    dam_media = DamMediaThumbnailSerializer(many=True, required=False)
    # location = SerializerMethodField("get_location")
    is_parent = SerializerMethodField("get_is_parent")
    parent =  SerializerMethodField("get_parent")
    upload_by = SerializerMethodField("get_user_name")

    class Meta:
        model = DAM
        fields = '__all__'

    def get_parent(self,obj):
        if obj.parent is not None:
            return obj.parent_id
        else:
            return False
    # def get_location(self, obj):
    #     if obj:
    #         return re_order(recursor(obj, 0))
    #     return ''

    def get_is_parent(self, obj):
        if obj.parent is not None:
            if obj.parent.parent is None:
                return False
            else:
                return obj.parent.parent.id
        else:
            return False

    def get_user_name(self,obj):
        if obj.agency is not None:
            return obj.agency.get_full_name()
        return ''


#--------------------------------------------------- End --------------------------------------------------#

class MyProjectSerializer(serializers.ModelSerializer):
    job = JobsWithAttachmentsSerializer(required=False)
    applied_count = SerializerMethodField("get_applied_count")
    class Meta:
        model = JobApplied
        fields = '__all__'

    def get_applied_count(self,obj):
        if obj.status is not None:
            return JobApplied.objects.filter(job=obj.job,status=obj.status).count()
        return None






class TestModalSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestModal
        fields = '__all__'

class AgencyLevelSerializer(serializers.ModelSerializer):

    class Meta:
        model = AgencyLevel
        fields = '__all__'

class DamMediaNewSerializer(serializers.ModelSerializer):
    class Meta:
        model = DamMedia
        fields = '__all__'


class AudienceChannelSerializer(serializers.ModelSerializer):

    class Meta:
        model = AudienceChannel
        fields = ['channel', 'url']


class AudienceListCreateSerializer(serializers.ModelSerializer):
    """
    Serializer to view list of all Audiences and add Audience
    """
    channel = AudienceChannelSerializer(many=True, write_only=True)

    class Meta:
        model = Audience
        fields = ['audience_id', 'title', 'channel']

    def create(self, validated_data):
        channel_data = validated_data.pop('channel')
        with transaction.atomic():
            audience = Audience.objects.create(**validated_data)
            for channel in channel_data:
                if not channel.get('channel'):
                    raise serializers.ValidationError("Channel id not provided!")
                channel_obj = Channel.objects.get(id=channel.get('channel').id)
                AudienceChannel.objects.create(audience=audience, channel=channel_obj, url=channel.get('url'))
        return audience

    def to_representation(self, instance):
        representation = super(AudienceListCreateSerializer, self).to_representation(instance)
        representation['channel'] = AudienceChannelSerializer(instance.audience_channel_audience.all(), many=True).data
        return representation


class AudienceRetrieveUpdateDestroySerializer(serializers.ModelSerializer):
    """
    Serializer to update audience
    """
    channel = AudienceChannelSerializer(many=True, write_only=True)

    class Meta:
        model = Audience
        fields = ['audience_id', 'title', 'channel']

    def update(self, instance, validated_data):
        channel_data = validated_data.get('channel')
        instance.audience_id = validated_data.get('audience_id', instance.audience_id)
        instance.title = validated_data.get('title', instance.title)
        instance.channel.clear()
        for channel in channel_data:
            if not channel.get('channel'):
                raise serializers.ValidationError("Channel id not provided!")
            channel_obj = Channel.objects.get(id=channel.get('channel').id)
            AudienceChannel.objects.create(audience=instance, channel=channel_obj, url=channel.get('url'))
        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super(AudienceRetrieveUpdateDestroySerializer, self).to_representation(instance)
        representation['channel'] = AudienceChannelSerializer(instance.audience_channel_audience.all(), many=True).data
        return representation
