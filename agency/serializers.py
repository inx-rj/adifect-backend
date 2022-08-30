import json
import os
from pyexpat import model
from statistics import mode
from rest_framework import serializers
from .models import Stages, WorkFlowLevels, WorkFlow, InviteMember
from rest_framework.fields import SerializerMethodField

from authentication.serializers import UserSerializer
from authentication.models import CustomUser
from administrator.models import Job
from administrator.serializers import JobSerializer,UserListSerializer



class StagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stages
        fields = '__all__'


class WorkFlowLevelsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkFlowLevels
        fields = '__all__'

class WorkFlowSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = WorkFlow
        fields = '__all__'
    
    def get_agency_info(self, obj):
        try:
            if obj.user_id is not None:
                userObj = CustomUser.objects.get(id=obj.agency.id)
                if userObj is not None:
                    user_serializer = UserListSerializer(userObj, many=False)
                    return user_serializer.data
                else:
                    return ''
            else:
                return ''
        except Exception as err:
            return ''


    def get_user_info(self, obj):
        try:
            if obj.user_id is not None:
                userObj = CustomUser.objects.get(id=obj.user.id)
                if userObj is not None:
                    user_serializer = UserListSerializer(userObj, many=False)
                    return user_serializer.data
                else:
                    return ''
            else:
                return ''
        except Exception as err:
            return ''

    def get_stage_info(self, obj):
        try:
            if obj.user_id is not None:
                stageObj = Stages.objects.get(id=obj.stage.id)
                if stageObj is not None:
                    stage_serializer = StagesSerializer(stageObj, many=False)
                    return stage_serializer.data
                else:
                    return ''
            else:
                return ''
        except Exception as err:
            return ''

    def get_level_info(self, obj):
        try:
            if obj.level_id is not None:
                levelObj = WorkFlowLevels.objects.get(id=obj.level.id)
                if levelObj is not None:
                    level_serializer = WorkFlowLevelsSerializer(levelObj, many=False)
                    return level_serializer.data
                else:
                    return ''
            else:
                return ''
        except Exception as err:
            return ''

        
class InviteMemberSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    user_id = SerializerMethodField("get_user_info")
    message = serializers.CharField(write_only=True, required=True)
    level = serializers.CharField(write_only=True, required=True)
    exclusive = serializers.BooleanField(write_only=True,default=False)

    class Meta:
        model = InviteMember
        fields = ['agency','email','user_id','message','level','exclusive']

    def get_user_info(self, obj):
        try:
            if obj.user:
                user_serializer = UserListSerializer(obj.user, many=False)
                return user_serializer.data
            else:
                return ''
        except Exception as err:
            return ''




class InviteMemberRegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    username = serializers.CharField(max_length=20, required=True, allow_blank=False)
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    invite_user = serializers.ChoiceField(choices=((0, 'False'),(1,'True')),default=0)

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'password', 'confirm_password',
                  'email','role', 'invite_user')
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