from django.urls import path

from . import views

urlpatterns = [
    path('', views.RentalHomeView.as_view(), name='rentals'),

    path('bows/', views.ListBowsView.as_view(), name='list-bows'),
    path('bows/<int:pk>/', views.BowDetailView.as_view(), name='bow-detail'),
    path('bows/add/', views.AddBowView.as_view(), name='add-bow'),

    path('cases/', views.ListCasesView.as_view(), name='list-cases'),
    path('cases/<int:pk>/', views.CaseDetailView.as_view(), name='case-detail'),
    path('cases/add/', views.AddCaseView.as_view(), name='add-case'),

    path('viols/', views.ViolsMultiListView.as_view(), name='list-viols'),
    path('viols/<int:pk>/', views.ViolDetailView.as_view(), name='viol-detail'),
    path('viols/add/', views.AddViolView.as_view(), name='add-viol'),


    path('renters/', views.RentalHomeView.as_view(), name='list-renters'),
    path('waiting/', views.RentalHomeView.as_view(), name='list-waiting'),
]
