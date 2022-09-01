from django.urls import path

from . import views

urlpatterns = [
    path('view/', views.Viewemails.as_view(), name='view-expire-emails'),
]
