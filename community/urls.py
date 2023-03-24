from django.urls import path

from community.views import StoriesList, CommunityTagsList

urlpatterns = [
    path('stories/', StoriesList.as_view(), name='get_stories'),
    path('tags/', CommunityTagsList.as_view(), name='get_community_tags'),
]
