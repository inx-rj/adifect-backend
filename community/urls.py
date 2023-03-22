from django.urls import path

from community.views import StoriesList

urlpatterns = [
    path('stories/', StoriesList.as_view(), name='get_stories'),
]
