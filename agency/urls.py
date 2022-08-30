from django.urls import path
from rest_framework import routers
from .import views
  
router = routers.DefaultRouter()

router.register(r'agency-jobs', views.AgencyJobsViewSet, basename='agency-jobs')
router.register(r'get-agency-unapplied-jobs', views.GetAgencyUnappliedJobs, basename='get_agency_unapplied_jobs')
router.register(r'stages', views.StagesViewSet, basename='stages')
router.register(r'levels', views.WorkFlowLevelsViewSet, basename='workflow-levels')
router.register(r'workflow', views.WorkFlowViewSet, basename='workflow')

urlpatterns = [
    # path('job-hired/', views.JobHiredApi.as_view(), name='job_hired'),
    # path('workflow/', views.WorkFlowLevelsViewSet.as_view({'get': 'list'}), name='workflow'),
    path('invite-member/', views.InviteMemberApi.as_view(), name='invite_member'),
    path('update-invite-member/<str:id>/<str:status>/<str:exculsive>', views.UpdateInviteMemberStatus.as_view(), name='update_invite_member'),
    path('register-view-invite/<str:invite_id>/<str:exculsive>', views.SignUpViewInvite.as_view(), name='register_view_invite'),
    path('invite-member-list/', views.InviteMemberUserList.as_view(), name='invite_member_list'),
]
urlpatterns += router.urls