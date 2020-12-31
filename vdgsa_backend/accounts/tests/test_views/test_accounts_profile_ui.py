from django.contrib.auth.models import Permission

from vdgsa_backend.accounts.models import User

from .selenium_test_base import SeleniumTestCaseBase


class AccountsProfileUITestCase(SeleniumTestCaseBase):
    def setUp(self) -> None:
        self.membership_secretary = User.objects.create_user(
            username='memsec@steve.com', password='password'
        )
        self.membership_secretary.user_permissions.add(
            Permission.objects.get(codename='membership_secretary')
        )

        self.user = User.objects.create_user(username='steve@stove.com', password='password')

    def test_membership_secretary_sees_all_users_link(self) -> None:
        self.login_as(self.membership_secretary)
        navlinks = self.selenium.find_elements_by_css_selector('nav a')
        expected_navlinks_text = [
            'VdGSA',
            'Members Area',
            'All Users',
            'My Account',
            'Logout',
        ]
        self.assertCountEqual(expected_navlinks_text, [link.text for link in navlinks])

    def test_non_membership_secretary_no_all_users_link(self) -> None:
        self.login_as(self.user)
        navlinks = self.selenium.find_elements_by_css_selector('nav a')
        expected_navlinks_text = [
            'VdGSA',
            'Members Area',
            'My Account',
            'Logout',
        ]
        self.assertCountEqual(expected_navlinks_text, [link.text for link in navlinks])

    def test_membership_secretary_view_other_users_profile(self) -> None:
        self.login_as(self.membership_secretary, dest_url=f'/accounts/profile/{self.user.pk}/')
        self.assertEqual(
            self.user.username,
            self.selenium.find_element_by_id('current-username').text
        )

    def test_non_membership_secretary_cannot_view_other_users_profile(self) -> None:
        self.login_as(self.user, dest_url=f'/accounts/profile/{self.membership_secretary.pk}/')
        self.assertIn('Forbidden', self.selenium.find_element_by_css_selector('body').text)
