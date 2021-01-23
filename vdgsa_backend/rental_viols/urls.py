from django.urls import path

from . import views

urlpatterns = [
    path('bows/', views.ListBowsView.as_view(), name='list-bows'),
    path('bows/<int:pk>/', views.BowDetailView.as_view(), name='bow-detail'),
    path('bows/add/', views.AddBowView.as_view(), name='add-bow'),
]
