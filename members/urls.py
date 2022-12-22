from django.urls import path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'member-approver-job-list', views.MemberApprovedJobViewSet, basename='member_approver_job_list')
router.register(r'job-activity-member', views.JobActivityMemberViewSet, basename='job_activity_member')
router.register(r'member-job-list', views.MemberJobListViewSet, basename='member_job_list')
router.register(r'member-approval-job-list', views.MemberApprovalJobListViewSet, basename='member_approval_job_list')
router.register(r'invited-user-company-list', views.InviteUserCompanyListViewSet, basename='member_approval_job_list')
router.register(r'member-marketer-job', views.MemberMarketerJobViewSet, basename='member_marketer_job')
router.register(r'company', views.CompanyViewSet, basename='company')
router.register(r'workflow', views.WorksFlowViewSet, basename='workflow')
router.register(r'admin-workflow-stages', views.MemberStageViewSet, basename='admin-workflow-stages')
router.register(r'admin-my-project', views.MemberMyProjectViewSet, basename='admin_my_project')
router.register(r'invite-member', views.InviteMemberViewSet, basename='invite_member')
router.register(r'member-jobs', views.JobViewSet, basename='member_jobs')
router.register(r'members-job-template', views.MemberJobTemplatesViewSet, basename='job_template')
router.register(r'members-draft-jobs', views.DraftJobViewSet, basename='draft_jobs')
router.register(r'member-dam', views.MemberDAMViewSet, basename='member_dam')
router.register(r'member-dam-root', views.MemberDamRootViewSet, basename='dam_root')
router.register(r'member-dam-media', views.MemberDamMediaViewSet, basename='member_dam_media')
router.register(r'member-dam-duplicate', views.MemberDamDuplicateViewSet, basename='member_dam_duplicate')
router.register(r'member-dam-media-filter', views.MemberDAMFilter, basename='member_dam_media_filter')
router.register(r'member-dam-filter', views.MemberDamMediaFilterViewSet, basename='member_dam_filter')
router.register(r'job-house-member', views.JobHouseMember, basename='job_house_member')
router.register(r'member-notification', views.MemberNotificationViewset, basename='member_notification')

urlpatterns = [
        path('members-invite-member-list/', views.MemberInviteMemberUserList.as_view(), name='invite_member_list'),
        path('job-attachments/', views.JobAttachmentsView.as_view(), name='job_attachments'),
        path('company-media-count/', views.CompanyImageCount.as_view(), name='company_media_count'),
        path('company-count/', views.CompanyCountView.as_view(), name='company_count'),
]
urlpatterns += router.urls