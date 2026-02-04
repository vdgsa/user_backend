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
from django.contrib.auth.views import LoginView
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import include, path
from django.urls.base import reverse
from django.urls.conf import re_path


class VdGSALoginView(LoginView):
    success_url_allowed_hosts = {
        'public.vdgsa.org',
        'www.public.vdgsa.org',
        'members.vdgsa.org',
        'www.members.vdgsa.org',
    }


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

    path('login/', VdGSALoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('', include('django.contrib.auth.urls')),

    re_path('^$', lambda request: redirect(reverse('current-user-account'))),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
