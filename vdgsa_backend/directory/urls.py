from django.urls import path
from django.urls.conf import re_path

from . import views

urlpatterns = [
    path('', views.DirectoryHomeView.as_view(), name='directory'),
    path('', views.DirectoryHomeView.as_view(), name='clearDirectory'),
    path('detail/<int:pk>', views.DirectoryMemberDetailView.as_view(), name='member-detail'),
]
