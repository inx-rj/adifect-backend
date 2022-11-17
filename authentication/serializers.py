from typing_extensions import Required
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
# Django Standard
import os
# Django Local
from rest_framework.response import Response

from .models import CustomUser, PaymentMethod, PaymentDetails,UserProfile,UserCommunicationMode,CustomUserPortfolio
from django.db.models import Q
# Django Rest Framework
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class RegisterSerializer(serializers.ModelSerializer):
    # email = serializers.EmailField(required=True,validators=[UniqueValidator(queryset=CustomUser.objects.all())])
    email = serializers.EmailField(required=True)
    username = serializers.CharField(max_length=20, required=True, allow_blank=False)
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'password', 'confirm_password',
                  'email', 'role')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    ###  override the error message ####
    def __init__(self, *args, **kwargs):
        super(RegisterSerializer, self).__init__(*args, **kwargs)
        self.fields['username'].error_messages['blank'] = 'UserName Required'
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


# Serializer For User Model.
class UserSerializer(serializers.ModelSerializer):
    email = serializers.CharField(required=True)

    class Meta:
        model = CustomUser
        fields = ["email", "password"]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance


class SendForgotEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=200, required=True)
    confirm_password = serializers.CharField(max_length=200, required=True)

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = '__all__'


class PaymentVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentDetails
        fields = '__all__'

class ProfileChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=200, required=True)
    confirm_password = serializers.CharField(max_length=200, required=True)
    current_password = serializers.CharField(max_length=200, required=True)

    def validate(self, data):
        new_password = data.get('new_password')
        current_password = data.get('current_password')
        confirm_password = data.get('confirm_password')
        if len(new_password) < 7 or len(confirm_password) < 7 or len(current_password) < 7:
            raise serializers.ValidationError("'Make sure your password is at least 7 letters'")
        return data



class UserDetailsSerializer(serializers.Serializer):
    class Meta:
        model = CustomUser
        fields = '__all__'

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'

class CustomUserPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUserPortfolio
        fields = '__all__'


class UserCommunicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCommunicationMode
        fields = '__all__'

    def validate(self, data):
        try:
            if data['mode_value'] and data['communication_mode'] == 0:
                validate_email(data['mode_value'])
        except ValidationError:
            raise serializers.ValidationError('Please Enter valid Email.')
        return data