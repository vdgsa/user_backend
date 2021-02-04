import time

from django.contrib.auth.models import Permission
from django.utils import timezone
from selenium.common.exceptions import NoSuchElementException  # type: ignore

from vdgsa_backend.accounts.models import MembershipSubscription, MembershipType, User

from .selenium_test_base import SeleniumTestCaseBase


class AccountsProfileUITestCase(SeleniumTestCaseBase):
    def setUp(self) -> None:
        super().setUp()
        self.membership_secretary = self.make_membership_secretary()
        MembershipSubscription.objects.create(
            owner=self.membership_secretary,
            valid_until=timezone.now() + timezone.timedelta(hours=10),
            membership_type=MembershipType.regular
        )

        self.user = User.objects.create_user(username='steve@stove.com', password='password')
        MembershipSubscription.objects.create(
            owner=self.user,
            valid_until=timezone.now() + timezone.timedelta(hours=10),
            membership_type=MembershipType.regular
        )

    def test_membership_secretary_sees_all_users_link(self) -> None:
        self.login_as(self.membership_secretary)
        self.selenium.find_element_by_id('all-users-link').click()
        self.assertTrue(self.selenium.find_element_by_id('user-table').is_displayed())

    def test_non_membership_secretary_no_all_users_link(self) -> None:
        self.login_as(self.user)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element_by_id('all-users-link')

    def test_nav_links(self) -> None:
        self.login_as(self.user)
        navlinks = self.selenium.find_elements_by_css_selector('nav a')
        expected_navlinks_text = [
            'VdGSA',
            'Members Area',
            'My Account',
            'Logout',
        ]
        self.assertCountEqual(expected_navlinks_text, [link.text for link in navlinks])

    def test_membership_secretary_sees_directory_nav_link(self) -> None:
        self.login_as(self.membership_secretary)
        navlinks = self.selenium.find_elements_by_css_selector('nav a')
        expected_navlinks_text = [
            'VdGSA',
            'Members Area',
            'My Account',
            'Directory',
            'Logout',
        ]
        self.assertCountEqual(expected_navlinks_text, [link.text for link in navlinks])

    def test_board_member_sees_directory_nav_link(self) -> None:
        self.login_as(self.make_board_member())
        navlinks = self.selenium.find_elements_by_css_selector('nav a')
        expected_navlinks_text = [
            'VdGSA',
            'Members Area',
            'My Account',
            'Directory',
            'Logout',
        ]
        self.assertCountEqual(expected_navlinks_text, [link.text for link in navlinks])

    def test_membership_secretary_view_other_users_profile(self) -> None:
        self.login_as(self.membership_secretary, dest_url=f'/accounts/profile/{self.user.pk}/')
        self.assertEqual(
            self.user.username,
            self.selenium.find_element_by_id('current-username').get_attribute('value')
        )

    def test_non_membership_secretary_cannot_view_other_users_profile(self) -> None:
        self.login_as(self.user, dest_url=f'/accounts/profile/{self.membership_secretary.pk}/')
        self.assertIn('Forbidden', self.selenium.find_element_by_css_selector('body').text)

    def test_regular_user_change_password(self) -> None:
        new_password = 'norevmnoufyravncmtvnwfapnnovfiremfoatn1232141234123419798'
        self.login_as(self.user)
        self.selenium.find_element_by_id('password-change-link').click()
        self.selenium.find_element_by_id('id_old_password').send_keys('password')
        self.selenium.find_element_by_id('id_new_password1').send_keys(new_password)
        self.selenium.find_element_by_id('id_new_password2').send_keys(new_password)
        self.selenium.find_element_by_css_selector('button[type=submit]').click()

        self.selenium.find_element_by_id('logout').click()
        time.sleep(2)

        self.login_as(self.user, password=new_password)
        self.assertEqual(
            self.selenium.find_element_by_id('current-username').get_attribute('value'),
            self.user.username
        )

    def test_membership_secretary_change_own_password(self) -> None:
        new_password = 'nomrefvnofveinfohnsnrt2382387423'
        self.login_as(self.membership_secretary)
        self.selenium.find_element_by_id('password-change-link').click()
        self.selenium.find_element_by_id('id_old_password').send_keys('password')
        self.selenium.find_element_by_id('id_new_password1').send_keys(new_password)
        self.selenium.find_element_by_id('id_new_password2').send_keys(new_password)
        self.selenium.find_element_by_css_selector('button[type=submit]').click()

        self.selenium.find_element_by_id('logout').click()
        time.sleep(2)

        self.login_as(self.membership_secretary, password=new_password)
        self.assertEqual(
            self.selenium.find_element_by_id('current-username').get_attribute('value'),
            self.membership_secretary.username
        )

    def test_membership_secretary_cannot_change_other_user_password(self) -> None:
        self.login_as(self.membership_secretary, dest_url=f'/accounts/profile/{self.user.pk}/')
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element_by_id('password-change-link')
