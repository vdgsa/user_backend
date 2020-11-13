from functools import cached_property
from typing import Any, Optional, cast

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.db import transaction
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic.base import View

from vdgsa_backend.accounts.models import ChangeEmailRequest, User
from vdgsa_backend.accounts.views.permissions import is_requested_user_or_membership_secretary
from vdgsa_backend.accounts.views.utils import get_ajax_form_response


class ChangeEmailForm(forms.ModelForm):
    class Meta:
        model = ChangeEmailRequest
        fields = ['new_email']

    def __init__(self, requested_user: User, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.user = requested_user

    def save(self, commit: bool = True) -> ChangeEmailRequest:
        # Automatically use the requested user as the "user" field
        # for the ChangeEmailRequest object.
        instance = cast(ChangeEmailRequest, super().save(commit=False))
        instance.user = self.user
        if commit:
            instance.save()
        return instance


class ChangeEmailRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        form = ChangeEmailForm(self.requested_user, request.POST)

        if not form.is_valid():
            return get_ajax_form_response(form, 400)

        # If the requester is the membership secretary, then complete the
        # email change immediately and redirect to the user profile page.
        if self.request.user.has_perm('accounts.membership_secretary'):
            self.requested_user.username = form.cleaned_data['new_email']
            self.requested_user.save()
            return HttpResponse(self.requested_user.username)

        change_request = form.save()
        send_mail(
            subject='VdGSA Account - Change Login Email Request',
            from_email='webmaster@vdgsa.org',
            recipient_list=[change_request.new_email],
            message=f'''
You have requested that your VdGSA login email be changed from
{self.requested_user.username} to {change_request.new_email}.
Please visit this page to complete the change:

{request.META['HTTP_HOST']}{reverse('change-email-confirm', kwargs={'id': change_request.id})}

This link will expire in 24 hours.

Sincerely,
The VdGSA Web Team
''',
        )

        return render(
            request,
            'change_email/change_email_pending.tmpl',
            status=202,
            context={'new_email': change_request.new_email}
        )

    def test_func(self) -> Optional[bool]:
        return is_requested_user_or_membership_secretary(self.requested_user, self.request)

    @cached_property
    def requested_user(self) -> User:
        return get_object_or_404(User, pk=self.kwargs['pk'])


def change_email_confirm(request: HttpRequest, id: str) -> HttpResponse:
    change_request = get_object_or_404(ChangeEmailRequest, id=id)
    if timezone.now() - change_request.created_at > timezone.timedelta(days=1):
        return HttpResponse('This login email change request has expired.')

    with transaction.atomic():
        # Do NOT use .update() here, since we need .save() to be called
        # on the user object.
        user = change_request.user
        user.username = change_request.new_email
        user.save()
        change_request.delete()

    return redirect(reverse('current-user-profile'))


@login_required
def change_current_user_email_request(request: HttpRequest) -> HttpResponse:
    return redirect(reverse('change-email-request', kwargs={'pk': request.user.pk}))
