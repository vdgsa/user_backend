from typing import Any, Dict, Optional, cast

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import BaseModelForm, ModelForm, Textarea
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.urls.base import reverse
from django.utils.functional import cached_property
from django.views.generic.edit import UpdateView

from vdgsa_backend.accounts.models import User
from vdgsa_backend.accounts.views.change_email import ChangeEmailForm
from vdgsa_backend.accounts.views.subscription import AddFamilyMemberForm, PurchaseSubscriptionForm
from vdgsa_backend.accounts.views.utils import get_ajax_form_response

from .permissions import is_requested_user_or_membership_secretary


@login_required
def current_user_profile_view(request: HttpRequest) -> HttpResponse:
    return redirect(reverse('user-profile', kwargs={'pk': request.user.pk}))


class UserProfileForm(ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',

            'address_line_1',
            'address_line_2',
            'address_city',
            'address_state',
            'address_postal_code',
            'address_country',
            'phone1',
            'phone2',

            'is_young_player',
            'is_teacher',
            'teacher_description',
            'is_remote_teacher',
            'is_builder',
            'is_publisher',
            'other_commercial',
            'educational_institution_affiliation',

            'do_not_email',

            'include_name_in_membership_directory',
            'include_email_in_membership_directory',
            'include_address_in_membership_directory',
            'include_phone_in_membership_directory',

            'include_name_in_mailing_list',
            'include_email_in_mailing_list',
            'include_address_in_mailing_list',
            'include_phone_in_mailing_list',
        ]

        widgets = {
            'teacher_description': Textarea(attrs={'rows': 4}),
        }


class UserProfileView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = UserProfileForm

    template_name = 'user_profile/user_profile.html'

    @cached_property
    def requested_user(self) -> User:
        return cast(User, self.get_object())

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['edit_profile_form'] = context.pop('form')

        context['change_email_form'] = ChangeEmailForm(self.requested_user)
        context['change_password_form'] = PasswordChangeForm(self.requested_user)
        context['membership_renewal_form'] = PurchaseSubscriptionForm(self.requested_user)
        context['add_family_member_form'] = AddFamilyMemberForm()

        context['current_authenticated_user'] = self.request.user

        return context

    def test_func(self) -> Optional[bool]:
        return is_requested_user_or_membership_secretary(
            self.requested_user, self.request
        )

    def get_success_url(self) -> str:
        return reverse('user-profile', kwargs={'pk': self.requested_user.pk})

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
