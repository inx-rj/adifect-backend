from argparse import Action
from cProfile import label
from http.client import HTTPResponse
from urllib import request
from django.core.cache import cache
from django.shortcuts import render
from .serializers import RegisterSerializer, UserSerializer, SendForgotEmailSerializer, \
    ChangePasswordSerializer, PaymentMethodSerializer, PaymentVerificationSerializer
# Create your views here.
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from .models import CustomUser, PaymentMethod, PaymentDetails
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
# third-party
import jwt
# standard library
import datetime
import logging

import uuid
from datetime import timedelta
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

from adifect.settings import SEND_GRID_API_key, FRONTEND_SITE_URL, LOGO_122_SERVER_PATH, BACKEND_SITE_URL,SEND_GRID_FROM_EMAIL
from adifect import settings
import base64
from rest_framework import viewsets
import requests
import json
from agency.helper import StringEncoder,send_email
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
                email = serializer.validated_data['email']
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
                                               f'below to verify your email<br /></div><div '
                                               f'style="padding: 20px 0px; font-size: 16px; color: #384860;"> '
                                               f'Sincerely,<br />The Adifect Team</div></div><div style="padding-top: '
                                               f'40px;" class="confirm-email-button"> <a href={FRONTEND_SITE_URL}/verify-email/{token}/{decodeId}/><button style="height: 56px; '
                                               f'padding: 15px 44px; background: #2472fc; border-radius: 8px; '
                                               f'border-style: none; color: white; font-size: 16px;"> Confirm Email '
                                               f'Address</button></a></div> <div style="padding: 50px 0px;" '
                                               f'class="email-bottom-para"><div style="padding: 20px 0px; font-size: '
                                               f'16px; color: #384860;">This email was sent by Adifect. If you&#x27;d '
                                               f'rather not receive this kind of email, Don’t want any more emails '
                                               f'from Adifect?<a href="#"><span style="text-decoration: '
                                               f'underline;">Unsubscribe.</span></a></div><div style="font-size: 16px; '
                                               f'color: #384860;"> © 2022 '
                                               f'Adifect</div></div></div></td></tr></tbody></table></div>')
                data = send_email(from_email, to_email, subject, content)
                user.forget_password_token = token
                user.save()
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
        user_data = CustomUser.objects.filter(id=encoded_id, email_verified=False).first()
        if user_data:
            if token == user_data.forget_password_token:
                user_data.email_verified = True
                user_data.save()
                return Response({'message': 'Your email have been confirmed','status':status.HTTP_200_OK,'error':False}, status=status.HTTP_200_OK)

        context = {
            'message': "something went wrong!"
        }
        response = Response(context, status=status.HTTP_400_BAD_REQUEST)
        return response


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
        if user.email_verified == False:
            context = {
                'message': 'Please confirm your email to access your account'
            }
            return Response(context, status=status.HTTP_400_BAD_REQUEST)

        useremail = user.email

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
                'role': user.role
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
            else:
                token = str(uuid.uuid4())
                token_expire_time = datetime.datetime.utcnow() + timedelta(minutes=15)
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
                                      f'<div style="background: rgba(36, 114, 252, 0.06) !important"><table style="font: Arial, sans-serif;border-collapse: collapse;width: 600px;margin: 0 auto;"width="600"cellpadding="0"cellspacing="0"><tbody><tr><td style="width: 100%; margin: 36px 0 0"><div style="padding: 34px 44px;border-radius: 8px !important;background: #fff;border: 1px solid #dddddd5e;margin-bottom: 50px;margin-top: 50px;"><div class="email-logo"><img style="width: 165px"src="{LOGO_122_SERVER_PATH}"/></div><a href="#"></a><div class="welcome-text"style="padding-top: 80px"><h1 style="font: 24px">Opps,</h1></div><div class="welcome-paragraph"><div style="padding: 10px 0px;font-size: 16px;color: #384860;">looks like you have forgotten your password.<br />Please click the link below to reset your<br />password!</div><div style="padding: 20px 0px;font-size: 16px;color: #384860;">Sincerely,<br />The Adifect Team</div></div><div style="padding-top: 40px"class="create-new-account"><a href="{FRONTEND_SITE_URL}/reset-password/{token}/{decodeId}/"><button style="height: 56px;padding: 15px 44px;background: #2472fc;border-radius: 8px;border-style: none;color: white;font-size: 16px;">Reset Password</button></a></div><div style="padding: 50px 0px"class="email-bottom-para"><div style="padding: 20px 0px;font-size: 16px;color: #384860;">This email was sent by Adifect. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Adifect?<a href="#"><span style="text-decoration: underline">Unsubscribe.</span></a></div><div style="font-size: 16px; color: #384860">© 2022 Adifect</div></div></div></td></tr></tbody></table></div>')
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

        user_id = int(StringEncoder.decode(self,self.kwargs.get(self.lookup_url_kwarg2)))
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
