"""
Contains views and forms used for editing the user's profile
information. This form is in the "Profile" section of the user account
page.
"""

from typing import Any, Dict, Final, Optional, Sequence, cast

from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import BaseModelForm, ModelForm, Textarea, Select
from django.http.response import HttpResponse
from django.urls.base import reverse
from django.utils.functional import cached_property
from django.views.generic.edit import UpdateView

from vdgsa_backend.accounts.models import User
from vdgsa_backend.accounts.views.permissions import (
    is_membership_secretary, is_requested_user_or_membership_secretary
)
from vdgsa_backend.accounts.views.utils import get_ajax_form_response, LocationAddress


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
            'educational_institution_affiliation',
            'website',
            'is_remote_teacher',
            'is_instrument_maker',
            'is_bow_maker',
            'is_repairer',
            'is_publisher',
            'other_commercial',
            'commercial_description',

            'do_not_email',

            'include_name_in_membership_directory',
            'include_email_in_membership_directory',
            'include_address_in_membership_directory',
            'include_phone_in_membership_directory',

            # MEMBERSHIP SECRETARY ONLY
            'is_deceased',
            'receives_expiration_reminder_emails',
            'notes',
        ]

        widgets = {
            'teacher_description': Textarea(attrs={'rows': 5, 'cols': None}),
            'notes': Textarea(attrs={'rows': 5, 'cols': None}),
            'address_state': Select(),
            'address_country': Select(),
        }

    def __init__(self, *args: Any, authorized_user: User, **kwargs: Any):
        data = kwargs.pop('data', None)

        if data is not None and not is_membership_secretary(authorized_user):
            data = data.copy()
            for field in self._membership_secretary_only_fields:
                if field in data:
                    data.pop(field)

        super().__init__(data, *args, **kwargs)
        self.authorized_user = authorized_user

        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

        self.fields['address_line_1'].required = True
        self.fields['address_city'].required = True
        self.fields['address_postal_code'].required = True
        self.fields['address_country'].required = True

        if self.instance.address_country in LocationAddress.COUNTRY_SUBDIVISION_WHITELIST:
            self.fields['address_state'].widget.choices = [('', 'Select State/Province')]+[(c.code.split('-')[1], c.name)
            for c in LocationAddress.getSubdivisions(self.instance.address_country)]
        else:
            self.fields['address_state'].widget.choices = [('', 'N/A - No Subdivisions')]
        
        self.fields['address_country'].widget.choices = [
            (c.name, c.name) for c in LocationAddress.getCountries()]
    
    def clean(self):
        # Example cross-field validation
        cleaned_data = super().clean()
        address_state_data = cleaned_data.get('address_state')
        address_country_data = cleaned_data.get('address_country')

        if address_country_data in LocationAddress.COUNTRY_SUBDIVISION_WHITELIST\
            and (not address_state_data or address_state_data == ''):
            raise ValidationError("Please select a valid state/province for the selected country.")
        return cleaned_data
    
    _membership_secretary_only_fields: Final[Sequence[str]] = [
        'is_deceased',
        'receives_expiration_reminder_emails',
        'notes',
    ]


class UserProfileView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = UserProfileForm

    template_name = 'user_account/user_profile_form.tmpl'

    @cached_property
    def requested_user(self) -> User:
        return cast(User, self.get_object())

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs['authorized_user'] = self.request.user
        return kwargs

    def test_func(self) -> Optional[bool]:
        return is_requested_user_or_membership_secretary(
            self.requested_user, self.request
        )

    def get_success_url(self) -> str:
        # Django requires us to override this method, but we expect this
        # view to only be used in AJAX requests.
        return reverse('user-account', kwargs={'pk': self.requested_user.pk})

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        print('form valid',form.errors)
        super().form_valid(form)
        return get_ajax_form_response(
            'success',
            form,
            form_template=self.template_name,
            form_context=self.get_context_data()
        )

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        print('form invalid',form.errors)
        return get_ajax_form_response(
            'form_validation_error',
            form,
            form_template=self.template_name,
            form_context=self.get_context_data()
        )
