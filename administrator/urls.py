from django.urls import path
# from .views import ProfileEdit, JobFilterApi, LatestJobAPI
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='categories')
router.register(r'jobs', views.JobViewSet, basename='jobs')
router.register(r'job-applied', views.JobAppliedViewSet, basename='job_applied')
# router.register(r'industries', views.IndustryViewSet, basename='industries')
router.register(r'levels', views.LevelViewSet, basename='levels')
router.register(r'skills', views.SkillsViewSet, basename='skills')
router.register(r'job-hired', views.JobHiredViewSet, basename='job_hired')
# router.register(r'company', views.CompanyViewSet, basename='company')
router.register(r'users-list', views.UserListViewSet, basename='users_list')
router.register(r'activities', views.ActivitiesViewSet, basename='activities')
# ---------------------------------  perferred lang ----------------------------------- #
router.register(r'preferred-language', views.PrefferedLanguageViewSet, basename='preferred_language')
# ---------------------------------  JOB TASK ----------------------------------- #
router.register(r'job-task', views.JobTasksViewSet, basename='job_task')
#--------------------------------- Job Draft ----------------------------------#
router.register(r'job-draft', views.JobDraftViewSet, basename='job-draft')
#-------------------------------- end ----------------------------------------------#
# ---------------------------------  JOB TEMPLATE ----------------------------------- #
router.register(r'job-template', views.JobTemplatesViewSet, basename='job_template')
router.register(r'company', views.CompanyViewSet, basename='company')
router.register(r'workflows', views.WorkflowViewSet, basename='workflows')
router.register(r'stages', views.StagesViewSet, basename='stages')

urlpatterns = [
    path('edit-profile/', views.ProfileEdit.as_view(), name='edit_profile'),
    path('job-filter/', views.JobFilterApi.as_view(), name='job_filter'),
    path('latest-job/', views.LatestJobAPI.as_view(), name='latest_job'),
    path('related-jobs/<int:company_id>/', views.RelatedJobsAPI.as_view(), name='related_jobs'),
    # ----------------------------- test api url -----------------------------#
    path('test-api/', views.TestApi.as_view(), name='test_api'),

]
urlpatterns += router.urls
