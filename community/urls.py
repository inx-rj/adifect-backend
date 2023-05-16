from django.urls import path

from community.views import StoriesList, CommunityTagsListCreate, CommunityList, CommunitySettingsView, \
    ChannelListCreateAPIView, ChannelRetrieveUpdateDestroyAPIView, ProgramRetrieveUpdateDestroyAPIView, \
    ProgramListCreateAPIView, CopyCodeListCreateAPIView, CopyCodeRetrieveUpdateDestroyAPIView, \
    CreativeCodeListCreateAPIView, CreativeCodeRetrieveUpdateDestroyAPIView, ExportArticleCsv, AddStoryTagsView, \
    OpnSesameViewSet

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
    path('program/', ProgramListCreateAPIView.as_view(), name='list_create_program'),
    path('program/<int:id>/', ProgramRetrieveUpdateDestroyAPIView.as_view(), name='retrieve_update_destroy_program'),
    path('copy-code/', CopyCodeListCreateAPIView.as_view(), name='list_create_copy_code'),
    path('copy-code/<int:id>/', CopyCodeRetrieveUpdateDestroyAPIView.as_view(),
         name='retrieve_update_destroy_copy_code'),
    path('creative-code/', CreativeCodeListCreateAPIView.as_view(), name='list_create_creative_code'),
    path('creative-code/<int:id>/', CreativeCodeRetrieveUpdateDestroyAPIView.as_view(),
         name='retrieve_update_destroy_creative_code'),
    path('story-export/', ExportArticleCsv.as_view(), name="story_export"),
    path('story-tag/', AddStoryTagsView.as_view(), name="story_tag"),
    path('open-sesame-auth/', OpnSesameViewSet.as_view(), name="open_sesame_auth"),
]
