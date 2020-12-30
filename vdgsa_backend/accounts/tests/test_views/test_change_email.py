from unittest import mock

from django.contrib.auth.models import Permission
from django.core import mail
from django.test import LiveServerTestCase, TestCase
from django.utils import timezone
from django.urls.base import reverse
from selenium.common.exceptions import (  # type: ignore ## FIXME
    ElementNotInteractableException, NoSuchElementException
)
from selenium.webdriver.firefox.webdriver import WebDriver  # type: ignore ## FIXME

from vdgsa_backend.accounts.models import AccountPermissions, ChangeEmailRequest, User


class ChangeEmailUITestCase(LiveServerTestCase):
    selenium: WebDriver
    user: User

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='steve@stove.com', password='password')

    def login_as(
        self,
        user: User,
        dest_url: str = '/accounts/profile/',
        password: str = 'password'
    ) -> None:
        """
        Visit dest_url in selenium, get redirected to login page,
        login as the specified user, get redirected back to dest_url.
        """
        self.selenium.get(f'{self.live_server_url}{dest_url}')
        self.selenium.find_element_by_id('id_username').send_keys(user.username)
        self.selenium.find_element_by_id('id_password').send_keys(password)
        self.selenium.find_element_by_css_selector('button[type=submit]').click()

    def test_change_email(self) -> None:
        self.login_as(self.user)

        # The change email form is hidden initially
        with self.assertRaises(ElementNotInteractableException):
            self.selenium.find_element_by_id('id_new_email').click()

        # Show the form
        self.selenium.find_element_by_id('show-change-email-form').click()

        # Hide the form
        self.selenium.find_element_by_id('change-email-cancel-button').click()
        with self.assertRaises(ElementNotInteractableException):
            self.selenium.find_element_by_id('id_new_email').click()

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
        self.assertEqual(self.selenium.find_element_by_id('current-username').text, new_email)
        self.user.refresh_from_db()
        self.assertEqual(new_email, self.user.username)
        self.assertEqual(new_email, self.user.email)

    def test_membership_secretary_change_other_user_email(self) -> None:
        membership_secretary = User.objects.create_user(
            username='waluigi@time.com', password='password')
        membership_secretary.user_permissions.add(
            Permission.objects.get(codename='membership_secretary'))

        self.login_as(membership_secretary, dest_url=f'/accounts/profile/{self.user.pk}/')

        # Show the form
        self.selenium.find_element_by_id('show-change-email-form').click()

        new_email = 'some_other_email@email.com'
        self.selenium.find_element_by_id('id_new_email').send_keys(new_email)
        self.selenium.find_element_by_css_selector(
            '#change-email-form button[type=submit]'
        ).click()

        # Email change happens immediately
        self.assertEqual(self.selenium.find_element_by_id('current-username').text, new_email)
        self.user.refresh_from_db()
        self.assertEqual(new_email, self.user.username)
        self.assertEqual(new_email, self.user.email)

    def test_membership_secretary_change_other_user_email_email_already_in_use(self) -> None:
        membership_secretary = User.objects.create_user(
            username='waluigi@time.com', password='password')
        membership_secretary.user_permissions.add(
            Permission.objects.get(codename='membership_secretary'))

        self.login_as(membership_secretary, dest_url=f'/accounts/profile/{self.user.pk}/')

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
