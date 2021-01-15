import csv
from typing import Any

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
    ordering = ['last_name', 'first_name', 'username']

    def test_func(self) -> bool:
        return is_membership_secretary(self.request.user)


class AllUsersSpreadsheetView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
        users = User.objects.all()
        field_names = [
            'Database ID',
            'Last Name',
            'First Name',
            'Username',
            'Membership Type',
            'Membership Expires'
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
                'Username': user.username,
                'Membership Type': (
                    user.subscription.membership_type if user.subscription is not None else ''),
                'Membership Expires': self._get_membership_expiration(user),
            })

        return response

    def _get_membership_expiration(self, user: User) -> str:
        if user.subscription is None:
            return ''

        return format_datetime_impl(user.subscription.valid_until, none_ok=True)

    def test_func(self) -> bool:
        return is_membership_secretary(self.request.user)
