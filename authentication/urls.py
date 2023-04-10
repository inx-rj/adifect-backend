from django.urls import path

from .views import SignUpView, ForgetPassword, ChangePassword, LoginView, CustomTokenRefreshView
from . import views
from rest_framework import routers
router = routers.DefaultRouter()
router.register(r'payment-method', views.PaymentMethodViewSet, basename='payment_method')
router.register(r'user-profile', views.UserProfileViewSet, basename='user_profile')
router.register(r'user1-portfolio', views.CustomUserPortfolioViewSet, basename='user_portfolio')
router.register(r'user-communication', views.UserCommunicationViewSet, basename='user_communication')
urlpatterns = [
    path('registerview/', SignUpView.as_view(), name='registerview'),
    path('loginview/', LoginView.as_view(), name='loginview'),
    path('forget-password/', ForgetPassword.as_view(), name='forget-password'),
    path('reset-password/<str:token>/<str:uid>/', ChangePassword.as_view(), name='reset-password'),
    path('payment-verification', views.PaymentVerification.as_view(), name='payment_verification'),
    path('verify-email/<str:token>/<str:uid>/', views.VerifyEmail.as_view(), name='verify_email'),
    path('email-change/', views.EmailChange.as_view(), name='email_change'),
    path('profile-password-change/', views.ProfileChangePassword.as_view(), name='profile_password_change'),
    path('close-account/', views.CloseAccount.as_view(), name='close_account'),
    path('in-active-user/', views.InActiveAccount.as_view(), name='in_active_user'),
    path('logout_test/', views.logout_test.as_view(), name='logout_test'),
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
]
urlpatterns += router.urls
