import json
import os
from pyexpat import model
from statistics import mode
from rest_framework import serializers
from .models import InviteMember, WorksFlow, Workflow_Stages
from rest_framework.fields import SerializerMethodField

from authentication.serializers import UserSerializer
from authentication.models import CustomUser
from administrator.models import Job
from administrator.serializers import JobSerializer, UserListSerializer


class WorksFlowSerializer(serializers.ModelSerializer):
    job_title = SerializerMethodField("get_job_name")

    class Meta:
        model = WorksFlow
        fields = '__all__'

    def get_job_name(self, obj):
        if obj.job:
            return obj.job.title
        else:
            return ''


class InviteMemberSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    user_id = SerializerMethodField("get_user_id")
    user_name = SerializerMethodField("get_user_name")
    user_email = SerializerMethodField("get_user_email")
    user_image = SerializerMethodField("get_user_image")
    message = serializers.CharField(write_only=True, required=True)
    level = serializers.CharField(write_only=True, required=True)
    exclusive = serializers.BooleanField(write_only=True, default=False)

    class Meta:
        model = InviteMember
        fields = ['id','agency', 'email', 'user_id', 'message', 'level', 'exclusive', 'user_name', 'user_email',
                  'user_image']

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
        # if CustomUser.objects.filter(username__iexact=user_name, email__iexact=email).exists():
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
