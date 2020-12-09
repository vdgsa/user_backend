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
from django.contrib import admin
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseRedirect
from django.urls import include, path
from rest_framework.authtoken import views


class VdGSALoginView(LoginView):
    success_url_allowed_hosts = {
        'public.vdgsa.org',
        'www.public.vdgsa.org',
        'members.vdgsa.org',
        'www.members.vdgsa.org',
    }


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return HttpResponseRedirect('http://vdgsa.org')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('vdgsa_backend.accounts.urls')),
    path('schema/', include('vdgsa_backend.api_schema.urls')),

    # TODO: remove
    path('token_auth/', views.obtain_auth_token),

    path('login/', VdGSALoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('', include('django.contrib.auth.urls')),
]
