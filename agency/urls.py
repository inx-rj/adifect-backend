from django.urls import path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'industries', views.IndustryViewSet, basename='industries')
router.register(r'company', views.CompanyViewSet, basename='company')
router.register(r'agency-jobs', views.AgencyJobsViewSet, basename='agency-jobs')
router.register(r'get-agency-unapplied-jobs', views.GetAgencyUnappliedJobs, basename='get_agency_unapplied_jobs')
router.register(r'works-flow', views.WorksFlowViewSet, basename='works_flow')
router.register(r'works-flow-stages', views.StageViewSet, basename='works_flow_stages')
router.register(r'dam', views.DAMViewSet, basename='dam')
router.register(r'dam-root', views.DamRootViewSet, basename='dam_root')
router.register(r'dam-media', views.DamMediaViewSet, basename='dam_media')
router.register(r'dam-duplicate', views.DamDuplicateViewSet, basename='dam_duplicate')
router.register(r'draft-jobs', views.DraftJobViewSet, basename='draft_jobs')
router.register(r'test-api', views.TestModalViewSet, basename='test_api')
router.register(r'invite-member',views.InviteMemberViewSet, basename='invite_member')
router.register(r'my-project',views.MyProjectViewSet, basename='my_project')
router.register(r'dam-filter', views.DamMediaFilterViewSet, basename='dam_filter')
router.register(r'job-activity-member', views.JobActivityMemberViewSet, basename='job_activity_member')
router.register(r'dam-media-filter', views.DAMFilter, basename='dam_filter')
router.register(r'inhouse-user-list', views.InHouseMemberViewset, basename='inhouse_user_list')
router.register(r'job-feedback', views.JobFeedbackViewset, basename='job_feedback')






urlpatterns = [
    path('update-invite-member/<str:id>/<str:status>/<str:exculsive>', views.UpdateInviteMemberStatus.as_view(),
         name='update_invite_member'),
    path('register-view-invite/<str:invite_id>/<str:exculsive>', views.SignUpViewInvite.as_view(),
       name='register_view_invite'),
    # path('invite-member-list/<int:company_id>/', views.InviteMemberUserList.as_view(), name='invite_member_list'),
    path('invite-member-list/', views.InviteMemberUserList.as_view(), name='invite_member_list'),
    path('share-media-link/', views.ShareMediaUrl.as_view(), name='share_media_link'),
    path('job-attachments/', views.JobAttachmentsView.as_view(), name='job_attachments'),
    path('member-nudge-reminder/', views.NudgeReminder.as_view(), name='member_nudge_reminder'),
    path('company-media-count/', views.CompanyImageCount.as_view(), name='company_media_count'),
]
urlpatterns += router.urls
