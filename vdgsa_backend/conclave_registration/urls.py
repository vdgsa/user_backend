from django.urls import path
from django.urls.conf import re_path

from . import views

urlpatterns = [
    path('admin/create/', views.CreateConclaveRegistrationConfigView.as_view(),
         name='create-conclave'),
    path('admin/<int:pk>/settings/', views.EditConclaveRegistrationConfigView.as_view(),
         name='edit-conclave'),
    path('admin/<int:conclave_config_pk>/add_class/', views.CreateConclaveClassView.as_view(),
         name='create-class'),
    path('admin/<int:pk>/', views.ConclaveRegistrationConfigView.as_view(),
         name='conclave-detail'),
    path('admin/', views.ListConclaveRegistrationConfigView.as_view(), name='list-conclaves'),
    path('class/<int:pk>/', views.EditConclaveClassView.as_view(), name='edit-class'),
    path('class/<int:pk>/delete/', views.DeleteConclaveClassView.as_view(), name='delete-class'),

    path('register/<int:conclave_reg_pk>/basic_info/', views.BasicInfoView.as_view(),
         name='conclave-basic-info'),
    path('register/<int:conclave_reg_pk>/work_study/', views.WorkStudyApplicationView.as_view(),
         name='conclave-work-study'),
    path('register/<int:conclave_reg_pk>/instruments/', views.InstrumentsBringingView.as_view(),
         name='conclave-instruments-bringing'),
    path('register/instruments/<int:pk>/', views.DeleteInstrumentView.as_view(),
         name='delete-instrument'),
    path('register/<int:conclave_reg_pk>/classes/',
         views.RegularProgramClassSelectionView.as_view(),
         name='conclave-class-selection'),
    path('register/<int:conclave_reg_pk>/housing/', lambda _: _, name='conclave-housing'),
    path('register/<int:conclave_reg_pk>/tshirts/', views.TShirtsView.as_view(),
         name='conclave-tshirts'),
    path('register/<int:conclave_reg_pk>/payment/', views.PaymentView.as_view(),
         name='conclave-payment'),
    path('register/<int:conclave_reg_pk>/done/', views.RegistrationDoneView.as_view(),
         name='conclave-done'),

    path('<int:conclave_config_pk>/register/', views.ConclaveRegistrationLandingPage.as_view(),
         name='conclave-reg-landing'),

    # redirect registration for current year
    # (only show link in navbar if there's an open registration)
    # re_path('^$', views., lambda _: _, name='conclave-reg-landing-current-user'),
]
