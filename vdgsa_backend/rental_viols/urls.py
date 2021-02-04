from django.urls import path

from . import views

urlpatterns = [
    path('', views.RentalHomeView.as_view(), name='rentals'),

    path('bows/', views.ListBowsView.as_view(), name='list-bows'),
    path('bows/add/', views.AddBowView.as_view(), name='add-bow'),
    path('bows/<int:pk>/', views.BowDetailView.as_view(), name='bow-detail'),
    path('bow/<int:pk>/', views.UpdateBowView.as_view(), name='bow-update'),

    path('cases/', views.ListCasesView.as_view(), name='list-cases'),
    path('cases/add/', views.AddCaseView.as_view(), name='add-case'),
    path('cases/<int:pk>/', views.CaseDetailView.as_view(), name='case-detail'),
    path('case/<int:pk>/', views.UpdateCaseView.as_view(), name='case-update'),

    path('viols/', views.ViolsMultiListView.as_view(), name='list-viols'),
    path('viols/add/', views.AddViolView.as_view(), name='add-viol'),
    path('viols/<int:pk>/', views.ViolDetailView.as_view(), name='viol-detail'),
    path('viol/<int:pk>/', views.UpdateViolView.as_view(), name='viol-update'),

    path('renters/', views.RentalHomeView.as_view(), name='list-renters'),
    path('waiting/', views.RentalHomeView.as_view(), name='list-waiting'),
]
