from django.urls import path

from . import views

urlpatterns = [
    path('', views.StripeWixProxyView.as_view(), name='stripe-wix-proxy'),

]
