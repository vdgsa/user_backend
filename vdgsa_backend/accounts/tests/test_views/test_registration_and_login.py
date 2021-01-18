from django.core import mail
from selenium.common.exceptions import NoSuchElementException  # type: ignore

from vdgsa_backend.accounts.models import User

from .selenium_test_base import SeleniumTestCaseBase


class RegistrationAndLoginUITestCase(SeleniumTestCaseBase):
    def test_register_and_login(self) -> None:
        email = 'zomg_email@wat.com'

        first_name = 'noewfitanwf'
        last_name = 'nwfoiet'
        address_line_1 = 'zvorhsul'
        address_line_2 = 'nothief'
        address_city = 'nfieo'
        address_state = 'MU'
        address_postal_code = '1234234AA'
        address_country = 'noieftmwnf'

        # Go to the registration page, enter an email
        self.selenium.get(f'{self.live_server_url}/accounts/register/')
        self.selenium.find_element_by_id('id_email').send_keys(email)
        self.selenium.find_element_by_id('id_first_name').send_keys(first_name)
        self.selenium.find_element_by_id('id_last_name').send_keys(last_name)
        self.selenium.find_element_by_id('id_address_line_1').send_keys(address_line_1)
        self.selenium.find_element_by_id('id_address_line_2').send_keys(address_line_2)
        self.selenium.find_element_by_id('id_address_city').send_keys(address_city)
        self.selenium.find_element_by_id('id_address_state').send_keys(address_state)
        self.selenium.find_element_by_id('id_address_postal_code').send_keys(address_postal_code)
        self.selenium.find_element_by_id('id_address_country').send_keys(address_country)

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
        # Name and address in profile should be popluated with entered values.
        self.assertEqual(
            self.selenium.find_element_by_id('id_first_name').get_attribute('value'),
            first_name
        )
        self.assertEqual(
            self.selenium.find_element_by_id('id_last_name').get_attribute('value'),
            last_name
        )
        self.assertEqual(
            self.selenium.find_element_by_id('id_address_line_1').get_attribute('value'),
            address_line_1
        )
        self.assertEqual(
            self.selenium.find_element_by_id('id_address_line_2').get_attribute('value'),
            address_line_2
        )
        self.assertEqual(
            self.selenium.find_element_by_id('id_address_city').get_attribute('value'),
            address_city
        )
        self.assertEqual(
            self.selenium.find_element_by_id('id_address_state').get_attribute('value'),
            address_state
        )
        self.assertEqual(
            self.selenium.find_element_by_id('id_address_postal_code').get_attribute('value'),
            address_postal_code
        )
        self.assertEqual(
            self.selenium.find_element_by_id('id_address_country').get_attribute('value'),
            address_country
        )

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

    def _fill_name_and_address(self) -> None:
        """
        Fill name and address with some dummy values for tests where we don't
        care about that info.
        """
        self.selenium.find_element_by_id('id_first_name').send_keys('Firsty')
        self.selenium.find_element_by_id('id_last_name').send_keys('Lasty')
        self.selenium.find_element_by_id('id_address_line_1').send_keys('123 Street Rd')
        # Address line 2 is optional
        self.selenium.find_element_by_id('id_address_city').send_keys('The Fjords')
        self.selenium.find_element_by_id('id_address_state').send_keys('Bolton')
        self.selenium.find_element_by_id('id_address_postal_code').send_keys('43213')
        self.selenium.find_element_by_id('id_address_country').send_keys('US&A')
