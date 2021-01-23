from django.urls import path

from . import views

urlpatterns = [
    path('bows/add/', views.AddBowView.as_view(), name='add-bow'),
]
