# import csv
# import tempfile
# import time
# from typing import List, Protocol, Sequence
from django.db.models import query
from django.test.testcases import TestCase
from vdgsa_backend.conclave_registration.models import ConclaveRegistrationConfig, Program, RegistrationEntry, RegistrationPhase

# from django.contrib.auth.models import Permission
# from django.test.testcases import TestCase
# from django.urls.base import reverse
# from django.utils import timezone
from selenium.common.exceptions import NoSuchElementException  # type: ignore
from selenium.webdriver.remote.webelement import WebElement  # type: ignore
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore

from vdgsa_backend.accounts.models import MembershipSubscription, MembershipType, User
# from vdgsa_backend.templatetags.filters import format_datetime_impl

from vdgsa_backend.selenium_test_base import SeleniumTestCaseBase


class ConclaveRegistrationLandingPageTestCase(SeleniumTestCaseBase):
    conclave_config: ConclaveRegistrationConfig
    user: User

    def setUp(self) -> None:
        self.conclave_config = ConclaveRegistrationConfig.objects.create(
            year=2019, phase=RegistrationPhase.open
        )
        self.user = User.objects.create_user('useron@user.edu', password='password')
        MembershipSubscription.objects.create(
            owner=self.user, membership_type=MembershipType.lifetime)

    def test_select_regular_program(self) -> None:
        self.login_as(self.user, dest_url=f'/conclave/{self.conclave_config.pk}/register')
        self.assertEqual(
            f'Conclave {self.conclave_config.year} Registration',
            self.find('#registration-landing-header').text
        )
        self.assertEqual('regular', self.get_value('#id_program'))

        button = self.find('form button')
        self.assertEqual('Start Registration', button.text)
        self.click_on(button)

        self.assertEqual('Misc Info', self.find('[data-testid=registration_section_header]').text)

        query = RegistrationEntry.objects.all()
        self.assertEqual(1, query.count())

        reg_entry = query.first()
        self.assertEqual(Program.regular, reg_entry.program)
        self.assertEqual(reg_entry.conclave_config, self.conclave_config)
        self.assertEqual(reg_entry.user, self.user)

    def test_select_faculty_registration_with_password(self) -> None:
        password = 'nrsoietanrsit'
        self.login_as(self.user, dest_url=f'/conclave/{self.conclave_config.pk}/register')

        self.assertFalse(self.find('#id_faculty_registration_password').is_displayed())
        self.click_on(self.find_all('#id_program option')[1])
        self.set_value('#id_faculty_registration_password', password)

        self.click_on(self.find('form button'))

        self.assertEqual('Misc Info', self.find('[data-testid=registration_section_header]').text)

        query = RegistrationEntry.objects.all()
        self.assertEqual(1, query.count())

        reg_entry = query.first()
        self.assertEqual(Program.faculty_guest_other, reg_entry.program)
        self.assertEqual(reg_entry.conclave_config, self.conclave_config)
        self.assertEqual(reg_entry.user, self.user)

    def test_registration_already_started_redirect(self) -> None:
        RegistrationEntry.objects.create(
            conclave_config=self.conclave_config,
            user=self.user,
            program=Program.regular
        )

        self.login_as(self.user, dest_url=f'/conclave/{self.conclave_config.pk}/register')
        self.assertEqual('Misc Info', self.find('[data-testid=registration_section_header]').text)

    def test_membership_out_of_date_message(self) -> None:
        self.user.subscription.delete()
        self.login_as(self.user, dest_url=f'/conclave/{self.conclave_config.pk}/register')
        self.assertIn(
            'membership is not up to date',
            self.find('[data-testid=membership_renewal_message]').text
        )

        self.click_on(self.find('[data-testid=accounts_link]'))
        self.assertEqual('Pay For Your Membership', self.find('#membership-header').text)

    def test_registration_unpublished_permission_denied(self) -> None:
        self.conclave_config.phase = RegistrationPhase.unpublished
        self.conclave_config.save()
        self.login_as(self.user, dest_url=f'/conclave/{self.conclave_config.pk}/register')

        self.assertIn('Forbidden', self.find('body').text)
        self.assertEqual(0, RegistrationEntry.objects.count())

    def test_conclave_team_start_unpublished_registration(self) -> None:
        self.conclave_config.phase = RegistrationPhase.unpublished
        self.conclave_config.save()

        user = self.make_conclave_team()
        self.login_as(user, dest_url=f'/conclave/{self.conclave_config.pk}/register')

        button = self.find('form button')
        self.assertEqual('Start Registration', button.text)
        self.click_on(button)

        self.assertEqual('Misc Info', self.find('[data-testid=registration_section_header]').text)

        query = RegistrationEntry.objects.all()
        self.assertEqual(1, query.count())

        reg_entry = query.first()
        self.assertEqual(Program.regular, reg_entry.program)
        self.assertEqual(reg_entry.conclave_config, self.conclave_config)
        self.assertEqual(reg_entry.user, user)

    def test_late_registration_message(self) -> None:
        self.conclave_config.phase = RegistrationPhase.late
        self.conclave_config.save()

        self.login_as(self.user, dest_url=f'/conclave/{self.conclave_config.pk}/register')
        self.assertIn('(Late)', self.find('#registration-landing-header').text)

        button = self.find('form button')
        self.assertEqual('Start Registration', button.text)
        self.click_on(button)

        self.assertEqual('Misc Info', self.find('[data-testid=registration_section_header]').text)

        query = RegistrationEntry.objects.all()
        self.assertEqual(1, query.count())

        reg_entry = query.first()
        self.assertEqual(Program.regular, reg_entry.program)
        self.assertEqual(reg_entry.conclave_config, self.conclave_config)
        self.assertEqual(reg_entry.user, self.user)
        self.assertTrue(reg_entry.is_late)

    def test_registration_closed_message(self) -> None:
        self.conclave_config.phase = RegistrationPhase.closed
        self.conclave_config.save()

        self.login_as(self.user, dest_url=f'/conclave/{self.conclave_config.pk}/register')
        self.assertIn('closed', self.find('[data-testid=registration_closed_message]').text)
        self.assertFalse(self.exists('form'))

    def test_registration_closed_registration_already_started(self) -> None:
        self.conclave_config.phase = RegistrationPhase.closed
        self.conclave_config.save()

        RegistrationEntry.objects.create(
            conclave_config=self.conclave_config,
            user=self.user,
            program=Program.regular
        )

        self.login_as(self.user, dest_url=f'/conclave/{self.conclave_config.pk}/register')
        self.assertIn('closed', self.find('[data-testid=registration_closed_message]').text)
        self.assertFalse(self.exists('[data-testid=registration_section_header]'))


class StartRegistrationPermissionsTestCase(TestCase):
    def test_registration_unpublished_permission_denied(self) -> None:
        self.fail()

    def test_registration_closed_permission_denied(self) -> None:
        self.fail()


# class RegistrationBaseTestCases(SeleniumTestCaseBase):
#     def test_(self) -> None:
#         self.fail()

    # Do we want this restriction?
    # def test_membership_expired_after_registration_started(self) -> None:
    #     self.fail()
