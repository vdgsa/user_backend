from vdgsa_backend.accounts.views import ChangeUsernameView
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from . import views

user_router = routers.DefaultRouter()
user_router.register(r'users', views.ListUserViewSet)
user_router.register(r'users', views.RetrieveUpdateUserViewSet)

urlpatterns = [
    path('users/current/', views.CurrentUserView.as_view()),
    path('users/<username>/membership_subscription/',
         views.MembershipSubscriptionView.as_view()),
    path('users/<username>/subscription_history/',
         views.MembershipSubscriptionHistoryView.as_view()),
    # This must go before including the user_router urls
    path('users/<username>/username/',
         views.ChangeUsernameView.as_view(),
         name='change-username'),
    path('', include(user_router.urls)),

    path('register/', views.UserRegistrationView.as_view(),
         name='register'),
]
