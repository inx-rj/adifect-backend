from django.urls import path
from rest_framework import routers
from .import views
  
router = routers.DefaultRouter()

router.register(r'latest-jobs', views.LatestsJobsViewSet, basename='latest_jobs')
router.register(r'job-applied', views.JobAppliedViewSet, basename='job_applied')
router.register(r'creator-jobs', views.CreatorJobsViewSet, basename='creator_jobs')
router.register(r'my-jobs', views.MyJobsViewSet, basename='my_jobs')
router.register(r'public-job-api', views.PublicJobViewApi, basename='public_job_api')
router.register(r'available-jobs', views.AvailableJobs, basename='available_jobs')
router.register(r'job-activity', views.JobActivityCreaterViewSet, basename='job_activity')
router.register(r'creator-job-count',  views.CreatorJobsCountViewSet, basename='creator_job_count')



urlpatterns = [
    path('my-project-all/', views.MyProjectAllJob.as_view(), name='my_project_all'),
    path('creator-company-list', views.CreatorCompanyList.as_view(), name='creator_company_list'),
    path('get-resubmit-work/', views.GetRejectedWork.as_view(), name='get_resubmit_work'),
    path('get-task-list/', views.GetTaskList.as_view(), name='get_task_list'),
]
urlpatterns += router.urls