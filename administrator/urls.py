from django.urls import path
# from .views import ProfileEdit, JobFilterApi, LatestJobAPI
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='categories')
router.register(r'jobs', views.JobViewSet, basename='jobs')
router.register(r'job-applied', views.JobAppliedViewSet, basename='job_applied')
router.register(r'industries', views.IndustryViewSet, basename='industries')
router.register(r'levels', views.LevelViewSet, basename='levels')
router.register(r'skills', views.SkillsViewSet, basename='skills')
router.register(r'job-hired', views.JobHiredViewSet, basename='job_hired')
router.register(r'company', views.CompanyViewSet, basename='company')
router.register(r'users-list', views.UserListViewSet, basename='users_list')
router.register(r'activities', views.ActivitiesViewSet, basename='activities')
# ---------------------------------  perferred lang ----------------------------------- #
router.register(r'preferred-language', views.PrefferedLanguageViewSet, basename='preferred_language')

urlpatterns = [
    path('edit-profile/', views.ProfileEdit.as_view(), name='edit_profile'),
    path('job-filter/', views.JobFilterApi.as_view(), name='job_filter'),
    path('latest-job/', views.LatestJobAPI.as_view(), name='latest_job'),
    path('related-jobs/<str:title>', views.RelatedJobsAPI.as_view(), name='related_jobs'),
    # ----------------------------- test api url -----------------------------#
    path('test-api/', views.TestApi.as_view(), name='test_api'),

]
urlpatterns += router.urls
