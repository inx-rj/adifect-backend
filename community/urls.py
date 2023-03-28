from django.urls import path

from community.views import StoriesList, CommunityTagsListCreate, CommunityList

urlpatterns = [
    path('list-community-status-tag-data/', CommunityList.as_view(), name='list_community_status_tag'),
    path('stories/', StoriesList.as_view(), name='get_stories'),
    path('tags/', CommunityTagsListCreate.as_view(), name='get_create_community_tags'),
]
