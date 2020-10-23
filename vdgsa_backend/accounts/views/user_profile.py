from typing import Optional, cast

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.urls.base import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView

from vdgsa_backend.accounts.models import User

from .permissions import is_requested_user_or_membership_secretary


class UserProfileView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = User
    fields = ['username', 'first_name', 'last_name']

    template_name = 'user_profile/view_user_profile.html'

    def test_func(self) -> Optional[bool]:
        return is_requested_user_or_membership_secretary(
            cast(User, self.get_object()), self.request
        )


@login_required
def current_user_profile_view(request: HttpRequest) -> HttpResponse:
    return redirect(reverse('user-profile', kwargs={'pk': request.user.pk}))


class EditUserProfileView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name']

    template_name = 'user_profile/edit_user_profile.html'

    def test_func(self) -> Optional[bool]:
        return is_requested_user_or_membership_secretary(
            cast(User, self.get_object()), self.request
        )

    def get_success_url(self) -> str:
        return reverse('user-profile', kwargs={'pk': self.get_object().pk})


@login_required
def edit_current_user_profile_view(request: HttpRequest) -> HttpResponse:
    return redirect(reverse('edit-user-profile', kwargs={'pk': request.user.pk}))
