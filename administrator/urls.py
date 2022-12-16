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
# router.register(r'job-hired', views.JobHiredViewSet, basename='job_hired')
# router.register(r'company', views.CompanyViewSet, basename='company')
router.register(r'users-list', views.UserListViewSet, basename='users_list')
# router.register(r'activities', views.ActivitiesViewSet, basename='activities')
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
router.register(r'job-activity', views.JobActivityViewSet, basename='job_activity')
router.register(r'admin-job-activity', views.AdminJobActivityViewSet, basename='admin_job_activity')

#----------------------------------- ADMIN SECTION ---------------------------------#
router.register(r'agency-list', views.AgencyListViewSet, basename='agency_list')
router.register(r'agency-job-list', views.AgencyJobListViewSet, basename='agency_job_list')
router.register(r'agency-workflow-list', views.AgencyWorkflowViewSet, basename='agency_workflow_list')
router.register(r'agency-company-list', views.AgencyCompanyListViewSet, basename='agency_company_list')
router.register(r'agency-invited-list', views.AgencyInviteListViewSet, basename='agency_invite_list')
router.register(r'creator-list', views.CreatorListViewSet, basename='creator_list')
router.register(r'creator-job-list', views.CreatorJobListViewSet, basename='creator_job_list')
router.register(r'user-portfolio', views.UserPortfolioViewset, basename='user_portfolio')
router.register(r'agency-job-details', views.AgencyJobDetailsViewSet, basename='agency_job_details')
router.register(r'submit-job-work', views.JobWorkSubmitViewSet, basename='submit_job_work')
router.register(r'member-work-approval', views.MemberApprovalViewSet, basename='member_work_approval')
router.register(r'completed-job', views.JobCompletedViewSet, basename='completed_job')
router.register(r'super-admin-dam', views.SuperAdminDAMViewSet, basename='super_admin_dam')
router.register(r'super-admin-dam-root', views.DamRootViewSet, basename='super_admin_dam_root')
router.register(r'super-admin-dam-media', views.DamMediaViewSet, basename='super_admin_dam_media')
router.register(r'super-admin-dam-filter', views.DamMediaFilterViewSet, basename='super_admin_dam_filter')
router.register(r'super-admin-dam-duplicate', views.DamDuplicateViewSet, basename='dam_duplicate')
router.register(r'super-admin-dam-media-filter', views.DAMFilter, basename='super_admin_dam_media_filter')



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
    path('job-block/', views.JobBlock.as_view(), name='job_block'),
    path('admin-company-block/', views.AdminCompanyBlock.as_view(), name='admin_company_block'),
    path('job-work-status/', views.JobWorkStatus.as_view(), name='job_work_status'),
    path('job-completed-status/', views.JobCompletedStatus.as_view(), name='job_completed_status'),
    path('job-activity-users/<int:job_id>/', views.JobActivityUserList.as_view(), name='job_activity_users'),
    path('admin-job-attachments/', views.AdminJobAttachmentsView.as_view(), name='admin_job_attachments'),
    path('admin-question-filter/', views.AdminQuestionFilterAPI.as_view(), name='admin_question_filter'),
    path('super-admin-company-media-count/', views.CompanyImageCount.as_view(), name='company_media_count'),
    path('super-admin-share-media-link/', views.ShareMediaUrl.as_view(), name='share_media_link'),



]
urlpatterns += router.urls
