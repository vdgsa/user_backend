from django.test import TestCase
from django.urls.base import reverse
from django.utils import timezone

from vdgsa_backend.accounts.models import MembershipSubscription, MembershipType, User

from ..selenium_test_base import SeleniumTestCaseBase


class UserProfileFormUI(SeleniumTestCaseBase):
    user: User

    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.create_user(
            username='steve@stove.com',
            password='password',
            first_name='Old First',
            last_name='Old Last',
            address_line_1='Old Street',
            address_line_2='Old apt number',
            address_city='Old Cityyy',
            address_state='Old State',
            address_postal_code='78906',
            address_country='Old country',
            phone1='1234512345',
            phone2='4321432143',
        )
        # Give our user a membership so that we see the full account page
        MembershipSubscription.objects.create(
            owner=self.user,
            valid_until=timezone.now() + timezone.timedelta(hours=500),
            membership_type=MembershipType.regular
        )

    def test_edit_contact_info_required_only(self) -> None:
        self.login_as(self.user)

        self.assertEqual(self.user.first_name, self.get_value('#id_first_name'))
        self.assertEqual(self.user.last_name, self.get_value('#id_last_name'))
        self.assertEqual(self.user.address_line_1, self.get_value('#id_address_line_1'))
        self.assertEqual(self.user.address_line_2, self.get_value('#id_address_line_2'))
        self.assertEqual(self.user.address_city, self.get_value('#id_address_city'))
        self.assertEqual(self.user.address_state, self.get_value('#id_address_state'))
        self.assertEqual(self.user.address_postal_code, self.get_value('#id_address_postal_code'))
        self.assertEqual(self.user.address_country, self.get_value('#id_address_country'))
        self.assertEqual(self.user.phone1, self.get_value('#id_phone1'))
        self.assertEqual(self.user.phone2, self.get_value('#id_phone2'))
        self.assertEqual('', self.get_value('#id_website'))

        self.set_value('#id_first_name', 'Firsto')
        self.set_value('#id_last_name', 'Lasto')
        self.set_value('#id_address_line_1', '123 Street')
        self.set_value('#id_address_line_2', '')
        self.set_value('#id_address_city', 'An City')
        self.set_value('#id_address_state', 'Statey')
        self.set_value('#id_address_postal_code', '43215')
        self.set_value('#id_address_country', 'US&A')
        self.set_value('#id_phone1', '')
        self.set_value('#id_phone2', '')

        self.assertEqual('', self.find('.last-saved').text)
        self.click_on(self.find('[data-testid=save_user_profile'))
        self.wait.until(lambda _: self.find('.last-saved').text.strip() != '')

        self.user.refresh_from_db()
        self.assertEqual('Firsto', self.user.first_name)

        self.selenium.refresh()
        self.assertEqual('Firsto', self.get_value('#id_first_name'))
        self.assertEqual('Lasto', self.get_value('#id_last_name'))
        self.assertEqual('123 Street', self.get_value('#id_address_line_1'))
        self.assertEqual('', self.get_value('#id_address_line_2'))
        self.assertEqual('An City', self.get_value('#id_address_city'))
        self.assertEqual('Statey', self.get_value('#id_address_state'))
        self.assertEqual('43215', self.get_value('#id_address_postal_code'))
        self.assertEqual('US&A', self.get_value('#id_address_country'))
        self.assertEqual('', self.get_value('#id_phone1'))
        self.assertEqual('', self.get_value('#id_phone2'))
        self.assertEqual('', self.get_value('#id_website'))

    def test_edit_contact_info_all_fields(self) -> None:
        self.login_as(self.user)

        self.assertEqual(self.user.first_name, self.get_value('#id_first_name'))
        self.assertEqual(self.user.last_name, self.get_value('#id_last_name'))
        self.assertEqual(self.user.address_line_1, self.get_value('#id_address_line_1'))
        self.assertEqual(self.user.address_line_2, self.get_value('#id_address_line_2'))
        self.assertEqual(self.user.address_city, self.get_value('#id_address_city'))
        self.assertEqual(self.user.address_state, self.get_value('#id_address_state'))
        self.assertEqual(self.user.address_postal_code, self.get_value('#id_address_postal_code'))
        self.assertEqual(self.user.address_country, self.get_value('#id_address_country'))
        self.assertEqual(self.user.phone1, self.get_value('#id_phone1'))
        self.assertEqual(self.user.phone2, self.get_value('#id_phone2'))
        self.assertEqual('', self.get_value('#id_website'))

        self.set_value('#id_first_name', 'Firsto')
        self.set_value('#id_last_name', 'Lasto')
        self.set_value('#id_address_line_1', '123 Street')
        self.set_value('#id_address_line_2', 'some apartment 4')
        self.set_value('#id_address_city', 'An City')
        self.set_value('#id_address_state', 'Statey')
        self.set_value('#id_address_postal_code', '43215')
        self.set_value('#id_address_country', 'US&A')
        self.set_value('#id_phone1', '1234123412')
        self.set_value('#id_phone2', '7897897890')
        self.set_value('#id_website', 'www.waluigi.com')

        self.assertEqual('', self.find('.last-saved').text)
        self.click_on(self.find('[data-testid=save_user_profile'))
        self.wait.until(lambda _: self.find('.last-saved').text.strip() != '')

        self.user.refresh_from_db()
        self.assertEqual('Firsto', self.user.first_name)

        self.selenium.refresh()
        self.assertEqual('Firsto', self.get_value('#id_first_name'))
        self.assertEqual('Lasto', self.get_value('#id_last_name'))
        self.assertEqual('123 Street', self.get_value('#id_address_line_1'))
        self.assertEqual('some apartment 4', self.get_value('#id_address_line_2'))
        self.assertEqual('An City', self.get_value('#id_address_city'))
        self.assertEqual('Statey', self.get_value('#id_address_state'))
        self.assertEqual('43215', self.get_value('#id_address_postal_code'))
        self.assertEqual('US&A', self.get_value('#id_address_country'))
        self.assertEqual('1234123412', self.get_value('#id_phone1'))
        self.assertEqual('7897897890', self.get_value('#id_phone2'))
        self.assertEqual('www.waluigi.com', self.get_value('#id_website'))

    def test_affiliations(self) -> None:
        self.login_as(self.user)

        self.assertFalse(self.find('#id_is_young_player').is_selected())
        self.assertEqual('', self.get_value('#id_educational_institution_affiliation'))

        self.click_on(self.find('#id_is_young_player'))
        self.set_value('#id_educational_institution_affiliation', 'WAAAA stuff')

        self.click_on(self.find('[data-testid=save_user_profile'))
        self.wait.until(lambda _: self.find('.last-saved').text.strip() != '')
        self.selenium.refresh()

        self.assertTrue(self.find('#id_is_young_player').is_selected())
        self.assertEqual(
            'WAAAA stuff',
            self.get_value('#id_educational_institution_affiliation')
        )

    def test_teachers(self) -> None:
        self.login_as(self.user)

        self.do_checkbox_toggle_test('#id_is_teacher', False)
        self.do_checkbox_toggle_test('#id_is_remote_teacher', False)

        self.do_text_value_change_test(
            '#id_teacher_description', '', 'noersatonirsa noriseta norst')

    def test_commercial_members(self) -> None:
        self.login_as(self.user)

        self.do_checkbox_toggle_test('#id_is_instrument_maker', False)
        self.do_checkbox_toggle_test('#id_is_bow_maker', False)
        self.do_checkbox_toggle_test('#id_is_repairer', False)
        self.do_checkbox_toggle_test('#id_is_publisher', False)

        self.do_text_value_change_test('#id_other_commercial', '', 'harps')
        self.assertTrue(self.find('[data-testid=other_commercial]'))
        self.do_text_value_change_test('#id_commercial_description', '', 'me business')

    def test_privacy(self) -> None:
        self.login_as(self.user)

        self.do_checkbox_toggle_test('#id_do_not_email', False)
        self.do_checkbox_toggle_test('#id_include_name_in_membership_directory', True)
        self.do_checkbox_toggle_test('#id_include_email_in_membership_directory', True)
        self.do_checkbox_toggle_test('#id_include_address_in_membership_directory', True)
        self.do_checkbox_toggle_test('#id_include_phone_in_membership_directory', True)

    def test_membership_secretary_can_edit(self) -> None:
        self.login_as(self.make_membership_secretary(), dest_url=f'/accounts/{self.user.pk}/')

        self.do_checkbox_toggle_test('#id_is_remote_teacher', False)
        self.do_checkbox_toggle_test('#id_is_bow_maker', False)
        self.do_checkbox_toggle_test('#id_include_email_in_membership_directory', True)

        self.do_text_value_change_test('#id_first_name', self.user.first_name, 'Firsto')
        self.do_text_value_change_test('#id_phone2', self.user.phone2, '7897897890')
        self.do_text_value_change_test('#id_website', self.user.website, 'www.waluigi.com')

        self.do_checkbox_toggle_test('#id_is_deceased', False)
        self.do_text_value_change_test('#id_notes', '', 'This person is not a person')

    def test_non_membership_secretary_secret_fields_hidden(self) -> None:
        self.login_as(self.user)
        self.assertFalse(self.exists('[data-testid=secret_membership_secretary_fields]'))

    def do_text_value_change_test(
        self,
        selector: str,
        initial_value: str,
        new_value: str
    ) -> None:
        self.assertEqual(initial_value, self.get_value(selector))
        self.set_value(selector, new_value)

        self.click_on(self.find('[data-testid=save_user_profile'))
        self.wait.until(lambda _: self.find('.last-saved').text.strip() != '')
        self.selenium.refresh()

        self.assertEqual(new_value, self.get_value(selector))

    def do_checkbox_toggle_test(self, selector: str, initially_selected: bool) -> None:
        self.assertEqual(initially_selected, self.find(selector).is_selected())
        self.click_on(self.find(selector))

        self.click_on(self.find('[data-testid=save_user_profile'))
        self.wait.until(lambda _: self.find('.last-saved').text.strip() != '')
        self.selenium.refresh()

        self.assertEqual(not initially_selected, self.find(selector).is_selected())
        self.click_on(self.find(selector))

        self.click_on(self.find('[data-testid=save_user_profile'))
        self.wait.until(lambda _: self.find('.last-saved').text.strip() != '')
        self.selenium.refresh()

        self.assertEqual(initially_selected, self.find(selector).is_selected())


class UserProfileFormPermissions(TestCase):
    def test_other_user_non_membership_secretary_edit_profile_permission_denied(self) -> None:
        user = User.objects.create_user(username='steve@stove.com', password='password')
        requester = User.objects.create_user(username='bad@bad.com', password='password')

        self.client.force_login(requester)
        response = self.client.post(
            reverse('user-profile', kwargs={'pk': user.pk}),
            {'first_name': 'WAAAAAAAAAAAAAAAA'}
        )
        self.assertEqual(403, response.status_code)

    def test_membership_secretary_only_fields_ignored_if_not_membership_secretary(self) -> None:
        user = User.objects.create_user(username='steve@stove.com', password='password')
        self.assertFalse(user.is_deceased)
        self.assertTrue(user.receives_expiration_reminder_emails)
        self.assertEqual('', user.notes)

        self.client.force_login(user)
        response = self.client.post(
            reverse('user-profile', kwargs={'pk': user.pk}),
            {'is_deceased': True, 'notes': 'WAAAAAAAAAA'}
        )
        self.assertEqual(200, response.status_code)

        user.refresh_from_db()
        self.assertFalse(user.is_deceased)
        self.assertTrue(user.receives_expiration_reminder_emails)
        self.assertEqual('', user.notes)
