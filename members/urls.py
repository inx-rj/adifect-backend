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

urlpatterns = [
        path('members-invite-member-list/', views.MemberInviteMemberUserList.as_view(), name='invite_member_list'),
]
urlpatterns += router.urls