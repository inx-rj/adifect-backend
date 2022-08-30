from argparse import Action
from cProfile import label
from http.client import HTTPResponse
from urllib import request
from django.core.cache import cache
from django.shortcuts import render
from .serializers import RegisterSerializer, UserSerializer, Fast2SMSSerializer, SendForgotEmailSerializer, ChangePasswordSerializer   
# Create your views here.
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from .models import CustomUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
# third-party
import jwt
# standard library
import datetime
import logging

import uuid
from datetime import timedelta
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

from adifect.settings import SEND_GRID_API_key,FRONTEND_SITE_URL,LOGO_122_SERVER_PATH
import base64


# Get an instance of a logger
logger = logging.getLogger('django')

class SignUpView(APIView):
    serializer_class = RegisterSerializer

    def post(self, request):
        try:
            data = request.data
            serializer = RegisterSerializer(data=data)
            if serializer.is_valid():  
                
                if CustomUser.objects.filter(email=data['email']).exists():
                    context = {
                            'message': 'Email already exists'
                        }
                    return Response(context, status=status.HTTP_400_BAD_REQUEST)

                if CustomUser.objects.filter(username=data['username']).exists():
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
                user.save()
                return Response({'message': 'User Registered Successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except KeyError as e:
            return Response({'message': f'{e} is required'}, status=status.HTTP_400_BAD_REQUEST)


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
        user = CustomUser.objects.filter(email=email).first()
    
        if not user:
            user = CustomUser.objects.filter(username=email).first()
    
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

        useremail = user.email

        token = get_tokens_for_user(user)
        response = Response(status=status.HTTP_200_OK)

        # Set Token Cookie

        response.set_cookie(key='token', value=token, httponly=True)
        cache.set('token', token, 60)
        response.data = {
            'message': "Login Success",
            "user": {
                "user_id" : user.id,
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



class Fast2SMS(APIView):
    serializer_class = Fast2SMSSerializer
    def post(self, request):
        print(request.data)

        # mention url
        url = "https://www.fast2sms.com/dev/bulk"
        
        # create a dictionary
        my_data = {
            # Your default Sender ID
            'sender_id': 'FastSM', 
            
            # Put your message here!
            'message': 'This is a test message', 
            
            'language': 'english',
            'route': 'p',
            
            # You can send sms to multiple numbers
            # separated by comma.
            # 'numbers': '9999999999, 7777777777, 6666666666'    
            'numbers': '9700059005, 8219757476, 9459379141'    
        }
        
        # create a dictionary
        headers = {
            'authorization': 'DNjhHoOwf3vQW0LFyPUA82nsStJib9Iq5lYR46dMTXVBzGkamKwa24iKkNgIJvQVMTnWZbofBs8qUypP',
            'Content-Type': "application/x-www-form-urlencoded",
            'Cache-Control': "no-cache"
        }


        # make a post request
        response = requests.request("POST",
                                    url,
                                    data = my_data,
                                    headers = headers)



        print(response)
        # return Response(response)

        # load json data from source
        if response.text:
            returned_msg = json.loads(response.text)
            print(returned_msg['message'])
        else:
            print("else")



        context = {
                    'message': 'Fast2SMS'
                  }
        return Response(context, status=status.HTTP_200_OK)
        # return HTTPResponse("hjkfdhgd")


class ForgetPassword(APIView):
    serializer_class = SendForgotEmailSerializer

    def post(self, request):      
        urlObject = request._current_scheme_host
        email = request.data
        serializer = SendForgotEmailSerializer(data=email)
        if serializer.is_valid(raise_exception=True):
            email = request.data['email']
            user = CustomUser.objects.filter(email=email).first()
            if not user:
                user = CustomUser.objects.filter(username=email).first()
                return Response({'message': 'Email does not exists in database'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                token = str(uuid.uuid4())
                token_expire_time = datetime.datetime.utcnow() + timedelta(minutes=15)
                user.forget_password_token = token
                user.token_expire_time = token_expire_time
                user.save()         
                
                try:
                    sg = sendgrid.SendGridAPIClient(api_key=SEND_GRID_API_key)
                    from_email = Email("no-reply@sndright.com")
                    to_email = To(email)
                    subject = "Forget Password"
                    content = Content("text/html",f'<div style=" background: rgba(36,114,252,0.06)!important;"><table style="font:Arial,sans-serif;border-collapse:collapse;width:600px; margin: 0 auto; " width="600" cellpadding="0" cellspacing="0"><tbody style = "width: 100%; float: left; text-align: center;"><tr style = "width: 100%;float: left; text-align: center;"><td style = "width: 100%;float: left; text-align: center;margin: 36px 0 0;"><div class ="email-logo"><img src="{LOGO_122_SERVER_PATH}" style="height: auto;width: 189px;"/></div><div style="margin-top:20px;padding:25px;border-radius:8px!important;background: #fff;border:1px solid #dddddd5e;margin-bottom: 50px;"><h1 style="font-family: arial;font-size: 26px !important;font-weight: bold !important;line-height: inherit !important;margin: 0;color: #000;"> Welcome to Adifect </h1><a href = "#"></a><h1 style = "color: #222222;font-size: 16px;font-weight: 600;line-height: 16px; font-family: arial;" > Forgot your password? </h1><p style = "font-size: 16px;font-family: arial;margin: 35px 0 35px;line-height: 24px;color: #000;" > Hi, <b>{user.first_name} {user.last_name}</b> <br> There was a request to change your password! </p><p style = "font-size: 16px; font-family: arial; margin: 25px 0 54px;line-height: 24px; color: #000;" > If did not make this request, just ignore this email.Otherwise, please <br> click the button below to change your password: </p><a href = {FRONTEND_SITE_URL}/reset-password/{token}/{user.id}/ style = "    padding: 16px 19px;border-radius: 4px; text-decoration: none;color: #fff;font-size: 12px; font-weight: bold; text-transform: uppercase; font-family: arial; background: #2472fc;"> Reset Password </a></a><p style = "font-size: 14px;font-family: arial;margin: 45px 0 10px;" > Contact us: 1-800-123-45-67 I mailto:info@adifect.com </p></div></td></tr></tbody></table></div>')
                    mail = Mail(from_email, to_email, subject, content)
                    mail_json = mail.get()
                    response = sg.client.mail.send.post(request_body=mail_json)
                except Exception as e:
                    pass                
                
                if user != 0:
                    return Response({'message': 'Email Send successfully, Please check your email'}, status=status.HTTP_200_OK)
                else:
                    return Response({'message': 'There is an error to sending the data'}, status=status.HTTP_400_BAD_REQUEST)


class ChangePassword(GenericAPIView):    
    serializer_class = ChangePasswordSerializer
    lookup_url_kwarg = "token"
    lookup_url_kwarg2 = "uid"

    def get(self, request,*args,**kwargs):
        token = self.kwargs.get(self.lookup_url_kwarg)
        uid = self.kwargs.get(self.lookup_url_kwarg2)
        user_data = CustomUser.objects.filter(id=uid).first()        
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
            'current_expire_time':current_expire_time
        }
        response = Response(context,status=status.HTTP_200_OK)
        return response


    def put(self,request,*args,**kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_data = serializer.validated_data
        password = request.data['password']
        confirm_password = request.data['confirm_password']

        if len(password) < 7 or len(confirm_password) <7:            
            return Response({'message': 'Make sure your password is at lest 7 letters'}, status=status.HTTP_400_BAD_REQUEST)

        if password != confirm_password:            
            return Response({'message': 'Password and Confirm Password do not match'}, status=status.HTTP_400_BAD_REQUEST)

        user_id = self.kwargs.get(self.lookup_url_kwarg2)    
        user_data = CustomUser.objects.get(id=user_id)
        user_data.set_password(password)
        user_data.forget_password_token = None                
        user_data.save()

        if user_data != 0:
            return Response({'message': 'Your Password updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'There is an error to updating the data'}, status=status.HTTP_400_BAD_REQUEST)

   