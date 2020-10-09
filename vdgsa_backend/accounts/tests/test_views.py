from unittest.case import skip

from django.contrib.auth import authenticate
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from vdgsa_backend.accounts.models import User
from vdgsa_backend.accounts.serializers import UserSerializer


class UserViewTestCase(TestCase):
    membership_secretary: User
    user: User

    client: APIClient

    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()
        self.membership_secretary = User.objects.create_user(username='batman@batman.com')
        self.membership_secretary.user_permissions.add(
            Permission.objects.get(codename='membership_secretary')
        )
        self.user = User.objects.create_user(username='waa@luigi.com')

    def test_user_registration(self) -> None:
        username = 'an_user@gmail.com'
        password = 'norsevnoireatoienartfoieanor'
        response = self.client.post(
            reverse('register'), {'username': username, 'password': password}
        )
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        assert response.data is not None
        self.assertIn('token', response.data)

        loaded_user = Token.objects.get(key=response.data['token']).user
        self.assertEqual(loaded_user, authenticate(username=username, password=password))

    def test_bad_request_user_registration_request_params_missing(self) -> None:
        response = self.client.post(reverse('register'), {'username': 'spam@spam.com'})
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        response = self.client.post(reverse('register'), {'password': 'norisetanroieatonr'})
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_bad_request_user_registration_username_exists(self) -> None:
        response = self.client.post(
            reverse('register'),
            {'username': self.user.username, 'password': 'norisetanroieatonr'}
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_membership_secretary_list_users(self) -> None:
        self.client.force_authenticate(self.membership_secretary)
        response = self.client.get(reverse('user-list'))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        assert response.data is not None
        self.assertCountEqual(
            UserSerializer([self.membership_secretary, self.user], many=True).data,
            response.data['results']
        )

    def test_permission_denied_list_users(self) -> None:
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('user-list'))
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_user_get_self(self) -> None:
        self.client.force_authenticate(self.user)
        response = self.client.get(
            reverse('user-detail', kwargs={'username': self.user.username})
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(UserSerializer(self.user).data, response.data)

    def test_membership_secretary_get_user(self) -> None:
        self.client.force_authenticate(self.membership_secretary)
        response = self.client.get(
            reverse('user-detail', kwargs={'username': self.user.username})
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(UserSerializer(self.user).data, response.data)

    def test_permission_denied_user_get_other(self) -> None:
        self.client.force_authenticate(self.user)
        response = self.client.get(
            reverse('user-detail', kwargs={'username': self.membership_secretary.username})
        )
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_user_update_self(self) -> None:
        new_data = {
            'first_name': 'WAAAAAA',
            'last_name': 'Luigi'
        }
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            reverse('user-detail', kwargs={'username': self.user.username}),
            data=new_data
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        assert response.data is not None
        self.assertEqual(new_data['first_name'], response.data['first_name'])
        self.assertEqual(new_data['last_name'], response.data['last_name'])

        self.user.refresh_from_db()
        self.assertEqual(UserSerializer(self.user).data, response.data)

    def test_membership_secretary_update_user(self) -> None:
        new_data = {
            'first_name': 'Bat',
            'last_name': 'Man'
        }
        self.client.force_authenticate(self.membership_secretary)
        response = self.client.patch(
            reverse('user-detail', kwargs={'username': self.user.username}),
            data=new_data
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        assert response.data is not None
        self.assertEqual(new_data['first_name'], response.data['first_name'])
        self.assertEqual(new_data['last_name'], response.data['last_name'])

        self.user.refresh_from_db()
        self.assertEqual(UserSerializer(self.user).data, response.data)

    def test_permission_denied_user_update_other(self) -> None:
        original_first_name = self.membership_secretary.first_name
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            reverse('user-detail', kwargs={'username': self.membership_secretary.username}),
            {'first_name': 'norfkvbonirufav'}
        )
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        self.membership_secretary.refresh_from_db()
        self.assertEqual(original_first_name, self.membership_secretary.first_name)

    def test_cannot_change_username_in_patch_user_endpoint(self) -> None:
        original_username = self.user.username
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            reverse('user-detail', kwargs={'username': self.user.username}),
            data={'username': 'nrst@nrst.org'}
        )
        # DRF's default behavior is to ignore read-only fields
        # https://github.com/encode/django-rest-framework/issues/1655
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        self.user.refresh_from_db()
        self.assertEqual(original_username, self.user.username)

    @skip('Not implemented')
    def test_user_change_username_self(self) -> None:
        self.fail()

    def test_membership_secretary_change_other_username(self) -> None:
        new_username = 'new_username@username.org'
        self.client.force_authenticate(self.membership_secretary)
        response = self.client.put(
            reverse('change-username', kwargs={'username': self.user.username}),
            data={'username': 'new_username@username.org'}
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        assert response.data is not None
        self.assertEqual(new_username, response.data['username'])

        self.user.refresh_from_db()
        self.assertEqual(new_username, self.user.username)

    def test_permission_denied_user_change_other_username(self) -> None:
        original_username = self.membership_secretary.username
        self.client.force_authenticate(self.user)
        response = self.client.put(
            reverse('change-username', kwargs={'username': self.membership_secretary.username}),
            data={'username': 'new@username.org'}
        )
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        self.membership_secretary.refresh_from_db()
        self.assertEqual(original_username, self.membership_secretary.username)


class MembershipSubscriptionViewTestCase(TestCase):
    def test_user_get_self_subscription_as_owner(self) -> None:
        self.fail()

    def test_user_get_self_subscription_as_family(self) -> None:
        self.fail()

    def test_membership_secretary_get_user_subscription(self) -> None:
        self.fail()

    def test_permission_denied_user_get_other_subscription(self) -> None:
        self.fail()

    # Note that this endpoint doesn't differentiate between purchasing
    # and renewing a subscription.
    def test_user_purchase_regular_subscription(self) -> None:
        self.fail()

    def test_user_purchase_student_subscription(self) -> None:
        self.fail()

    def test_permission_denied_user_purchase_for_other_user(self) -> None:
        self.fail()

    def test_membership_secretary_purchase_regular_subscription_for_user(self) -> None:
        self.fail()

    def test_membership_secretary_purchase_student_subscription_for_user(self) -> None:
        self.fail()

    def test_bad_request_purchase_subscription_for_lifetime_member(self) -> None:
        self.fail()

    def test_bad_request_purchase_lifetime_membership(self) -> None:
        self.fail()

    def test_bad_request_membership_type_not_included(self) -> None:
        self.fail()

    def test_purchase_subscription_with_donation(self) -> None:
        self.fail()

    def test_donation_amout_decimal_truncated(self) -> None:
        self.fail()

    def test_donation_zero_ignored(self) -> None:
        self.fail()

    def test_bad_request_donation_not_number(self) -> None:
        self.fail()

    def test_bad_request_donation_negative(self) -> None:
        self.fail()


class StripeWebhookViewTestCase(TestCase):
    def test_membership_payment_intent_succeeded(self) -> None:
        self.fail()

    def test_non_membership_payment_intent_succeeded_ignored(self) -> None:
        self.fail()

    def test_other_event_ignored(self) -> None:
        self.fail()
