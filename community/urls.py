from django.urls import path

from community.views import StoriesList, CommunityTagsListCreate, CommunityList, CommunitySettingsView, \
    ChannelListCreateAPIView, ChannelRetrieveUpdateDestroyAPIView

urlpatterns = [
    path('stories/', StoriesList.as_view(), name='list_stories'),
    path('stories/<int:id>/', StoriesList.as_view(), name='get_story'),
    path('tags/', CommunityTagsListCreate.as_view(), name='get_create_community_tags'),
    path('list-community-status-tag-data/', CommunityList.as_view(), name='list_community_status_tag'),
    path('community-setting/<int:id>/', CommunitySettingsView.as_view(),
         name='retrieve_delete_update_community_setting'),
    path('community-setting/', CommunitySettingsView.as_view(), name='community_setting'),
    # path('list-status/', StatusList.as_view(), name='list_status'),
    # path('list-tag/', TagList.as_view(), name='list_tag'),
    path('channel/', ChannelListCreateAPIView.as_view(), name='list_create_channel'),
    path('channel/<int:id>/', ChannelRetrieveUpdateDestroyAPIView.as_view(), name='retrieve_update_destroy_channel'),
]
