from django.urls import path
from .views import SignUpView,  Fast2SMS, ForgetPassword , ChangePassword, LoginView

urlpatterns = [
    path('registerview/', SignUpView.as_view(), name='registerview'),
    path('loginview/', LoginView.as_view(), name='loginview'),
    path('fast2sms/', Fast2SMS.as_view(),name='fast2sms'),
    path('forget-password/', ForgetPassword.as_view(), name='forget-password'),
    path('reset-password/<str:token>/<str:uid>/', ChangePassword.as_view(), name='reset-password'),
]