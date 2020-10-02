from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)

urlpatterns = [
    path('users/current/', views.CurrentUserView.as_view()),
    path('users/<username>/membership_subscription/',
         views.MembershipSubscriptionView.as_view()),
    path('users/<username>/subscription_history/',
         views.MembershipSubscriptionHistoryView.as_view()),
    path('', include(router.urls)),

    path('register/', views.UserRegistrationView.as_view(),
         name='register'),
]
