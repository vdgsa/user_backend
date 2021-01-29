import json
import time

from django.core import mail
from django.test import TestCase
from django.urls.base import reverse
from django.utils import timezone
from selenium.common.exceptions import NoSuchElementException  # type: ignore
from selenium.webdriver.support import expected_conditions as EC  # type: ignore
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore

from vdgsa_backend.accounts.models import MembershipSubscription, MembershipType, User
from vdgsa_backend.accounts.templatetags.filters import format_datetime_impl
from vdgsa_backend.accounts.tests.test_views.selenium_test_base import SeleniumTestCaseBase
from vdgsa_backend.accounts.views.subscription import MAX_NUM_FAMILY_MEMBERS


class MembershipUITestCase(SeleniumTestCaseBase):
    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.create_user(username='steve@stove.com', password='password')

    def test_purchase_regular_subscription(self) -> None:
        self.login_as(self.user)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element_by_id('login-info-wrapper')

        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element_by_id('user-profile-form')

        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element_by_id('family-members-wrapper')

        self.assertIn(
            'Pay For Your Membership',
            self.selenium.find_element_by_id('membership-header').text
        )

        self.selenium.find_element_by_css_selector(
            '#purchase-subscription-form button[type=submit]'
        ).click()

        wait = WebDriverWait(self.selenium, 5)
        wait.until(
            lambda driver: driver.find_element_by_id('ProductSummary-totalAmount').text != '')
        self.assertIn(
            '$35.00',
            self.selenium.find_element_by_id('ProductSummary-totalAmount').text
        )
        self.assertIn('checkout.stripe.com', self.selenium.current_url)

        # TODO: Figure out a good way to integration test the stripe webhook

    def test_purchase_student_subscription(self) -> None:
        self.login_as(self.user)

        self.selenium.find_element_by_id('id_membership_type').click()
        self.selenium.find_elements_by_css_selector('#id_membership_type option')[1].click()

        self.selenium.find_element_by_css_selector(
            '#purchase-subscription-form button[type=submit]'
        ).click()

        wait = WebDriverWait(self.selenium, 5)
        wait.until(
            lambda driver: driver.find_element_by_id('ProductSummary-totalAmount').text != '')
        self.assertIn(
            '$20.00',
            self.selenium.find_element_by_id('ProductSummary-totalAmount').text
        )
        self.assertIn('checkout.stripe.com', self.selenium.current_url)

    def test_purchase_international_subscription(self) -> None:
        self.login_as(self.user)

        self.selenium.find_element_by_id('id_membership_type').click()
        self.selenium.find_elements_by_css_selector('#id_membership_type option')[2].click()

        self.selenium.find_element_by_css_selector(
            '#purchase-subscription-form button[type=submit]'
        ).click()

        wait = WebDriverWait(self.selenium, 5)
        wait.until(
            lambda driver: driver.find_element_by_id('ProductSummary-totalAmount').text != '')
        self.assertIn(
            '$40.00',
            self.selenium.find_element_by_id('ProductSummary-totalAmount').text
        )
        self.assertIn('checkout.stripe.com', self.selenium.current_url)

    def test_purchase_student_subscription_with_donation(self) -> None:
        self.login_as(self.user)

        self.selenium.find_element_by_id('id_membership_type').click()
        self.selenium.find_elements_by_css_selector('#id_membership_type option')[1].click()

        self.selenium.find_element_by_id('id_donation').send_keys('25')
        self.selenium.find_element_by_css_selector(
            '#purchase-subscription-form button[type=submit]'
        ).click()

        wait = WebDriverWait(self.selenium, 5)
        wait.until(
            lambda driver: driver.find_element_by_id('ProductSummary-totalAmount').text != '')
        self.assertIn(
            '$45.00',
            self.selenium.find_element_by_id('ProductSummary-totalAmount').text
        )
        self.assertIn('checkout.stripe.com', self.selenium.current_url)

    def test_renew_subscription(self) -> None:
        valid_until = timezone.now() + timezone.timedelta(days=1)
        MembershipSubscription.objects.create(
            owner=self.user, valid_until=valid_until, membership_type=MembershipType.regular)

        self.login_as(self.user)
        # Make sure that these sections exist
        self.selenium.find_element_by_id('login-info-wrapper')
        self.selenium.find_element_by_id('user-profile-form')

        self.assertEqual(
            format_datetime_impl(valid_until),
            self.selenium.find_element_by_id('valid-until-timestamp').text
        )
        self.assertIn(
            'Your membership is valid until',
            self.selenium.find_element_by_id('membership-status-msg').text
        )
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element_by_id('family-member-msg')

        self.assertIn('Renew', self.selenium.find_element_by_id('show-membership-purchase').text)
        self.selenium.find_element_by_id('show-membership-purchase').click()

        self.selenium.find_element_by_css_selector(
            '#purchase-subscription-form button[type=submit]'
        ).click()

        wait = WebDriverWait(self.selenium, 5)
        wait.until(
            lambda driver: driver.find_element_by_id('ProductSummary-totalAmount').text != '')
        self.assertIn(
            '$35.00',
            self.selenium.find_element_by_id('ProductSummary-totalAmount').text
        )
        self.assertIn('checkout.stripe.com', self.selenium.current_url)

        # TODO: Figure out a good way to integration test the stripe webhook

    def test_renew_membership_form_toggle(self) -> None:
        valid_until = timezone.now() + timezone.timedelta(days=1)
        MembershipSubscription.objects.create(
            owner=self.user, valid_until=valid_until, membership_type=MembershipType.regular)

        self.login_as(self.user)
        self.assertFalse(
            self.selenium.find_element_by_id('purchase-subscription-form').is_displayed())

        self.selenium.find_element_by_id('show-membership-purchase').click()
        time.sleep(2)  # Wait for bootstrap's animation to finish
        self.assertTrue(
            self.selenium.find_element_by_id('purchase-subscription-form').is_displayed())

        self.selenium.find_element_by_id('show-membership-purchase').click()
        time.sleep(2)  # Wait for bootstrap's animation to finish
        self.assertFalse(
            self.selenium.find_element_by_id('purchase-subscription-form').is_displayed())

        self.selenium.find_element_by_id('show-membership-purchase').click()
        time.sleep(2)  # Wait for bootstrap's animation to finish
        self.assertTrue(
            self.selenium.find_element_by_id('purchase-subscription-form').is_displayed())

        self.selenium.find_element_by_id('hide-purchase-subscription').click()
        time.sleep(2)  # Wait for bootstrap's animation to finish
        self.assertFalse(
            self.selenium.find_element_by_id('purchase-subscription-form').is_displayed())

        # TODO: Figure out a good way to integration test the stripe webhook

    def test_subscription_expired_message(self) -> None:
        valid_until = timezone.now() - timezone.timedelta(days=1)
        MembershipSubscription.objects.create(
            owner=self.user, valid_until=valid_until, membership_type=MembershipType.regular)

        self.login_as(self.user)
        self.assertEqual(
            format_datetime_impl(valid_until),
            self.selenium.find_element_by_id('valid-until-timestamp').text
        )

        self.assertIn('expired', self.selenium.find_element_by_id('membership-status-msg').text)

    def test_lifetime_member_message(self) -> None:
        MembershipSubscription.objects.create(
            owner=self.user, valid_until=None, membership_type=MembershipType.lifetime)

        self.login_as(self.user)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element_by_id('valid-until-timestamp')

        self.assertIn('forever', self.selenium.find_element_by_id('membership-status-msg').text)

    def test_family_member_message(self) -> None:
        owner = User.objects.create_user(
            username='subscription_owner@me.me',
            first_name='Waa',
            last_name='Luigi'
        )
        valid_until = timezone.now() + timezone.timedelta(days=4)
        subscription = MembershipSubscription.objects.create(
            owner=owner, valid_until=valid_until, membership_type=MembershipType.regular)
        self.user.subscription_is_family_member_for = subscription
        self.user.save()

        self.login_as(self.user)
        self.assertEqual(
            format_datetime_impl(valid_until),
            self.selenium.find_element_by_id('valid-until-timestamp').text
        )
        self.assertIn(
            'Your membership is valid until',
            self.selenium.find_element_by_id('membership-status-msg').text
        )

        self.assertEqual(
            f"You are a family member on Waa Luigi's membership.",
            self.selenium.find_element_by_id('family-member-msg').text
        )

        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element_by_id('family-members-wrapper')

        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element_by_id('show-membership-purchase')

    def test_membership_secretary_purchase_and_renew_subscription_for_other_user(self) -> None:
        membership_secretary = self.make_membership_secretary()
        self.login_as(membership_secretary, f'/accounts/profile/{self.user.pk}/')
        # When the membership secretary purchases a membership, it skips the Stripe flow.
        self.selenium.find_element_by_css_selector(
            '#purchase-subscription-form button[type=submit]'
        ).click()

        subscription = MembershipSubscription.objects.get(owner=self.user)
        self.assertEqual(
            format_datetime_impl(subscription.valid_until),
            self.selenium.find_element_by_id('valid-until-timestamp').text
        )
        assert subscription.valid_until is not None
        old_valid_until = subscription.valid_until

        # Renew the membership
        self.assertIn('Renew', self.selenium.find_element_by_id('show-membership-purchase').text)
        self.selenium.find_element_by_id('show-membership-purchase').click()

        self.selenium.find_element_by_css_selector(
            '#purchase-subscription-form button[type=submit]'
        ).click()
        subscription.refresh_from_db()
        self.assertEqual(1, subscription.valid_until.year - old_valid_until.year)
        self.assertEqual(
            format_datetime_impl(subscription.valid_until),
            self.selenium.find_element_by_id('valid-until-timestamp').text
        )

        # Renew the membership again (make sure the csrf token gets rotated)
        # Also renewing as student to make sure form fields were re-rendered
        self.selenium.find_element_by_id('show-membership-purchase').click()

        self.selenium.find_element_by_id('id_membership_type').click()
        self.selenium.find_elements_by_css_selector('#id_membership_type option')[1].click()

        self.selenium.find_element_by_css_selector(
            '#purchase-subscription-form button[type=submit]'
        ).click()
        subscription.refresh_from_db()
        self.assertEqual(2, subscription.valid_until.year - old_valid_until.year)
        self.assertEqual(
            format_datetime_impl(subscription.valid_until),
            self.selenium.find_element_by_id('valid-until-timestamp').text
        )

    def test_add_remove_family_members(self) -> None:
        MembershipSubscription.objects.create(
            owner=self.user, valid_until=timezone.now(), membership_type=MembershipType.regular)

        # One user that doesn't exist, one that does.
        family1_username = 'family1@wat.com'
        family2 = User.objects.create_user(username='family2@wat.com')

        self.login_as(self.user)

        # Add 2 family members sequentially
        self.selenium.find_element_by_css_selector(
            '#add-family-member-input-wrapper input').send_keys(family1_username)
        self.selenium.find_element_by_css_selector(
            '#add-family-member-input-wrapper button[type=submit]').click()

        family_member_names = self.selenium.find_elements_by_css_selector(
            '.family-member .family-member-name')
        self.assertEqual(1, len(family_member_names))
        self.assertIn(family1_username, family_member_names[0].text)

        self.selenium.find_element_by_css_selector(
            '#add-family-member-input-wrapper input').send_keys(family2.username)
        self.selenium.find_element_by_css_selector(
            '#add-family-member-input-wrapper button[type=submit]').click()

        family_member_names = self.selenium.find_elements_by_css_selector(
            '.family-member .family-member-name')
        self.assertEqual(2, len(family_member_names))
        self.assertIn(family1_username, family_member_names[0].text)
        self.assertIn(family2.username, family_member_names[1].text)

        # Make sure an email was sent to family member 1 (the one who didn't
        # already have an account).
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(f'{self.user.username} has added you', mail.outbox[0].subject)

        # Make sure family members are displayed on page load
        self.selenium.refresh()
        family_member_names = self.selenium.find_elements_by_css_selector(
            '.family-member .family-member-name')
        self.assertEqual(2, len(family_member_names))
        self.assertIn(family1_username, family_member_names[0].text)
        self.assertIn(family2.username, family_member_names[1].text)

        # Remove both family members
        remove_buttons = self.selenium.find_elements_by_css_selector(
            '.remove-family-member-form button[type=submit]')
        remove_buttons[0].click()
        wait = WebDriverWait(self.selenium, 5)
        wait.until(EC.alert_is_present())
        alert = self.selenium.switch_to.alert
        alert.accept()
        time.sleep(2)

        family_member_names = self.selenium.find_elements_by_css_selector(
            '.family-member .family-member-name')
        self.assertEqual(1, len(family_member_names))
        self.assertIn(family2.username, family_member_names[0].text)

        remove_buttons = self.selenium.find_elements_by_css_selector(
            '.remove-family-member-form button[type=submit]')
        remove_buttons[0].click()
        time.sleep(1)
        wait.until(EC.alert_is_present())
        alert = self.selenium.switch_to.alert
        alert.accept()
        time.sleep(2)

        family_member_names = self.selenium.find_elements_by_css_selector(
            '.family-member .family-member-name')
        self.assertEqual(0, len(family_member_names))

        self.selenium.refresh()
        family_member_names = self.selenium.find_elements_by_css_selector(
            '.family-member .family-member-name')
        self.assertEqual(0, len(family_member_names))

    def test_lifetime_members_can_add_family_members(self) -> None:
        MembershipSubscription.objects.create(
            owner=self.user, valid_until=None, membership_type=MembershipType.lifetime)

        family = User.objects.create_user(username='family1@wat.com')

        self.login_as(self.user)

        # Add 2 family members sequentially
        self.selenium.find_element_by_css_selector(
            '#add-family-member-input-wrapper input').send_keys(family.username)
        self.selenium.find_element_by_css_selector(
            '#add-family-member-input-wrapper button[type=submit]').click()

        family_member_names = self.selenium.find_elements_by_css_selector(
            '.family-member .family-member-name')
        self.assertEqual(1, len(family_member_names))
        self.assertIn(family.username, family_member_names[0].text)

    def test_membership_secretary_add_remove_family_members(self) -> None:
        MembershipSubscription.objects.create(
            owner=self.user, valid_until=timezone.now(), membership_type=MembershipType.regular)

        family = User.objects.create_user(username='family1@wat.com')

        self.login_as(self.make_membership_secretary(), f'/accounts/profile/{self.user.pk}/')

        # Add 2 family members sequentially
        self.selenium.find_element_by_css_selector(
            '#add-family-member-input-wrapper input').send_keys(family.username)
        self.selenium.find_element_by_css_selector(
            '#add-family-member-input-wrapper button[type=submit]').click()

        family_member_names = self.selenium.find_elements_by_css_selector(
            '.family-member .family-member-name')
        self.assertEqual(1, len(family_member_names))
        self.assertIn(family.username, family_member_names[0].text)


class MaxNumFamilyMembersTestCase(TestCase):
    def test_error_when_adding_too_many_family_members(self) -> None:
        user = User.objects.create_user(username='user@user.com', password='password')
        subscription = MembershipSubscription.objects.create(
            owner=user, valid_until=timezone.now(), membership_type=MembershipType.regular)

        family_members = [
            User.objects.create_user(username=f'family{i}@wat.com')
            for i in range(MAX_NUM_FAMILY_MEMBERS + 1)
        ]

        self.client.force_login(user)
        for family in family_members[:-1]:
            response = self.client.post(
                reverse('add-family-member', kwargs={'pk': subscription.pk}),
                {'username': family.username}
            )
            self.assertEqual(200, response.status_code)
            self.assertEqual('success', json.loads(response.content.decode())['status'])

        response = self.client.post(
            reverse('add-family-member', kwargs={'pk': subscription.pk}),
            {'username': family_members[-1].username}
        )
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content.decode())
        self.assertEqual('other_error', data['status'])
        self.assertEqual(
            f'You cannot add more than {MAX_NUM_FAMILY_MEMBERS} to a membership.',
            data['extra_data']['error_msg']
        )


class MembershipFormsPermissionTestCase(TestCase):
    def test_non_owner_non_membership_secretary_buy_subscription_permission_denied(self) -> None:
        user = User.objects.create_user(username='user@user.com', password='password')
        unauthorized_user = User.objects.create_user(
            username='other@other.com', password='password')

        self.client.force_login(unauthorized_user)
        response = self.client.post(
            reverse('purchase-subscription', kwargs={'pk': user.pk}),
            {'membership_type': MembershipType.regular}
        )
        self.assertEqual(403, response.status_code)
        self.assertFalse(MembershipSubscription.objects.filter(owner=user).exists())

    def test_non_owner_non_membership_secretary_add_family_permission_denied(self) -> None:
        user = User.objects.create_user(username='user@user.com', password='password')
        subscription = MembershipSubscription.objects.create(
            owner=user, valid_until=timezone.now(), membership_type=MembershipType.regular)

        unauthorized_user = User.objects.create_user(
            username='other@other.com', password='password')
        family = User.objects.create_user(username='family@family.com', password='password')

        self.client.force_login(unauthorized_user)
        response = self.client.post(
            reverse('add-family-member', kwargs={'pk': subscription.pk}),
            {'username': family.username}
        )
        self.assertEqual(403, response.status_code)
        subscription.refresh_from_db()
        self.assertEqual(0, subscription.family_members.count())

    def test_non_owner_non_membership_secretary_remove_family_permission_denied(self) -> None:
        user = User.objects.create_user(username='user@user.com', password='password')
        subscription = MembershipSubscription.objects.create(
            owner=user, valid_until=timezone.now(), membership_type=MembershipType.regular)
        family = User.objects.create_user(username='family@family.com', password='password')
        subscription.family_members.add(family)

        unauthorized_user = User.objects.create_user(
            username='other@other.com', password='password')
        self.client.force_login(unauthorized_user)
        response = self.client.post(
            reverse('remove-family-member', kwargs={'pk': subscription.pk}),
            {'username': family.username}
        )
        self.assertEqual(403, response.status_code)
        subscription.refresh_from_db()
        self.assertEqual(1, subscription.family_members.count())

    def test_invalid_donation_amount(self) -> None:
        user = User.objects.create_user(username='user@user.com', password='password')

        self.client.force_login(user)
        response = self.client.post(
            reverse('purchase-subscription', kwargs={'pk': user.pk}),
            {'membership_type': MembershipType.regular, 'donation': '-5'}
        )
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content.decode())
        self.assertEqual('form_validation_error', data['status'])
