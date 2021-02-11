from django.urls import path
from django.urls.conf import re_path

from . import views

urlpatterns = [
    path('users/current/', views.CurrentUserView.as_view(), name='current-user'),

    path('register/', views.UserRegistrationView.as_view(), name='user-registration'),
    path('change_email/<int:pk>/', views.ChangeEmailRequestView.as_view(),
         name='change-email-request'),
    path('change_email/', views.change_current_user_email_request,
         name='change-current-user-email'),
    path('change_email_confirm/<id>/', views.change_email_confirm, name='change-email-confirm'),

    path('profile/<int:pk>/', views.UserProfileView.as_view(), name='user-profile'),

    path('subscription/<int:pk>/add_family_member/', views.AddFamilyMemberView.as_view(),
         name='add-family-member'),
    path('subscription/<int:pk>/remove_family_member/',
         views.RemoveFamilyMemberView.as_view(),
         name='remove-family-member'),
    path('user/<int:pk>/purchase_subscription/', views.PurchaseSubscriptionView.as_view(),
         name='purchase-subscription'),

    path('directory/csv/', views.AllUsersSpreadsheetView.as_view(),
         name='all-users-csv'),
    path('directory/', views.MembershipSecretaryView.as_view(),
         name='membership-secretary'),

    path('stripe_webhook/', views.stripe_webhook_view),

    path('<int:pk>/', views.UserAccountView.as_view(), name='user-account'),
    re_path('^$', views.current_user_account_view, name='current-user-account'),
]
