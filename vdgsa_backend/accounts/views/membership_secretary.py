import csv
from typing import Any, Literal

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http.response import HttpResponse
from django.views.generic.base import View
from django.views.generic.list import ListView

from vdgsa_backend.accounts.templatetags.filters import format_datetime_impl
from vdgsa_backend.accounts.views.permissions import is_membership_secretary

from ..models import User


class MembershipSecretaryView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'membership_secretary.html'

    def test_func(self) -> bool:
        return is_membership_secretary(self.request.user)


class AllUsersSpreadsheetView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
        users = User.objects.all()
        field_names = [
            'Database ID',
            'Last Name',
            'First Name',
            'Email',
            'Membership Type',
            'Membership Expires',
            'Membership is Current',

            'Address',
            'Phone 1',
            'Phone 2',

            'Is Young Player',
            'Is Teacher',
            'Is Remote Teacher',
            'Teacher Description',
            'Is Builder',
            'Is Publisher',
            'Other Commercial',
            'Educational Institution Affiliation',

            'Do Not Email',
            'Include Name in Membership Directory',
            'Include Email in Membership Directory',
            'Include Address in Membership Directory',
            'Include Phone in Membership Directory',
            'Include Name in Mailing List',
            'Include Email in Mailing List',
            'Include Address in Mailing List',
            'Include Phone in Mailing List',
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

                'Address': self._format_address(user),
                'Phone 1': user.phone1,
                'Phone 2': user.phone2,

                'Is Young Player': self._format_bool(user.is_young_player),
                'Is Teacher': self._format_bool(user.is_teacher),
                'Is Remote Teacher': self._format_bool(user.is_remote_teacher),
                'Teacher Description': user.teacher_description,
                'Is Builder': self._format_bool(user.is_builder),
                'Is Publisher': self._format_bool(user.is_publisher),
                'Other Commercial': user.other_commercial,
                'Educational Institution Affiliation': user.educational_institution_affiliation,

                'Do Not Email': user.do_not_email,
                'Include Name in Membership Directory': self._format_bool(
                    user.include_name_in_membership_directory),
                'Include Email in Membership Directory': self._format_bool(
                    user.include_email_in_membership_directory),
                'Include Address in Membership Directory': self._format_bool(
                    user.include_address_in_membership_directory),
                'Include Phone in Membership Directory': self._format_bool(
                    user.include_phone_in_membership_directory),
                'Include Name in Mailing List': self._format_bool(
                    user.include_name_in_mailing_list),
                'Include Email in Mailing List': self._format_bool(
                    user.include_email_in_mailing_list),
                'Include Address in Mailing List': self._format_bool(
                    user.include_address_in_mailing_list),
                'Include Phone in Mailing List': self._format_bool(
                    user.include_phone_in_mailing_list),
                'Last Modified': user.last_modified,
            })

        return response

    def test_func(self) -> bool:
        return is_membership_secretary(self.request.user)

    def _get_membership_expiration(self, user: User) -> str:
        if user.subscription is None:
            return ''

        return format_datetime_impl(user.subscription.valid_until, none_ok=True)

    def _format_address(self, user: User) -> str:
        return (
            f'{user.address_line_1} {user.address_line_2}, '
            f'{user.address_city}, {user.address_state} {user.address_postal_code} '
            f'{user.address_country}'
        )

    def _format_bool(self, val: bool) -> Literal['TRUE', 'FALSE']:
        return 'TRUE' if val else 'FALSE'
