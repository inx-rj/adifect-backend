from django.urls import path
from rest_framework import routers
from .import views
  
router = routers.DefaultRouter()

router.register(r'latest-jobs', views.LatestsJobsViewSet, basename='latest_jobs')
router.register(r'job-applied', views.JobAppliedViewSet, basename='job_applied')
router.register(r'creator-jobs', views.CreatorJobsViewSet, basename='creator_jobs')

urlpatterns = []
urlpatterns += router.urls