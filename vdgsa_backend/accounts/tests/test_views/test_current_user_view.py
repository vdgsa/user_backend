import json
from unittest.case import skip

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls.base import reverse
from django.utils import timezone

from vdgsa_backend.accounts.models import MembershipSubscription, MembershipType, User


class CurrentUserViewTestCase(TestCase):
    membership_secretary: User
    user: User

    def setUp(self) -> None:
        super().setUp()
        self.membership_secretary = User.objects.create_user(username='batman@batman.com')
        self.membership_secretary.user_permissions.add(
            Permission.objects.get(codename='membership_secretary')
        )
        self.user = User.objects.create_user(username='waa@luigi.com')
        self.subscription = MembershipSubscription.objects.create(
            owner=self.user,
            membership_type=MembershipType.regular,
            # Set valid_until to time in past
            valid_until=timezone.now()
        )

        self.family = User.objects.create_user(
            username='llama@llama.net',
            subscription_is_family_member_for=self.subscription
        )

        self.url = reverse('current-user')

    def test_get_current_user_with_subscription(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content.decode())

        expected_fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'subscription',
            'subscription_is_current',
            'last_modified',
        ]
        self.assertCountEqual(expected_fields, data.keys())

        expected_subscription_fields = [
            'id',
            'owner',
            'family_members',
            'valid_until',
            'membership_type',
        ]
        self.assertCountEqual(expected_subscription_fields, data['subscription'].keys())

        expected_owner_data = {'id': self.user.id, 'username': self.user.username}
        self.assertEqual(expected_owner_data, data['subscription']['owner'])

        expected_family_data = [{'id': self.family.id, 'username': self.family.username}]
        self.assertEqual(expected_family_data, data['subscription']['family_members'])

    def test_get_current_user_not_authenticated(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(401, response.status_code)

    def test_get_current_user_no_subscription(self) -> None:
        self.family.delete()
        self.subscription.delete()

        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content.decode())
        self.assertIsNone(data['subscription'])
        self.assertFalse(data['subscription_is_current'])


@skip('Hard to test, figure out later')
class StripeWebhookViewTestCase(TestCase):
    def test_membership_payment_intent_succeeded(self) -> None:
        self.fail()

    def test_non_membership_payment_intent_succeeded_ignored(self) -> None:
        self.fail()

    def test_other_event_ignored(self) -> None:
        self.fail()
