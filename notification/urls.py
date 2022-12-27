from django.urls import path
from rest_framework import routers
from . import views
urlpatterns = [
        path('test-modal/', views.testmedia.as_view(), name='test_modal'),
        path('get-test-modal/<int:id>/', views.get_media.as_view(), name='get_test_modal'),
]