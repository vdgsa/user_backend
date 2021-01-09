import time

from django.test import TestCase
from django.utils import timezone
from selenium.common.exceptions import NoSuchElementException  # type: ignore
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore

from vdgsa_backend.accounts.models import MembershipSubscription, MembershipType, User
from vdgsa_backend.accounts.templatetags.filters import format_datetime_impl
from vdgsa_backend.accounts.tests.test_views.selenium_test_base import SeleniumTestCaseBase


class MembershipUITestCase(SeleniumTestCaseBase):
    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.create_user(username='steve@stove.com', password='password')

    def test_purchase_subscription_form_toggle(self) -> None:
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

        # TODO: Figure out why this button click closes and then immediately re-opens
        # the collapsible in selenium only.
        # self.selenium.find_element_by_id('hide-purchase-subscription').click()
        # time.sleep(2)  # Wait for bootstrap's animation to finish
        # self.assertFalse(
        #     self.selenium.find_element_by_id('purchase-subscription-form').is_displayed())

        # TODO: Figure out a good way to integration test the stripe webhook

    def test_purchase_regular_subscription(self) -> None:
        self.login_as(self.user)
        self.assertIn(
            'become a member',
            self.selenium.find_element_by_id('show-membership-purchase').text.lower()
        )
        self.selenium.find_element_by_id('show-membership-purchase').click()
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

        # TODO: Figure out a good way to integration test the stripe webhook

    def test_purchase_student_subscription_with_donation(self) -> None:
        self.login_as(self.user)
        self.selenium.find_element_by_id('show-membership-purchase').click()

        self.selenium.find_element_by_id('id_membership_type').click()
        self.selenium.find_elements_by_css_selector('#id_membership_type option')[1].click()

        self.selenium.find_element_by_id('id_donation').send_keys('20')
        self.selenium.find_element_by_css_selector(
            '#purchase-subscription-form button[type=submit]'
        ).click()

        wait = WebDriverWait(self.selenium, 5)
        wait.until(
            lambda driver: driver.find_element_by_id('ProductSummary-totalAmount').text != '')
        self.assertIn(
            '$55.00',
            self.selenium.find_element_by_id('ProductSummary-totalAmount').text
        )
        self.assertIn('checkout.stripe.com', self.selenium.current_url)

    def test_renew_subscription(self) -> None:
        valid_until = timezone.now() + timezone.timedelta(days=1)
        MembershipSubscription.objects.create(
            owner=self.user, valid_until=valid_until, membership_type=MembershipType.regular)

        self.login_as(self.user)
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
            '$40.00',
            self.selenium.find_element_by_id('ProductSummary-totalAmount').text
        )
        self.assertIn('checkout.stripe.com', self.selenium.current_url)

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
        self.assertIn(
            'become a member',
            self.selenium.find_element_by_id('show-membership-purchase').text.lower()
        )
        # When the membership secretary purchases a membership, it skips the Stripe flow.
        self.selenium.find_element_by_id('show-membership-purchase').click()
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
        self.fail()

    def test_membership_secretary_add_remove_family_members(self) -> None:
        self.fail()


class MembershipFormsPermission(TestCase):
    def test_membership_purchase_form_permissions(self) -> None:
        self.fail()

    def test_add_remove_family_permissions(self) -> None:
        self.fail()

    def test_invalid_donation_amount(self) -> None:
        # self.login_as(self.user)
        # self.selenium.find_element_by_id('show-membership-purchase').click()

        # self.selenium.find_element_by_id('id_membership_type').click()
        # self.selenium.find_elements_by_css_selector('#id_membership_type option')[1].click()

        # self.selenium.find_element_by_id('id_donation').send_keys('20')
        # self.selenium.find_element_by_css_selector(
        #     '#purchase-subscription-form button[type=submit]'
        # ).click()

        self.fail()
