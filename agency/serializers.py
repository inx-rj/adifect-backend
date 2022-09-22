import json
import os
from pyexpat import model
from statistics import mode
from rest_framework import serializers
from .models import InviteMember, WorksFlow, Workflow_Stages, Industry, Company, DAM, DamMedia
from rest_framework.fields import SerializerMethodField

from authentication.serializers import UserSerializer
from authentication.models import CustomUser
from administrator.models import Job
from administrator.serializers import JobSerializer, UserListSerializer
from django.core.exceptions import ValidationError

class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = '__all__'

    def validate_industry_name(self, value):
        exist_industry = None
        if self.instance:
            exist_industry = Industry.objects.exclude(id=self.instance.id).filter(industry_name=value,is_trashed=False)
        else:
            exist_industry = Industry.objects.filter(industry_name=value, is_trashed=False)
        if exist_industry:
            raise ValidationError("Industry Already Exist")
        return value



class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


    def validate(self, data):
        exist_company = None
        if self.instance:
            exist_company = Company.objects.exclude(id=self.instance.id).filter(name__iexact=data['name'], agency=self.instance.agency,
                                                                                is_trashed=False)
        else:
            exist_company = Company.objects.filter(name__iexact=data['name'],agency=data['agency'], is_trashed=False)
        if exist_company:
            raise ValidationError("Company Already Exist")
        return data


class WorksFlowSerializer(serializers.ModelSerializer):
    assigned_job = SerializerMethodField("get_assigned_job")
    company_name = SerializerMethodField("get_company_name")

    class Meta:
        model = WorksFlow
        fields = '__all__'

    def validate_name(self, value):
        exist_WorksFlow = None
        if self.instance:
            exist_WorksFlow = WorksFlow.objects.exclude(id=self.instance.id).filter(name=value, is_trashed=False)
        else:
            exist_WorksFlow = WorksFlow.objects.filter(name=value, is_trashed=False)
        if exist_WorksFlow:
            raise ValidationError("Works Flow With This Name Already Exist")
        return value


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
    email = serializers.EmailField(write_only=True)
    user_id = SerializerMethodField("get_user_id")
    user_name = SerializerMethodField("get_user_name")
    user_email = SerializerMethodField("get_user_email")
    user_image = SerializerMethodField("get_user_image")
    user_first_name = SerializerMethodField("get_first_name")
    user_last_name = SerializerMethodField("get_last_name")

    # message = serializers.CharField(write_only=True, required=True)
    # level = serializers.CharField(write_only=True, required=True)
    exclusive = serializers.BooleanField(write_only=True, default=False)

    class Meta:
        model = InviteMember
        fields = ['id', 'agency', 'email', 'user_id', 'exclusive', 'user_name', 'user_email',
                  'user_image','user_first_name','user_last_name']

    def get_user_id(self, obj):
        try:
            if obj.user:
                return obj.user.id
            else:
                return ''
        except Exception as err:
            return ''

    def get_user_name(self, obj):
        try:
            if obj.user:
                return obj.user.username
            else:
                return ''
        except Exception as err:
            return ''

    def get_user_email(self, obj):
        try:
            if obj.user:
                return obj.user.email
            else:
                return ''
        except Exception as err:
            return ''

    def get_user_image(self, obj):
        try:
            if obj.user:
                return self.get_image_url(obj.user.profile_img.url)
            else:
                return ''
        except Exception as err:
            return ''

    def get_first_name(self, obj):
        try:
            if obj.user:
                return obj.user.first_name
            else:
                return ''
        except Exception as err:
            return ''

    def get_last_name(self, obj):
        try:
            if obj.user:
                return obj.user.last_name
            else:
                return ''
        except Exception as err:
            return ''

    def get_image_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj)


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
    class Meta:
        model = DamMedia
        fields = '__all__'

class DamWithMediaSerializer(serializers.ModelSerializer):
    dam_media = DamMediaSerializer(many=True, required=False)
    class Meta:
        model = DAM
        fields = '__all__'