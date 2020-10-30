from vdgsa_backend.accounts.views.views import StripeWebhookView
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views

# user_router = routers.DefaultRouter()
# user_router.register(r'users', views.ListUserViewSet)
# user_router.register(r'users', views.RetrieveUpdateUserViewSet)

urlpatterns = [
    # path('login/', LoginView.as_view(), name='login'),
    # path('logout/', LogoutView.as_view(), name='logout'),

    path('users/current/', views.CurrentUserView.as_view()),
    # path('users/<username>/membership_subscription/',
    #      views.MembershipSubscriptionView.as_view()),
    # path('users/<username>/subscription_history/',
    #      views.MembershipSubscriptionHistoryView.as_view()),
    # # This must go before including the user_router urls
    # path('users/<username>/username/',
    #      views.ChangeUsernameView.as_view(),
    #      name='change-username'),
    # path('', include(user_router.urls)),

    path('register/', views.UserRegistrationView.as_view(), name='user-registration'),
    path('change_email/<int:pk>/', views.ChangeEmailRequestView.as_view(),
         name='change-email-request'),
    path('change_email/', views.change_current_user_email_request,
         name='change-current-user-email'),
    path('change_email_confirm/<id>/', views.change_email_confirm, name='change-email-confirm'),

    path('profile/<int:pk>/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/', views.current_user_profile_view, name='current-user-profile'),

    path('edit_profile/<int:pk>/', views.EditUserProfileView.as_view(), name='edit-user-profile'),
    path('edit_profile/', views.edit_current_user_profile_view, name='edit-current-user-profile'),

    path('user/<int:pk>/subscription/', views.PurchaseSubscriptionView.as_view(),
         name='purchase-subscription'),

    path('stripe_webhook/', views.StripeWebhookView.as_view()),
    path('stripe_checkout/<stripe_session_id>/', views.stripe_checkout_view,
         name='stripe-checkout'),
    path('stripe_cancel/', views.stripe_cancel_view,
         name='stripe-cancel'),
]
