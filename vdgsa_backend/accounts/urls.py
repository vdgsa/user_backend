from django.shortcuts import redirect
from django.urls import path
from django.urls.base import reverse
from django.urls.conf import re_path

from . import views

# user_router = routers.DefaultRouter()
# user_router.register(r'users', views.ListUserViewSet)
# user_router.register(r'users', views.RetrieveUpdateUserViewSet)

urlpatterns = [
    path('users/current/', views.CurrentUserView.as_view(), name='current-user'),

    path('register/', views.UserRegistrationView.as_view(), name='user-registration'),
    path('change_email/<int:pk>/', views.ChangeEmailRequestView.as_view(),
         name='change-email-request'),
    path('change_email/', views.change_current_user_email_request,
         name='change-current-user-email'),
    path('change_email_confirm/<id>/', views.change_email_confirm, name='change-email-confirm'),

    path('profile/<int:pk>/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/', views.current_user_profile_view, name='current-user-profile'),

    path('user/<int:pk>/subscription/add_family_member/', views.AddFamilyMemberView.as_view(),
         name='add-family-member'),
    path('user/<int:pk>/subscription/remove_family_member/',
         views.RemoveFamilyMemberView.as_view(),
         name='remove-family-member'),
    path('user/<int:pk>/subscription/', views.PurchaseSubscriptionView.as_view(),
         name='purchase-subscription'),

    path('membership_secretary/all_users_csv/', views.AllUsersSpreadsheetView.as_view(),
         name='all-users-csv'),
    path('membership_secretary/', views.MembershipSecretaryView.as_view(),
         name='membership-secretary'),

    path('stripe_webhook/', views.stripe_webhook_view),

    # re_path('$', lambda request: redirect(reverse('current-user-profile'))),
]
