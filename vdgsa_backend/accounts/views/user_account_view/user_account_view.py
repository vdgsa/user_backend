"""
Contains the top-level view for the "My Account" page.
"""
from typing import Any, Dict, Optional, cast
from datetime import date
from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import BaseModelForm
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.urls.base import reverse
from django.utils.functional import cached_property
from django.views.generic.edit import UpdateView

from vdgsa_backend.accounts.models import User
from vdgsa_backend.accounts.views.permissions import is_requested_user_or_membership_secretary
from vdgsa_backend.accounts.views.utils import get_ajax_form_response

from .change_email import ChangeEmailForm
from .membership_renewal import AddFamilyMemberForm, PurchaseSubscriptionForm
from .user_profile import UserProfileForm


@login_required
def current_user_account_view(request: HttpRequest) -> HttpResponse:
    return redirect(reverse('user-account', kwargs={'pk': request.user.pk}))



class UserAccountView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = UserProfileForm

    template_name = 'user_account/user_account.html'

    @cached_property
    def requested_user(self) -> User:
        return cast(User, self.get_object())

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs['authorized_user'] = self.requested_user
        return kwargs

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['MAX_NUM_FAMILY_MEMBERS'] = settings.MAX_NUM_FAMILY_MEMBERS

        context['edit_profile_form'] = UserProfileForm(
            authorized_user=cast(User, self.request.user),
            instance=self.requested_user
        )
        context['change_email_form'] = ChangeEmailForm(self.requested_user)
        context['change_password_form'] = PasswordChangeForm(self.requested_user)
        context['membership_renewal_form'] = PurchaseSubscriptionForm(
            requested_user=self.requested_user,
            authenticated_user=cast(User, self.request.user)
        )
        context['add_family_member_form'] = AddFamilyMemberForm()
        context['can_renew_membership'] = self.can_renew_membership()
        print('can_renew_membership',context['can_renew_membership'] )

        return context
    
    def can_renew_membership(self) -> Optional[bool]:
        return not self.requested_user.subscription or self.requested_user.subscription.membership_type == 'lifetime' or ( date.today() > self.requested_user.subscription.valid_until.date() - relativedelta(months=6))

    def test_func(self) -> Optional[bool]:
        return is_requested_user_or_membership_secretary(
            self.requested_user, self.request
        )

    def get_success_url(self) -> str:
        return reverse('user-account', kwargs={'pk': self.requested_user.pk})

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        super().form_valid(form)
        return get_ajax_form_response(
            'success',
            form,
            form_template=self.template_name,
            form_context=self.get_context_data()
        )

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        return get_ajax_form_response(
            'form_validation_error',
            form,
            form_template=self.template_name,
            form_context=self.get_context_data()
        )
