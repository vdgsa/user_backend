from typing import Any, Dict, Optional, cast

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms.models import BaseModelForm
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.urls.base import reverse
from django.views.generic.edit import UpdateView

from vdgsa_backend.accounts.models import User
from vdgsa_backend.accounts.views.change_email import ChangeEmailForm
from vdgsa_backend.accounts.views.subscription import PurchaseSubscriptionForm
from vdgsa_backend.accounts.views.utils import get_ajax_form_response

from .permissions import is_requested_user_or_membership_secretary


@login_required
def current_user_profile_view(request: HttpRequest) -> HttpResponse:
    return redirect(reverse('user-profile', kwargs={'pk': request.user.pk}))


class UserProfileView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name']

    template_name = 'user_profile/user_profile.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['edit_profile_form'] = context.pop('form')

        requested_user = cast(User, self.get_object())
        context['change_email_form'] = ChangeEmailForm(requested_user)
        context['change_password_form'] = PasswordChangeForm(requested_user)
        context['membership_renewal_form'] = PurchaseSubscriptionForm(requested_user)

        return context

    def test_func(self) -> Optional[bool]:
        return is_requested_user_or_membership_secretary(
            cast(User, self.get_object()), self.request
        )

    def get_success_url(self) -> str:
        return reverse('user-profile', kwargs={'pk': self.get_object().pk})

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        super().form_valid(form)
        return get_ajax_form_response(form, 200)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        return get_ajax_form_response(form, 400)
