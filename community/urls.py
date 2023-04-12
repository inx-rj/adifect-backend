from django.urls import path

from community.views import StoriesList, CommunityTagsListCreate, CommunityList, CommunitySettingsView

urlpatterns = [
    path('stories/', StoriesList.as_view(), name='get_stories'),
    path('tags/', CommunityTagsListCreate.as_view(), name='get_create_community_tags'),
    path('list-community-status-tag-data/', CommunityList.as_view(), name='list_community_status_tag'),
    path('community-setting/', CommunitySettingsView.as_view(), name='community_setting'),
    # path('list-status/', StatusList.as_view(), name='list_status'),
    # path('list-tag/', TagList.as_view(), name='list_tag')
]
