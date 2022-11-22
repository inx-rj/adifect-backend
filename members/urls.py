from django.urls import path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'member-approver-job-list', views.MemberApprovedJobViewSet, basename='member_approver_job_list')
router.register(r'job-activity-member', views.JobActivityMemberViewSet, basename='job_activity_member')
router.register(r'member-job-list', views.MemberJobListViewSet, basename='member_job_list')
router.register(r'member-approval-job-list', views.MemberApprovalJobListViewSet, basename='member_approval_job_list')
router.register(r'invited-user-company-list', views.InviteUserCompanyListViewSet, basename='member_approval_job_list')

urlpatterns = [

]
urlpatterns += router.urls