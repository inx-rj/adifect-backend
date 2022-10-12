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

# router.register(r'QA', views.QAViewSet, basename='QA')
router.register(r'question', views.QuestionViewSet, basename='question')
router.register(r'question-oldest-first', views.OldestFirstQuestionViewSet, basename='oldest_first_question')

router.register(r'answer', views.AnswerViewSet, basename='answer')
router.register(r'user-skills', views.UserSkillsViewSet, basename='user_skills')

#----------------------------------- ADMIN SECTION ---------------------------------#
router.register(r'agency-list', views.AgencyListViewSet, basename='agency_list')
router.register(r'agency-job-list', views.AgencyJobListViewSet, basename='agency_job_list')
router.register(r'agency-workflow-list', views.AgencyWorkflowViewSet, basename='agency_workflow_list')
router.register(r'agency-company-list', views.AgencyCompanyListViewSet, basename='agency_company_list')
router.register(r'agency-invited-list', views.AgencyInviteListViewSet, basename='agency_invite_list')
#-------------------------------------  END  ---------------------------------------------#

urlpatterns = [
    path('edit-profile/', views.ProfileEdit.as_view(), name='edit_profile'),
    path('job-filter/', views.JobFilterApi.as_view(), name='job_filter'),
    path('latest-job/', views.LatestJobAPI.as_view(), name='latest_job'),
    path('related-jobs/<int:company_id>/', views.RelatedJobsAPI.as_view(), name='related_jobs'),
    path('job-status-update/<int:Job_id>/<int:status>/', views.JobStatusUpdate.as_view(), name='job_status_update'),
    # ----------------------------- test api url -----------------------------#
    path('test-api/', views.TestApi.as_view(), name='test_api'),
    path('job-proposal/<int:pk>/', views.JobProposal.as_view(), name='jobs_proposal'),
    path('proposal-unseen-count/<int:pk>/', views.ProposalUnseenCount.as_view(), name='proposal_unseen_count'),
    path('question-filter/', views.QuestionFilterAPI.as_view(), name='question_filter'),
    path('job-share-details/', views.JobShareDetails.as_view(), name='job_share_details'),
]
urlpatterns += router.urls
