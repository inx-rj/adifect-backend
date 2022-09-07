from django.urls import path
from .views import SignUpView, ForgetPassword , ChangePassword, LoginView
from . import  views
from rest_framework import routers
router = routers.DefaultRouter()
router.register(r'payment-method', views.PaymentMethodViewSet, basename='payment_method')
urlpatterns = [
    path('registerview/', SignUpView.as_view(), name='registerview'),
    path('loginview/', LoginView.as_view(), name='loginview'),
    path('forget-password/', ForgetPassword.as_view(), name='forget-password'),
    path('reset-password/<str:token>/<str:uid>/', ChangePassword.as_view(), name='reset-password'),
    path('payment-verification', views.PaymentVerification.as_view(), name='payment_verification')
]
urlpatterns += router.urls