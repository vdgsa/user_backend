from django.core import mail
from selenium.common.exceptions import NoSuchElementException  # type: ignore ## FIXME

from vdgsa_backend.accounts.models import User

from .selenium_test_base import SeleniumTestCaseBase


class RegistrationAndLoginUITestCase(SeleniumTestCaseBase):
    def test_register_and_login(self) -> None:
        email = 'zomg_email@wat.com'

        # Go to the registration page, enter an email
        self.selenium.get(f'{self.live_server_url}/accounts/register/')
        email_input = self.selenium.find_element_by_id('id_email')
        email_input.send_keys(email)
        self.selenium.find_element_by_css_selector('button[type=submit]').click()

        self.assertEqual('Almost Done!', self.selenium.find_element_by_id('almost-done-msg').text)

        # Go to the password set link from the email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Finish Creating Your VdGSA Account')
        password_set_url = mail.outbox[0].body.split('\n')[-4]
        self.selenium.get(password_set_url)

        # Set a password
        password = 'AnPassword42'
        self.selenium.find_element_by_id('id_new_password1').send_keys(password)
        self.selenium.find_element_by_id('id_new_password2').send_keys(password)
        self.selenium.find_element_by_css_selector('button[type=submit]').click()

        # Redirected to login page, and sign in
        self.selenium.find_element_by_id('id_username').send_keys(email)
        self.selenium.find_element_by_id('id_password').send_keys(password)
        self.selenium.find_element_by_css_selector('button[type=submit]').click()

        self.assertEqual(self.selenium.find_element_by_id('current-username').text, email)

    def test_username_taken(self) -> None:
        email = 'batman@bat.man'
        User.objects.create_user(username=email, email=email, password='password')

        self.selenium.get(f'{self.live_server_url}/accounts/register/')
        self.selenium.find_element_by_id('id_email').send_keys(email)
        self.selenium.find_element_by_css_selector('button[type=submit]').click()

        self.assertTrue(
            'There is already an account associated with that email address.',
            self.selenium.find_element_by_id('username-taken-msg')
        )

    def test_inactive_user_object_with_same_email_exists(self) -> None:
        email = 'batman@bat.man'
        User.objects.create(username=email, email=email)

        self.selenium.get(f'{self.live_server_url}/accounts/register/')
        self.selenium.find_element_by_id('id_email').send_keys(email)
        self.selenium.find_element_by_css_selector('button[type=submit]').click()

        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element_by_id('username-taken-msg')

    def test_password_reset(self) -> None:
        email = 'batman@bat.man'
        User.objects.create(username=email, email=email)

        self.selenium.get(f'{self.live_server_url}/password_reset/')
        email_input = self.selenium.find_element_by_id('id_email')
        email_input.send_keys(email)
        self.selenium.find_element_by_css_selector('button[type=submit]').click()

        # Go to the password reset link from the email
        password_set_url = mail.outbox[0].body.split('\n')[-10]
        self.selenium.get(password_set_url)

        # Try too common password
        password = 'password'
        self.selenium.find_element_by_id('id_new_password1').send_keys(password)
        self.selenium.find_element_by_id('id_new_password2').send_keys(password)
        self.selenium.find_element_by_css_selector('button[type=submit]').click()

        errors = self.selenium.find_elements_by_css_selector('.form-field-errors .errorlist li')
        self.assertEqual(1, len(errors))
        self.assertIn('too common', errors[0].text)

        # Use good password
        password = 'noifevkmnoirfuvnsvknriosuetahnoriftkmnnrostemnsmtknoiers'

        self.selenium.find_element_by_id('id_new_password1').send_keys(password)
        self.selenium.find_element_by_id('id_new_password2').send_keys(password)
        self.selenium.find_element_by_css_selector('button[type=submit]').click()

        # Redirected to login page, and sign in
        self.selenium.find_element_by_id('id_username').send_keys(email)
        self.selenium.find_element_by_id('id_password').send_keys(password)
        self.selenium.find_element_by_css_selector('button[type=submit]').click()

        self.assertEqual(self.selenium.find_element_by_id('current-username').text, email)
