"""
Django settings for adifect project.

Generated by 'django-admin startproject' using Django 3.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

from pathlib import Path
import os
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-^r8dr13s8wlx5kkvg6)g3dha7=4mtangi6=@xo&ac5v)1x8cb4'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',
    
    'storages',
    'rest_framework',
    'corsheaders',
    'authentication',
    'administrator',
    'creator',
    'agency',

    # 'category'    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware'
]

CSRF_TRUSTED_ORIGINS = ['http://192.168.1.245:8001']

ROOT_URLCONF = 'adifect.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        # 'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'adifect.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'adifect',
        'USER': 'postgres',
        'PASSWORD': 'studio45#',
        'HOST': '192.168.1.245',
        'port': '5432',
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

#STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)
# STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static'), ] 

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'authentication.CustomUser'

CORS_ALLOWED_ORIGINS = [
    'http://192.168.1.245:3001',
    'http://122.160.74.251:3001',
    'http://localhost:3001'

]

SEND_GRID_API_key = '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'
SEND_GRID_FROM_EMAIL = "no-reply@sndright.com"

FRONTEND_SITE_URL = 'http://122.160.74.251:3001'
BACKEND_SITE_URL = 'http://122.160.74.251:8001'
# LOGO_122_SERVER_PATH = 'http://122.160.74.251/studio45creations-dev/adifect/logo/logo.svg'
LOGO_122_SERVER_PATH = 'http://122.160.74.251/studio45creations-dev/adifect/logo/logo.png'

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    # 'PAGE_SIZE': 1,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),

    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend']
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

AWS_ACCESS_KEY_ID = 'AKIA36VDHMT3BA4AR7WS'
AWS_SECRET_ACCESS_KEY = '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'
AWS_STORAGE_BUCKET_NAME = 'adifect'
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_REGION_NAME = 'ap-south-1'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_VERIFY = True
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Moov API Details
# MOOOV_DETAILS
MOOV_APPKEY = "8103QNSWC3XROQJ3FB9HM1A88CP1I490"
MOOV_LOGIN = "adamwittcop@txtred.com"
MOOV_PASSWORD = "Tax1099!"
MOOV_LOGIN_TAX_API_URL = 'https://tax1099api.1099cloud.com/api/v1/Login'
MOOV_SAVE_PAYER_URL_2 = "https://apipayer.1099cloud.com/api/v1/Payer/Save"
SKYPE_USERNAME = 'muskeshbhandari20@gmail.com'
SKYPE_PASSWORD = 'mukesh@studio45'
TWILIO_NUMBER = '+12058131912'
TWILIO_ACCOUNT_SID = 'AC4b620dd6c441a36c4de6e23abbc89f87'
TWILIO_AUTH_TOKEN = '57d86eba89a7f4bbd43989a0cd1a3145'
#---------- 2nd twillio -----------------------------#
TWILIO_NUMBER_WHATSAPP = 'whatsapp:+14155238886'
TWILIO_ACCOUNT_SID2 = 'ACcf61c478eed9d6a982577ecd8d908d73'
TWILIO_AUTH_TOKEN2 = '562c8ab115e0750140bc7584fd2640c6'
#----------------- end ------------------------------#
# WS_ACCESS_KEY = 'AKIA4TDB7U23RT7PE3MR'
# AWS_SECRET_KEY = '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'
# AWS_BUCKET_NAME = 'sndright-public-mms-uploadss'
# AWS_REGION_NAME='ap-south-1
