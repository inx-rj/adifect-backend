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

urlpatterns = [
    path('invite-member/', views.InviteMemberApi.as_view(), name='invite_member'),
    path('update-invite-member/<str:id>/<str:status>/<str:exculsive>', views.UpdateInviteMemberStatus.as_view(),
         name='update_invite_member'),
    path('register-view-invite/<str:invite_id>/<str:exculsive>', views.SignUpViewInvite.as_view(),
         name='register_view_invite'),
    path('invite-member-list/', views.InviteMemberUserList.as_view(), name='invite_member_list'),
]
urlpatterns += router.urls
