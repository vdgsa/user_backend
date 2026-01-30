import time
from unittest import mock

from django.contrib.auth.models import Permission
from django.core import mail
from django.test import TestCase
from django.urls.base import reverse
from django.utils import timezone

from vdgsa_backend.accounts.models import (
    ChangeEmailRequest, MembershipSubscription, MembershipType, User
)

from ..selenium_test_base import SeleniumTestCaseBase


class ChangeEmailUITestCase(SeleniumTestCaseBase):
    user: User

    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.create_user(username='steve@stove.com', password='password')
        # Give our user a membership so that we see the full account page
        MembershipSubscription.objects.create(
            owner=self.user,
            valid_until=timezone.now() + timezone.timedelta(hours=500),
            membership_type=MembershipType.regular
        )

    def test_change_email_form_toggle(self) -> None:
        self.login_as(self.user)

        self.assertFalse(self.selenium.find_element_by_id('id_new_email').is_displayed())

        # Show the form
        self.selenium.find_element_by_id('show-change-email-form').click()
        time.sleep(2)  # Wait for bootstrap's animation to finish
        self.assertTrue(self.selenium.find_element_by_id('id_new_email').is_displayed())

        # Hide the form
        self.selenium.find_element_by_id('show-change-email-form').click()
        time.sleep(2)  # Wait for bootstrap's animation to finish
        self.assertFalse(self.selenium.find_element_by_id('id_new_email').is_displayed())

        self.selenium.find_element_by_id('show-change-email-form').click()
        time.sleep(2)  # Wait for bootstrap's animation to finish
        self.assertTrue(self.selenium.find_element_by_id('id_new_email').is_displayed())

        self.selenium.find_element_by_id('change-email-cancel-button').click()
        time.sleep(2)  # Wait for bootstrap's animation to finish
        self.assertFalse(self.selenium.find_element_by_id('id_new_email').is_displayed())

    def test_change_email(self) -> None:
        self.login_as(self.user)

        # Show the form
        self.selenium.find_element_by_id('show-change-email-form').click()

        new_email = 'new_email@email.com'
        self.selenium.find_element_by_id('id_new_email').send_keys(new_email)
        self.selenium.find_element_by_css_selector(
            '#change-email-form button[type=submit]'
        ).click()

        # Go to the username change confirm link from the email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'VdGSA Account - Change Login Email Request')
        change_email_confirm_url = mail.outbox[0].body.split('\n')[-7]
        self.selenium.get(change_email_confirm_url)

        # Redirected to user profile page, check that email was changed
        self.assertEqual(
            self.selenium.find_element_by_id('current-username').get_attribute('value'),
            new_email
        )
        self.user.refresh_from_db()
        self.assertEqual(new_email, self.user.username)
        self.assertEqual(new_email, self.user.email)

    def test_membership_secretary_change_other_user_email(self) -> None:
        # The membership secretary should always see the full page regardless
        # of whether the user has a subscription.
        assert self.user.subscription is not None
        self.user.subscription.delete()

        membership_secretary = User.objects.create_user(
            username='waluigi@time.com', password='password')
        membership_secretary.user_permissions.add(
            Permission.objects.get(codename='membership_secretary'))

        self.login_as(membership_secretary, dest_url=f'/accounts/{self.user.pk}/')

        # Show the form
        self.selenium.find_element_by_id('show-change-email-form').click()

        new_email = 'some_other_email@email.com'
        self.selenium.find_element_by_id('id_new_email').send_keys(new_email)
        self.selenium.find_element_by_css_selector(
            '#change-email-form button[type=submit]'
        ).click()

        # Email change happens immediately
        self.assertEqual(
            self.selenium.find_element_by_id('current-username').get_attribute('value'),
            new_email
        )
        self.user.refresh_from_db()
        self.assertEqual(new_email, self.user.username)
        self.assertEqual(new_email, self.user.email)

    def test_membership_secretary_change_other_user_email_email_already_in_use(self) -> None:
        membership_secretary = User.objects.create_user(
            username='waluigi@time.com', password='password')
        membership_secretary.user_permissions.add(
            Permission.objects.get(codename='membership_secretary'))

        self.login_as(membership_secretary, dest_url=f'/accounts/{self.user.pk}/')

        # Show the form
        self.selenium.find_element_by_id('show-change-email-form').click()

        # Make sure the "email in use" error message isn't shown
        self.assertEqual('', self.selenium.find_element_by_id('email-in-use-msg').text)

        # Try to change self.user's username to one already in use.
        self.selenium.find_element_by_id('id_new_email').send_keys(membership_secretary.username)
        self.selenium.find_element_by_css_selector(
            '#change-email-form button[type=submit]'
        ).click()

        self.assertEqual(
            f'The username "{membership_secretary.username}" is in use by another account.',
            self.selenium.find_element_by_id('email-in-use-msg').text
        )

        # Change to another email, the error message should disappear.
        self.selenium.find_element_by_id('id_new_email').send_keys('emailio@wa.luigi')
        self.selenium.find_element_by_css_selector(
            '#change-email-form button[type=submit]'
        ).click()
        self.assertEqual('', self.selenium.find_element_by_id('email-in-use-msg').text)


class ChangeEmailFormTestCase(TestCase):
    def test_non_membership_secretary_cannot_request_email_change_for_other_user(self) -> None:
        user1 = User.objects.create_user(username='steve@stove.com', password='password')
        user2 = User.objects.create_user(username='stuve@stove.com', password='password')

        self.client.force_login(user1)
        response = self.client.post(
            reverse('change-email-request', kwargs={'pk': user2.pk}),
            {'new_email': 'wee_email@me.me'}
        )
        self.assertEqual(403, response.status_code)

        original_username = user2.username
        user2.refresh_from_db()
        self.assertEqual(original_username, user2.username)

    def test_confirm_change_url_cannot_be_reused(self) -> None:
        original_email = 'original@mail.com'
        new_email = 'new@mail.com'
        user = User.objects.create_user(username=original_email, password='password')
        change_email_request = ChangeEmailRequest.objects.create(user=user, new_email=new_email)

        self.client.force_login(user)
        change_email_url = reverse('change-email-confirm', kwargs={'id': change_email_request.id})
        self.client.get(change_email_url)
        user.refresh_from_db()
        self.assertEqual(new_email, user.username)

        # Set the user's email back to the original, then try to use the change email url again
        user.username = original_email
        user.save()
        response = self.client.get(change_email_url)
        self.assertEqual(404, response.status_code)
        user.refresh_from_db()
        self.assertEqual(original_email, user.username)

    def test_confirm_change_email_expires_after_24_hours(self) -> None:
        yesterday = timezone.now() - timezone.timedelta(hours=24, minutes=1)
        with mock.patch('django.utils.timezone.now', new=lambda: yesterday):
            original_email = 'original@mail.com'
            user = User.objects.create_user(username=original_email, password='password')
            change_email_request = ChangeEmailRequest.objects.create(
                user=user, new_email='new@mail.com'
            )

        self.client.force_login(user)
        change_email_url = reverse('change-email-confirm', kwargs={'id': change_email_request.id})
        response = self.client.get(change_email_url)
        self.assertEqual('This login email change request has expired.', response.content.decode())
        user.refresh_from_db()
        self.assertEqual(original_email, user.username)
