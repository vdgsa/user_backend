from functools import cached_property
from typing import Any, Dict, List

import stripe  # type: ignore
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from django.urls.base import reverse
from django.views.generic.base import View

from vdgsa_backend.accounts.models import (
    MembershipType, PendingMembershipSubscriptionPurchase, User
)
from vdgsa_backend.accounts.views.permissions import is_requested_user_or_membership_secretary
from vdgsa_backend.accounts.views.views import create_or_renew_subscription


class PurchaseSubscriptionForm(forms.Form):
    def __init__(self, user: User, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.user = user

    membership_type = forms.ChoiceField(
        choices=[
            (MembershipType.regular.value, MembershipType.regular.label),
            (MembershipType.student.value, MembershipType.student.label)
        ]
    )
    donation = forms.IntegerField(required=False, min_value=0)


class PurchaseSubscriptionView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
        return self._render_form(PurchaseSubscriptionForm(self.requested_user))

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        form = PurchaseSubscriptionForm(self.requested_user, request.POST)
        if not form.is_valid():
            return self._render_form(form)

        # If the request sender is not the specified user, they must be the membership secretary.
        # In this case we immediately complete the purchase.
        if request.user != self.requested_user:
            create_or_renew_subscription(self.requested_user)
            return redirect(reverse('user-profile', kwargs={'pk': self.requested_user.pk}))

        line_items = self._get_stripe_line_items(form)
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            customer_email=self.requested_user.username,
            success_url=request.build_absolute_uri(
                reverse('user-profile', kwargs={'pk': self.requested_user.pk})),
            cancel_url=request.build_absolute_uri(reverse('stripe-cancel')),
            metadata={'transaction_type': 'membership'}
        )

        PendingMembershipSubscriptionPurchase.objects.create(
            user=self.requested_user,
            stripe_payment_intent_id=session.payment_intent,
        )

        return redirect(reverse('stripe-checkout', kwargs={'stripe_session_id': session.id}))

    def test_func(self) -> bool:
        return is_requested_user_or_membership_secretary(self.requested_user, self.request)

    @cached_property
    def requested_user(self) -> User:
        return User.objects.get(pk=self.kwargs['pk'])

    def _render_form(self, form: PurchaseSubscriptionForm) -> HttpResponse:
        return render(self.request, 'subscription/purchase_subscription.html', {'form': form})

    def _get_stripe_line_items(self, form: PurchaseSubscriptionForm) -> List[Dict[str, object]]:
        membership_type = form.cleaned_data['membership_type']
        if membership_type == MembershipType.student:
            rate = 35  # FIXME: get actual number
            label = '1-year Student Membership'
        elif membership_type == MembershipType.regular:
            rate = 40  # FIXME: get actual number
            label = '1-year Membership'
        else:
            raise ValueError(f'Unexpected membership_type: {membership_type}')

        line_items = [{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': label
                },
                'unit_amount': rate * 100  # Unit is cents
            },
            'quantity': 1,
        }]

        donation = form.cleaned_data['donation']
        if donation:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Donation'
                    },
                    'unit_amount': donation * 100  # Unit is cents
                },
                'quantity': 1,
            })

        return line_items
