from django.urls import path

from . import views

urlpatterns = [
    path('send_officer_emails/', views.stripe_officer_email_view),
]
