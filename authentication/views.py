from argparse import Action
from cProfile import label
from http.client import HTTPResponse
from urllib import request
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import render
from .serializers import RegisterSerializer, UserSerializer, SendForgotEmailSerializer, \
    ChangePasswordSerializer, PaymentMethodSerializer, PaymentVerificationSerializer, ProfileChangePasswordSerializer, \
    UserProfileSerializer, UserCommunicationSerializer,CustomUserPortfolioSerializer
# Create your views here.
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from .models import CustomUser, PaymentMethod, PaymentDetails, UserProfile, UserCommunicationMode,CustomUserPortfolio
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken

from django.db.models import Q
import os
# third-party
import jwt
# standard library
import datetime
import logging

import uuid
from datetime import timedelta
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

from adifect.settings import SEND_GRID_API_key, FRONTEND_SITE_URL, LOGO_122_SERVER_PATH, BACKEND_SITE_URL, \
    SEND_GRID_FROM_EMAIL
from adifect import settings
import base64
from rest_framework import viewsets
import requests
import json
from helper.helper import StringEncoder, send_email
from agency.models import InviteMember, AgencyLevel

# Get an instance of a logger
logger = logging.getLogger('django')


class SignUpView(APIView):
    serializer_class = RegisterSerializer

    def post(self, request):
        try:
            data = request.data
            serializer = RegisterSerializer(data=data)
            if serializer.is_valid():

                if CustomUser.objects.filter(Q(email=data['email']) & Q(is_trashed=False)).exists():
                    context = {
                        'message': 'Email already exists'
                    }
                    return Response(context, status=status.HTTP_400_BAD_REQUEST)

                if CustomUser.objects.filter(username=data['username'], is_trashed=False).exists():
                    context = {
                        'message': 'Username already exists'
                    }
                    return Response(context, status=status.HTTP_400_BAD_REQUEST)

                if data['password'] != data['confirm_password']:
                    context = {
                        'message': 'Passwords do not match'
                    }
                    return Response(context, status=status.HTTP_400_BAD_REQUEST)

                user = CustomUser.objects.create(
                    username=data['username'],
                    email=data['email'],
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    role=data['role']
                )

                user.set_password(data['password'])
                if not request.data.get('email_verify'):
                    email = serializer.validated_data['email']
                    from_email = Email(SEND_GRID_FROM_EMAIL)
                    to_email = To(email)
                    token = str(uuid.uuid4())
                    decodeId = StringEncoder.encode(self, user.id)
                    subject = "Confirm Email"
                    content = Content("text/html",
                                      f'<div style="background: rgba(36, 114, 252, 0.06) !important;"><table '
                                      f'style="font: Arial, sans-serif; border-collapse: collapse; width: '
                                      f'600px; margin: 0 auto;" width="600" cellpadding="0" '
                                      f'cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 '
                                      f'0;"><div style="padding: 34px 44px; border-radius: 8px !important; '
                                      f'background: #fff; border: 1px solid #dddddd5e; margin-bottom: 50px; '
                                      f'margin-top: 50px;"><div class="email-logo"><img style="width: 165px;" '
                                      f'src="{LOGO_122_SERVER_PATH}" /></div><a href="#"></a><div '
                                      f'class="welcome-text" style="padding-top: 80px;"><h1 style="font: '
                                      f'24px;">   Welcome<span class="welcome-hand">👋</span></h1></div><div '
                                      f'class="welcome-paragraph"><div style="padding: 20px 0px; font-size: '
                                      f'16px; color: #384860;">Welcome to Adifect!</div><div style="padding: '
                                      f'10px 0px; font-size: 16px; color: #384860;">Please click the link '
                                      f'below to verify your email address.<br /></div><div '
                                      f'style="padding: 20px 0px; font-size: 16px; color: #384860;"> '
                                      f'Sincerely,<br />The Adifect Team</div></div><div style="padding-top: '
                                      f'40px; cursor: pointer !important;" class="confirm-email-button"> <a href={FRONTEND_SITE_URL}/verify-email/{token}/{decodeId} style="cursor: pointer;"><button style="height: 56px; '
                                      f'padding: 15px 44px; background: #2472fc; border-radius: 8px; '
                                      f'border-style: none; color: white; font-size: 16px; cursor: pointer !important;"> Confirm Email '
                                      f'Address</button></a></div> <div style="padding: 50px 0px;" '
                                      f'class="email-bottom-para"><div style="padding: 20px 0px; font-size: '
                                      f'16px; color: #384860;">This email was sent by Adifect. If you&#x27;d '
                                      f'rather not receive this kind of email, Don’t want any more emails '
                                      f'from Adifect? <a href="#"><span style="text-decoration: '
                                      f'underline;"> Unsubscribe.</span></a></div><div style="font-size: 16px; '
                                      f'color: #384860;"> © 2022 '
                                      f'Adifect</div></div></div></td></tr></tbody></table></div>')
                    data = send_email(from_email, to_email, subject, content)
                    user.forget_password_token = token
                else:
                    user.email_verified = True
                user.save()
                if user.role == '2':
                    agency_level = AgencyLevel.objects.create(user=user, levels=1)
                    invite_member = InviteMember.objects.create(agency=user, user=agency_level, status=1)
                return Response({'message': 'User Registered Successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({'message': f'{e} is required'}, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmail(APIView):
    lookup_url_kwarg = "token"
    lookup_url_kwarg2 = "uid"

    def get(self, request, *args, **kwargs):
        token = self.kwargs.get(self.lookup_url_kwarg)
        uid = self.kwargs.get(self.lookup_url_kwarg2)
        encoded_id = int(StringEncoder.decode(self, uid))
        user_data = CustomUser.objects.filter(id=encoded_id, email_verified=False, forget_password_token=token)
        if user_data:
            user_data.update(email_verified=True)
            context = {'message': 'Your email have been confirmed', 'status': status.HTTP_200_OK, 'error': False}
            return Response(context, status=status.HTTP_201_CREATED)
        context = {
            'message': "Something went wrong!",
            'error': True
        }
        return Response(context, status=status.HTTP_400_BAD_REQUEST)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class LoginView(GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request):
        logger.info('Login Page Accesed.')
        email = request.data['email']
        password = request.data['password']
        user = CustomUser.objects.filter(email=email, is_trashed=False).first()

        if not user:
            user = CustomUser.objects.filter(username=email, is_trashed=False).first()

        if user is None:
            logger.error('Something error wrong!')
            context = {
                'message': 'Please enter valid login details'
            }
            return Response(context, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            context = {
                'message': 'Please enter valid login details'
            }

            return Response(context, status=status.HTTP_400_BAD_REQUEST)
        if user.is_account_closed:
            context = {
                'message': 'Your old account is closed by you.',
                'error': True
            }
            return Response(context, status=status.HTTP_400_BAD_REQUEST)
        if user.is_blocked:
            context = {
                'message': 'Your Account Is Blocked.Kindly! Contact To The Administrator',
                'error': True
            }
            return Response(context, status=status.HTTP_400_BAD_REQUEST)
        if user.email_verified == False:
            context = {
                'message': 'Please confirm your email to access your account'
            }
            return Response(context, status=status.HTTP_400_BAD_REQUEST)
        if user.is_inactive == True:
            CustomUser.objects.filter(id=request.user.id).update(is_inactive=False)

        useremail = user.email
        # user_level
        agency_level = False
        if user.agency_level.all():
            agency_level = list(user.agency_level.values_list('levels', flat=True))[0]

        token = get_tokens_for_user(user)
        response = Response(status=status.HTTP_200_OK)

        # Set Token Cookie

        response.set_cookie(key='token', value=token, httponly=True)
        cache.set('token', token, 60)
        response.data = {
            'message': "Login Success",
            "user": {
                "user_id": user.id,
                "name": user.username,
                'email': useremail,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'user_level': agency_level
            },
            'token': token['access'],
            'refresh': token['refresh']
        }
        return response


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        ser = UserSerializerWithToken(self.user)
        serializer = UserSerializerWithToken(self.user).data
        for k, v in serializer.items():
            data[k] = v
        userData = CustomUser.objects.filter(id=data['id']).first()
        data.update({'role': userData.role, 'message': 'Login Successfull'})

        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class ForgetPassword(APIView):
    serializer_class = SendForgotEmailSerializer

    def post(self, request):
        urlObject = request._current_scheme_host
        email = request.data
        serializer = SendForgotEmailSerializer(data=email)
        if serializer.is_valid(raise_exception=True):
            email = request.data['email']
            user = CustomUser.objects.filter(email=email, is_trashed=False).first()
            if not user:
                user = CustomUser.objects.filter(username=email, is_trashed=False).first()
                return Response({'message': 'Email does not exists in database'}, status=status.HTTP_400_BAD_REQUEST)
            if not user.email_verified:
                context = {
                    'message': 'Please confirm your email to access your account'
                }
                return Response(context, status=status.HTTP_400_BAD_REQUEST)
            token = str(uuid.uuid4())
            token_expire_time = datetime.datetime.utcnow() + timedelta(minutes=3)
            user.forget_password_token = token
            user.token_expire_time = token_expire_time
            user.save()
            '''
            try:
                sg = sendgrid.SendGridAPIClient(api_key=SEND_GRID_API_key)
                from_email = Email("no-reply@sndright.com")
                to_email = To(email)
                subject = "Forget Password"
                content = Content("text/html",
                                  f'<div style=" background: rgba(36,114,252,0.06)!important;"><table style="font:Arial,sans-serif;border-collapse:collapse;width:600px; margin: 0 auto; " width="600" cellpadding="0" cellspacing="0"><tbody style = "width: 100%; float: left; text-align: center;"><tr style = "width: 100%;float: left; text-align: center;"><td style = "width: 100%;float: left; text-align: center;margin: 36px 0 0;"><div class ="email-logo"><img src="{LOGO_122_SERVER_PATH}" style="height: auto;width: 189px;"/></div><div style="margin-top:20px;padding:25px;border-radius:8px!important;background: #fff;border:1px solid #dddddd5e;margin-bottom: 50px;"><h1 style="font-family: arial;font-size: 26px !important;font-weight: bold !important;line-height: inherit !important;margin: 0;color: #000;"> Welcome to Adifect </h1><a href = "#"></a><h1 style = "color: #222222;font-size: 16px;font-weight: 600;line-height: 16px; font-family: arial;" > Forgot your password? </h1><p style = "font-size: 16px;font-family: arial;margin: 35px 0 35px;line-height: 24px;color: #000;" > Hi, <b>{user.first_name} {user.last_name}</b> <br> There was a request to change your password! </p><p style = "font-size: 16px; font-family: arial; margin: 25px 0 54px;line-height: 24px; color: #000;" > If did not make this request, just ignore this email.Otherwise, please <br> click the button below to change your password: </p><a href = {FRONTEND_SITE_URL}/reset-password/{token}/{user.id}/ style = "    padding: 16px 19px;border-radius: 4px; text-decoration: none;color: #fff;font-size: 12px; font-weight: bold; text-transform: uppercase; font-family: arial; background: #2472fc;"> Reset Password </a></a><p style = "font-size: 14px;font-family: arial;margin: 45px 0 10px;" > Contact us: 1-800-123-45-67 I mailto:info@adifect.com </p></div></td></tr></tbody></table></div>')
                mail = Mail(from_email, to_email, subject, content)
                mail_json = mail.get()
                response = sg.client.mail.send.post(request_body=mail_json)
            except Exception as e:
                pass
            '''
            try:
                decodeId = StringEncoder.encode(self, user.id)
                from_email = Email(SEND_GRID_FROM_EMAIL)
                to_email = To(email)
                subject = "Forget Password"

                content = Content("text/html",
                                  f'<div style="background: rgba(36, 114, 252, 0.06) !important"><table style="font: Arial, sans-serif;border-collapse: collapse;width: 600px;margin: 0 auto;"width="600"cellpadding="0"cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 0"><div style="padding: 34px 44px;border-radius: 8px !important;background: #fff;border: 1px solid #dddddd5e;margin-bottom: 50px;margin-top: 50px;"><div class="email-logo"><img style="width: 165px"src="{LOGO_122_SERVER_PATH}"/></div><a href="#"></a><div class="welcome-text"style="padding-top: 80px"><h1 style="font: 24px">Oops,</h1></div><div class="welcome-paragraph"><div style="padding: 10px 0px;font-size: 16px;color: #384860;">looks like you have forgotten your password.<br />Please click the link below to reset your<br />password!</div><div style="padding: 20px 0px;font-size: 16px;color: #384860;">Sincerely,<br />The Adifect Team</div></div><div style="padding-top: 40px"class="create-new-account"><a href="{FRONTEND_SITE_URL}/reset-password/{token}/{decodeId}/"><button style="height: 56px;padding: 15px 44px;background: #2472fc;border-radius: 8px;border-style: none;color: white;font-size: 16px;">Reset Password</button></a></div><div style="padding: 50px 0px"class="email-bottom-para"><div style="padding: 20px 0px;font-size: 16px;color: #384860;">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect?<a href="#"><span style="text-decoration: underline"> Unsubscribe.</span></a></div><div style="font-size: 16px; color: #384860">© 2022 Adifect</div></div></div></td></tr></tbody></table></div>')
                data = send_email(from_email, to_email, subject, content)
            except Exception as e:
                pass

            if data:
                return Response({'message': 'Email Send successfully, Please check your email'},
                                status=status.HTTP_200_OK)
            else:
                return Response({'message': 'There is an error to sending the data'},
                                status=status.HTTP_400_BAD_REQUEST)


class ChangePassword(GenericAPIView):
    serializer_class = ChangePasswordSerializer
    lookup_url_kwarg = "token"
    lookup_url_kwarg2 = "uid"

    def get(self, request, *args, **kwargs):
        token = self.kwargs.get(self.lookup_url_kwarg)
        uid = self.kwargs.get(self.lookup_url_kwarg2)
        encoded_id = int(StringEncoder.decode(self, uid))
        user_data = CustomUser.objects.filter(id=encoded_id, is_trashed=False).first()
        if not user_data.forget_password_token:
            return Response({'token_expire': 'Token Expired'}, status=status.HTTP_400_BAD_REQUEST)
        if token != user_data.forget_password_token:
            return Response({'token_expire': 'Token Expired'}, status=status.HTTP_400_BAD_REQUEST)
        token_expire_time = user_data.token_expire_time.replace(tzinfo=None)
        current_expire_time = datetime.datetime.utcnow()
        if current_expire_time > token_expire_time:
            return Response({'token_expire': 'Token Expired'}, status=status.HTTP_400_BAD_REQUEST)

        context = {
            'token_expire_time': token_expire_time,
            'current_expire_time': current_expire_time
        }
        response = Response(context, status=status.HTTP_200_OK)
        return response

    def put(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_data = serializer.validated_data
        password = request.data['password']
        confirm_password = request.data['confirm_password']

        if len(password) < 7 or len(confirm_password) < 7:
            return Response({'message': 'Make sure your password is at lest 7 letters'},
                            status=status.HTTP_400_BAD_REQUEST)

        if password != confirm_password:
            return Response({'message': 'Password and Confirm Password do not match'},
                            status=status.HTTP_400_BAD_REQUEST)

        user_id = int(StringEncoder.decode(self, self.kwargs.get(self.lookup_url_kwarg2)))
        user_data = CustomUser.objects.get(id=user_id, is_trashed=False)
        user_data.set_password(password)
        user_data.forget_password_token = None
        user_data.save()
        if user_data != 0:
            return Response({'message': 'Your Password updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'There is an error to updating the data'}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
class PaymentMethodViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentMethodSerializer
    queryset = PaymentMethod.objects.filter(is_trashed=False)


@permission_classes([IsAuthenticated])
class PaymentVerification(APIView):
    serializer_class = PaymentVerificationSerializer

    def post(self, request):
        headers = {
            'Content-type': 'application/json',
        }
        data = '{"AppKey":"' + settings.MOOV_APPKEY + '","Login":"' + settings.MOOV_LOGIN + '","Password":"' + settings.MOOV_PASSWORD + '"}'
        print(data)
        x = requests.post(settings.MOOV_LOGIN_TAX_API_URL, headers=headers, data=data)
        if x.text != '':
            json_object = json.loads(x.text)
            print(json_object)
            session_id = json_object["sessionId"]
            print(session_id)
            headers = {'Content-type': 'application/json', "Accept": "application/json",
                       "Authorization": "Bearer " + session_id}
            move_data = json.dumps([
                {
                    "ClientPayerId": request.data.get("clientPayerId", ""),
                    "Tintype": request.data.get("tintype", ""),
                    "payerTin": request.data.get("payerTin", ""),
                    "ssn": request.data.get("ssn", ""),
                    "firstName": request.data.get("first_name", ""),
                    "middleName": request.data.get("middle_name", ""),
                    "LastNameOrBusinessName": request.data.get("last_name", ""),
                    "suffix": request.data.get("suffix", ""),
                    "address": request.data.get("address_1", ""),
                    "address2": request.data.get("address_2", ""),
                    "city": request.data.get("city", ""),
                    "state": request.data.get("state", ""),
                    "zipCode": request.data.get("zipCode", ""),
                    "country": request.data.get("country", ""),
                    "phone": request.data.get("phone_number", ""),
                    "email": request.data.get("email", ""),
                    "lastFiling": request.data.get("last_filing", None),
                    "combinedFedStateFiling": request.data.get("combined_fed_state_filing", None),
                }
            ])
            resp = requests.post(settings.MOOV_SAVE_PAYER_URL_2, headers=headers, data=move_data)
            json_object2 = json.loads(resp.text)
            if json_object2['statusCode'] != 200:
                context = {'message': 'Something Went Wrong', 'error': True, 'status': status.HTTP_400_BAD_REQUEST}
            else:
                data = request.data
                serializer = self.serializer_class(data=data)
                if serializer.is_valid():
                    serializer.save()
                    context = {'message': 'Success', 'error': False, 'status': status.HTTP_200_OK}
        else:
            context = {'message': 'Something Went Wrong', 'error': True, 'status': status.HTTP_400_BAD_REQUEST}
        return Response(context, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
class EmailChange(APIView):
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        data = self.serializer_class(data=request.data)
        if data.is_valid():
            email = data.validated_data.get('email', None)
            password = data.validated_data.get('password', None)
            user = CustomUser.objects.filter(id=request.user.id).first()
            old_email = user.email
            if not user.check_password(password):
                context = {
                    'message': 'Please enter valid login details'
                }
                return Response(context, status=status.HTTP_400_BAD_REQUEST)

            if user.email == email:
                context = {
                    'message': 'Please enter new Email.'
                }
                return Response(context, status=status.HTTP_400_BAD_REQUEST)

            if CustomUser.objects.filter(email=email).exclude(id=request.user.id):
                context = {
                    'message': 'Email Already Registered.'
                }
                return Response(context, status=status.HTTP_400_BAD_REQUEST)

            from_email = Email(SEND_GRID_FROM_EMAIL)
            to_email = To(old_email)
            subject = "Change Password"

            content = content = Content("text/html",
                                        f'<div style="background: rgba(36, 114, 252, 0.06) !important"><table style="font: Arial, sans-serif;border-collapse: collapse;width: 600px;margin: 0 auto;"width="600"cellpadding="0"cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 0"><div style="padding: 34px 44px;border-radius: 8px !important;background: #fff;border: 1px solid #dddddd5e;margin-bottom: 50px;margin-top: 50px;"><div class="email-logo"><img style="width: 165px"src="{LOGO_122_SERVER_PATH}"/></div><a href="#"></a><div class="welcome-text"style="padding-top: 80px"><h1 style="font: 24px">Congratulations,</h1></div><div class="welcome-paragraph"><div style="padding: 10px 0px;font-size: 16px;color: #384860;">Your Email is changed as per your request.<br /></div><div style="padding: 20px 0px;font-size: 16px;color: #384860;">Sincerely,<br />The Adifect Team</div></div><div style="padding-top: 40px"class="create-new-account"><a href=""></a></div><div style="padding: 50px 0px"class="email-bottom-para"><div style="padding: 20px 0px;font-size: 16px;color: #384860;">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect?<a href="#"><span style="text-decoration: underline"> Unsubscribe.</span></a></div><div style="font-size: 16px; color: #384860">© 2022 Adifect</div></div></div></td></tr></tbody></table></div>')
            data = send_email(from_email, to_email, subject, content)

            user.email = email
            user.email_verified = False
            from_email = Email(SEND_GRID_FROM_EMAIL)
            to_email = To(email)
            token = str(uuid.uuid4())
            decodeId = StringEncoder.encode(self, user.id)
            subject = "Confirm Email"
            content = Content("text/html", f'<div style="background: rgba(36, 114, 252, 0.06) !important;"><table '
                                           f'style="font: Arial, sans-serif; border-collapse: collapse; width: '
                                           f'600px; margin: 0 auto;" width="600" cellpadding="0" '
                                           f'cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 '
                                           f'0;"><div style="padding: 34px 44px; border-radius: 8px !important; '
                                           f'background: #fff; border: 1px solid #dddddd5e; margin-bottom: 50px; '
                                           f'margin-top: 50px;"><div class="email-logo"><img style="width: 165px;" '
                                           f'src="{LOGO_122_SERVER_PATH}" /></div><a href="#"></a><div '
                                           f'class="welcome-text" style="padding-top: 80px;"><h1 style="font: '
                                           f'24px;">   Welcome<span class="welcome-hand">👋</span></h1></div><div '
                                           f'class="welcome-paragraph"><div style="padding: 20px 0px; font-size: '
                                           f'16px; color: #384860;">Welcome to Adifect!</div><div style="padding: '
                                           f'10px 0px; font-size: 16px; color: #384860;">Please click the link '
                                           f'below to verify your email address.<br /></div><div '
                                           f'style="padding: 20px 0px; font-size: 16px; color: #384860;"> '
                                           f'Sincerely,<br />The Adifect Team</div></div><div style="padding-top: '
                                           f'40px; cursor: pointer !important;" class="confirm-email-button"> <a href={FRONTEND_SITE_URL}/verify-email/{token}/{decodeId} style="cursor: pointer;"><button style="height: 56px; '
                                           f'padding: 15px 44px; background: #2472fc; border-radius: 8px; '
                                           f'border-style: none; color: white; font-size: 16px; cursor: pointer !important;"> Confirm Email '
                                           f'Address</button></a></div> <div style="padding: 50px 0px;" '
                                           f'class="email-bottom-para"><div style="padding: 20px 0px; font-size: '
                                           f'16px; color: #384860;">This email was sent by Adifect. If you&#x27;d '
                                           f'rather not receive this kind of email, Don’t want any more emails '
                                           f'from Adifect? <a href="#"><span style="text-decoration: '
                                           f'underline;"> Unsubscribe.</span></a></div><div style="font-size: 16px; '
                                           f'color: #384860;"> © 2022 '
                                           f'Adifect</div></div></div></td></tr></tbody></table></div>')
            data = send_email(from_email, to_email, subject, content)
            user.forget_password_token = token
            user.save()
            return Response({'message': 'Your email updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': data.errors}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
class ProfileChangePassword(APIView):
    serializer_class = ProfileChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        data = self.serializer_class(data=request.data)
        if data.is_valid():
            new_password = data.validated_data.get('new_password', None)
            confirm_password = data.validated_data.get('confirm_password', None)
            current_password = data.validated_data.get('current_password', None)
            user = CustomUser.objects.filter(id=request.user.id).first()
            email = request.user.email
            if new_password != confirm_password:
                return Response({'message': 'New Password and Confirm Password do not match'},
                                status=status.HTTP_400_BAD_REQUEST)
            if not user.check_password(current_password):
                context = {
                    'message': 'Please enter valid current_password.'
                }
                return Response(context, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(new_password)
            user.save()

            from_email = Email(SEND_GRID_FROM_EMAIL)
            to_email = To(email)
            subject = "Change Password"

            content = Content("text/html",
                              f'<div style="background: rgba(36, 114, 252, 0.06) !important"><table style="font: Arial, sans-serif;border-collapse: collapse;width: 600px;margin: 0 auto;"width="600"cellpadding="0"cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 0"><div style="padding: 34px 44px;border-radius: 8px !important;background: #fff;border: 1px solid #dddddd5e;margin-bottom: 50px;margin-top: 50px;"><div class="email-logo"><img style="width: 165px"src="{LOGO_122_SERVER_PATH}"/></div><a href="#"></a><div class="welcome-text"style="padding-top: 80px"><h1 style="font: 24px">Congratulations,</h1></div><div class="welcome-paragraph"><div style="padding: 10px 0px;font-size: 16px;color: #384860;">Your Password has been Changed.<br /></div><div style="padding: 20px 0px;font-size: 16px;color: #384860;">Sincerely,<br />The Adifect Team</div></div><div style="padding-top: 40px"class="create-new-account"><a href=""></a></div><div style="padding: 50px 0px"class="email-bottom-para"><div style="padding: 20px 0px;font-size: 16px;color: #384860;">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect?<a href="#"><span style="text-decoration: underline"> Unsubscribe.</span></a></div><div style="font-size: 16px; color: #384860">© 2022 Adifect</div></div></div></td></tr></tbody></table></div>')
            data = send_email(from_email, to_email, subject, content)
            if data:
                return Response({'message': 'Confirmation Email Sent to your Account.'}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'There is an error to sending the data'},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message': data.errors}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
class CloseAccount(APIView):
    def post(self, request, *args, **kwargs):

        try:
            password = request.data.get('password', None)
            user = CustomUser.objects.filter(id=request.user.id).first()
            if not user.check_password(password):
                context = {
                    'message': 'Please enter valid login details.'
                }
                return Response(context, status=status.HTTP_400_BAD_REQUEST)
            user = CustomUser.objects.filter(id=request.user.id).update(is_account_closed=True)
            request.user.delete()
            return Response({'message': 'Your account is Deactivated'}, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response({'message': f'{e} is required'}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
class InActiveAccount(APIView):

    def post(self, request, *args, **kwargs):

        try:
            password = request.data.get('password', None)
            user = CustomUser.objects.filter(id=request.user.id).first()
            if not user.check_password(password):
                context = {
                    'message': 'Please enter valid login details.'
                }
                return Response(context, status=status.HTTP_400_BAD_REQUEST)
            user = CustomUser.objects.filter(id=request.user.id).update(is_inactive=True)
            return Response({'message': 'Your account is Inactive now.'}, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response({'message': f'{e} is required'}, status=status.HTTP_400_BAD_REQUEST)



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

def validate_portfolio_images(images):
    error = 0
    for img in images:
        ext = os.path.splitext(img.name)[1]
        valid_extensions = ['.jpg', '.jpeg', '.png']
        if not ext.lower() in valid_extensions:
            error += 1
    return error
@permission_classes([IsAuthenticated])
class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    queryset = UserProfile.objects.all()
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['user']
    search_fields = ['=user', ]

    # pagination_class = FiveRecordsPagination
    # http_method_names = ['get']
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).filter(user=request.user)
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            if serializer.validated_data.get('profile_img'):
                profile_error = validate_profile_image_video(serializer.validated_data['profile_img'], 'img')
                if profile_error != 0:
                    return Response({'message': "Invalid profile images"}, status=status.HTTP_400_BAD_REQUEST)
            if serializer.validated_data.get('video'):
                profile_video_error = validate_profile_image_video(serializer.validated_data['video'], 'video')
                if profile_video_error != 0:
                    return Response({'message': "Invalid video format"}, status=status.HTTP_400_BAD_REQUEST)
            self.perform_create(serializer)
            context = {
                'message': 'Created Successfully',
                'status': status.HTTP_201_CREATED,
                'errors': serializer.errors,
                'data': serializer.data,
            }
            return Response(context)
        context = {
            'message': 'Error',
            'status': status.HTTP_400_BAD_REQUEST,
            'errors': serializer.errors,
        }
        return Response(context)


    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        if serializer.is_valid():
            if serializer.validated_data.get('profile_img'):
                profile_error = validate_profile_image_video(serializer.validated_data['profile_img'], 'img')
                if profile_error != 0:
                    return Response({'message': "Invalid profile images"}, status=status.HTTP_400_BAD_REQUEST)
            if serializer.validated_data.get('video'):
                profile_video_error = validate_profile_image_video(serializer.validated_data['video'], 'video')
                if profile_video_error != 0:
                    return Response({'message': "Invalid video format"}, status=status.HTTP_400_BAD_REQUEST)
            self.perform_update(serializer)
            context = {
                'message': 'Updated Succesfully',
                'status': status.HTTP_200_OK,
                'errors': serializer.errors,
                'data': serializer.data,
            }
            return Response(context)
        context = {
            'message': 'Error',
            'status': status.HTTP_400_BAD_REQUEST,
            'errors': serializer.errors,
        }
        return Response(context)

@permission_classes([IsAuthenticated])
class CustomUserPortfolioViewSet(viewsets.ModelViewSet):
    serializer_class = CustomUserPortfolioSerializer
    queryset = CustomUserPortfolio.objects.all()
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['user']
    search_fields = ['=user', ]

    # pagination_class = FiveRecordsPagination
    # http_method_names = ['get']
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).filter(user=request.user)
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        portfolio = request.FILES.getlist('portfolio')
        remove_portfolio_ids = request.data.getlist('remove_portfolio', None)
        if remove_portfolio_ids:
            for id in remove_portfolio_ids:
                CustomUserPortfolio.objects.filter(id=id).delete()
        if portfolio:
            portfolio_error = validate_portfolio_images(portfolio)
            if portfolio_error != 0:
                return Response({'message': "Invalid portfolio images"}, status=status.HTTP_400_BAD_REQUEST)
            for img in portfolio:
                CustomUserPortfolio.objects.create(user_id=request.user.id, portfolio_images=img)
            context = {
                'message': 'Portfolio Uploaded Succfully',
                'status': status.HTTP_200_OK,
                'errors': False,
            }
            return Response(context)
        context = {
            'message': 'No Data Found',
            'status': status.HTTP_400_BAD_REQUEST,
            'errors': True,
        }
        return Response(context)

@permission_classes([IsAuthenticated])
class UserCommunicationViewSet(viewsets.ModelViewSet):
    serializer_class = UserCommunicationSerializer
    queryset = UserCommunicationMode.objects.all()
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['modified', 'created']
    ordering = ['modified', 'created']
    filterset_fields = ['user']
    search_fields = ['=user', ]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).filter(user=request.user)
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            if serializer.validated_data.get('communication_mode') == 0:
                if UserCommunicationMode.objects.filter(communication_mode=0,
                                                        mode_value=serializer.validated_data.get(
                                                            'mode_value')).exists():
                    return Response({'message': "Email is Already added."}, status=status.HTTP_400_BAD_REQUEST)
            if serializer.validated_data.get('communication_mode') == 1:
                if UserCommunicationMode.objects.filter(communication_mode=1, mode_value=serializer.validated_data.get(
                        'mode_value')).exists():
                    return Response({'message': "Phone number is Already added."}, status=status.HTTP_400_BAD_REQUEST)
            user = self.queryset.filter(user=request.user, is_preferred=True)
            if serializer.validated_data['is_preferred'] is True:
                user.update(is_preferred=False)
            self.perform_create(serializer)
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
                'data': serializer.data,
            }
            return Response(context, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        if serializer.is_valid():
            if serializer.validated_data['is_preferred'] is True:
                self.get_queryset().filter(user=instance.user, is_preferred=True).update(is_preferred=False)
            self.perform_update(serializer)
            context = {
                    'message': 'Updated Succesfully',
                    'status': status.HTTP_200_OK,
                    'errors': serializer.errors,
                    'data': serializer.data,
            }
        else:
           return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response(context)
        

def block_tokens_for_user(user):
    token = RefreshToken(user)
    token.blacklist()
    print("hiityyy")
    return True



@permission_classes([IsAuthenticated])
class logout_test(APIView):
    def get(self, request, *args, **kwargs):

        try:
            print('hit')
            print(request.GET.get('token'))
            block_tokens_for_user(request.GET.get('token'))
            print("done")
            return Response({'message': 'Your account is Deactivated'}, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response({'message': f'{e} is required'}, status=status.HTTP_400_BAD_REQUEST)