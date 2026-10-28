"""vdgsa_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import logout
from django.contrib.auth.forms import AuthenticationForm
import django.contrib.auth.views as django_views
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import include, path
from django.urls.base import reverse
from django.urls.conf import re_path


class VDGSALoginForm(AuthenticationForm):
    def clean_username(self):
        username = self.cleaned_data.get('username')
        return username.lower() if username is not None else username


# LOWERCASE THE USERNAME/EMAIL
# Figure out which method to override to convert the
# email address to lowercase
class VdGSALoginView(django_views.LoginView):
    form_class = VDGSALoginForm

    success_url_allowed_hosts = {
        'public.vdgsa.org',
        'www.public.vdgsa.org',
        'members.vdgsa.org',
        'www.members.vdgsa.org',
    }


class VdGSAPasswordResetForm(django_views.PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        return email.lower() if email is not None else email


class VdGSAPasswordResetView(django_views.PasswordResetView):
    form_class = VdGSAPasswordResetForm


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return HttpResponseRedirect('http://public.vdgsa.org')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('vdgsa_backend.accounts.urls')),
    path('conclave/', include('vdgsa_backend.conclave_registration.urls')),
    path('schema/', include('vdgsa_backend.api_schema.urls')),
    path('rentals/', include('vdgsa_backend.rental_viols.urls')),
    path('directory/', include('vdgsa_backend.directory.urls')),
    path('emails/', include('vdgsa_backend.emails.urls')),
    path('swp/', include('vdgsa_backend.stripe_wix_proxy.urls')),
    path('stripe_emails/', include('vdgsa_backend.stripe_email_webhook.urls')),

    # URLs below taken from django.contrib.auth.urls
    # We extend several of Django's built-in auth views
    # to make usernames case-insensitive (i.e., always lowercase)
    path('login/', VdGSALoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),

    path('password_change/', django_views.PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', django_views.PasswordChangeDoneView.as_view(), name='password_change_done'),

    path('password_reset/', VdGSAPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', django_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', django_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', django_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    re_path('^$', lambda request: redirect(reverse('current-user-account'))),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
