from django.urls import path
from django.urls.conf import re_path

from . import views

urlpatterns = [
    path('', views.DirectoryHomeView.as_view(), name='directory'),
    path('clear', views.DirectoryHomeView.as_view(), name='clearDirectory')
    
]
