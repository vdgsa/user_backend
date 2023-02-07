"""
Contains views for the membership secretary dashboard (referred to as
"Directory" in the navbar).
"""

import csv
from typing import Any, Dict, Iterable, Literal

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models.query import QuerySet
from django.http.response import HttpResponse
from django.urls.base import reverse
from django.views.generic.base import View
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from vdgsa_backend.accounts.views.permissions import is_membership_secretary
from vdgsa_backend.templatetags.filters import format_datetime_impl

from ..models import User


class AddUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'username',
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
        ]

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

        self.fields['address_line_1'].required = True
        self.fields['address_city'].required = True
        self.fields['address_state'].required = True
        self.fields['address_postal_code'].required = True
        self.fields['address_country'].required = True


class AddUserView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    object: User  # Initialized by CreateView

    form_class = AddUserForm
    template_name = 'membership_secretary/add_user.html'

    def test_func(self) -> bool:
        return is_membership_secretary(self.request.user)

    def get_success_url(self) -> str:
        return reverse('user-account', kwargs={'pk': self.object.pk})


def _filter_active_users(queryset: QuerySet[User]) -> Iterable[User]:
    queryset = queryset.exclude(is_deceased=True)
    return filter(lambda membership: membership.subscription_is_current, queryset)


class MembershipSecretaryView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'membership_secretary/membership_secretary.html'
    context_object_name = 'users'

    # https://github.com/typeddjango/django-stubs/issues/477
    def get_queryset(self) -> Iterable[User]:  # type: ignore
        # Optimization: Load all related MembershipSubscription objects
        # in a single query instead of one query per user.
        queryset = super().get_queryset().select_related(
            'subscription_is_family_member_for', 'owned_subscription')

        return queryset if self.all_users else _filter_active_users(queryset)

    @property
    def all_users(self) -> bool:
        return self.request.GET.get('all_users', 'false').lower() == 'true'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['all_users'] = self.all_users
        return context

    def test_func(self) -> bool:
        return (is_membership_secretary(self.request.user)
                or self.request.user.has_perm('accounts.board_member'))


class AllUsersSpreadsheetView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
        user_query: QuerySet[User] = User.objects.all().select_related(
            'subscription_is_family_member_for', 'owned_subscription')
        if self.request.GET.get('all_users', 'false').lower() != 'true':
            users = _filter_active_users(user_query)
        else:
            users = user_query

        field_names = [
            'Database ID',
            'Last Name',
            'First Name',
            'Email',
            'Membership Type',
            'Membership Expires',
            'Membership is Current',
            'Primary Membership Email',
            'Is Primary Membership Holder',
            'Year Joined',
            'Years Renewed',

            'Address Line 1',
            'Address Line 2',
            'City',
            'State',
            'ZIP',
            'Country',
            'Phone 1',
            'Phone 2',

            'Is Young Player',
            'Is Teacher',
            'Is Remote Teacher',
            'Teacher Description',
            'Is Instrument Maker',
            'Is Bow Maker',
            'Is Repairer',
            'Is Publisher',
            'Other Commercial',
            'Educational Institution Affiliation',

            'Is Deceased',
            'Receives Expiration Reminder Emails',
            'Notes',

            'Do Not Email',
            'Include Name in Membership Directory',
            'Include Email in Membership Directory',
            'Include Address in Membership Directory',
            'Include Phone in Membership Directory',
            'Last Modified',
        ]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="vdgsa_users.csv"'

        writer = csv.DictWriter(response, fieldnames=field_names)
        writer.writeheader()
        for user in users:
            writer.writerow({
                'Database ID': user.pk,
                'Last Name': user.last_name,
                'First Name': user.first_name,
                'Email': user.username,
                'Membership Type': (
                    user.subscription.membership_type if user.subscription is not None else ''),
                'Membership Expires': self._get_membership_expiration(user),
                'Membership is Current': self._format_bool(user.subscription_is_current),
                'Primary Membership Email': (
                    user.subscription.owner.username if user.subscription is not None else ''),
                'Is Primary Membership Holder': self._format_bool(
                    user.is_primary_membership_holder
                ),
                'Year Joined': (
                    user.subscription.years_renewed[0] if user.subscription is not None else ''),
                'Years Renewed': (
                    ','.join([str(year) for year in user.subscription.years_renewed[1:]])
                    if user.subscription is not None else ''
                ),

                'Address Line 1': user.address_line_1,
                'Address Line 2': user.address_line_2,
                'City': user.address_city,
                'State': user.address_state,
                'ZIP': user.address_postal_code,
                'Country': user.address_country,

                'Phone 1': user.phone1,
                'Phone 2': user.phone2,

                'Is Young Player': self._format_bool(user.is_young_player),
                'Is Teacher': self._format_bool(user.is_teacher),
                'Is Remote Teacher': self._format_bool(user.is_remote_teacher),
                'Teacher Description': user.teacher_description,
                'Is Instrument Maker': self._format_bool(user.is_instrument_maker),
                'Is Bow Maker': self._format_bool(user.is_bow_maker),
                'Is Repairer': self._format_bool(user.is_repairer),
                'Is Publisher': self._format_bool(user.is_publisher),
                'Other Commercial': user.other_commercial,
                'Educational Institution Affiliation': user.educational_institution_affiliation,

                'Is Deceased': user.is_deceased,
                'Receives Expiration Reminder Emails': user.receives_expiration_reminder_emails,
                'Notes': user.notes,

                'Do Not Email': user.do_not_email,
                'Include Name in Membership Directory': self._format_bool(
                    user.include_name_in_membership_directory),
                'Include Email in Membership Directory': self._format_bool(
                    user.include_email_in_membership_directory),
                'Include Address in Membership Directory': self._format_bool(
                    user.include_address_in_membership_directory),
                'Include Phone in Membership Directory': self._format_bool(
                    user.include_phone_in_membership_directory),
                'Last Modified': user.last_modified,
            })

        return response

    def test_func(self) -> bool:
        return is_membership_secretary(self.request.user)

    def _get_membership_expiration(self, user: User) -> str:
        if user.subscription is None:
            return ''

        return format_datetime_impl(user.subscription.valid_until, none_ok=True)

    def _format_bool(self, val: bool) -> Literal['TRUE', 'FALSE']:
        return 'TRUE' if val else 'FALSE'
