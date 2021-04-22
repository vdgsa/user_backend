import time
from vdgsa_backend.conclave_registration.views.conclave_registration_views import BasicInfoForm
from django.test.testcases import TestCase
from django.urls import reverse
from selenium.common.exceptions import NoSuchElementException  # type: ignore
from selenium.webdriver.remote.webelement import WebElement  # type: ignore
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore

from vdgsa_backend.accounts.models import MembershipSubscription, MembershipType, User
from vdgsa_backend.conclave_registration.models import (
    BasicRegistrationInfo, Class, Clef, ConclaveRegistrationConfig, InstrumentBringing, InstrumentChoices, Level, PaymentInfo, Period, Program, RegistrationEntry, RegistrationPhase, RegularProgramClassChoices, TShirtSizes, TShirts, TuitionOption, WorkStudyApplication, WorkStudyJob, YesNoMaybe
)
from vdgsa_backend.selenium_test_base import SeleniumTestCaseBase


class _SetUp:
    conclave_config: ConclaveRegistrationConfig
    user: User

    def setUp(self) -> None:
        super().setUp()  # type: ignore
        self.conclave_config = ConclaveRegistrationConfig.objects.create(
            year=2019, phase=RegistrationPhase.open
        )
        self.user = User.objects.create_user('useron@user.edu', password='password')
        MembershipSubscription.objects.create(
            owner=self.user, membership_type=MembershipType.lifetime)


class ConclaveRegistrationLandingPageTestCase(_SetUp, SeleniumTestCaseBase):
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

    def test_conclave_team_start_unpublished_registration_for_self(self) -> None:
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

        reg_entry = RegistrationEntry.objects.create(
            conclave_config=self.conclave_config,
            user=self.user,
            program=Program.regular
        )

        self.login_as(self.user, dest_url=f'/conclave/register/{reg_entry.pk}/basic_info')
        self.assertIn('closed', self.find('[data-testid=registration_closed_message]').text)
        self.assertFalse(self.exists('[data-testid=registration_section_header]'))

    def test_conclave_team_start_closed_registration_for_self(self) -> None:
        self.conclave_config.phase = RegistrationPhase.closed
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

    def test_conclave_team_registration_closed_registration_already_started(self) -> None:
        self.conclave_config.phase = RegistrationPhase.closed
        self.conclave_config.save()

        reg_entry = RegistrationEntry.objects.create(
            conclave_config=self.conclave_config,
            user=self.user,
            program=Program.regular
        )

        user = self.make_conclave_team()
        self.login_as(user, dest_url=f'/conclave/register/{reg_entry.pk}/basic_info')
        self.assertEqual('Misc Info', self.find('[data-testid=registration_section_header]').text)

    def test_editing_not_allowed_after_submitting_payment(self) -> None:
        reg_entry = RegistrationEntry.objects.create(
            conclave_config=self.conclave_config,
            user=self.user,
            program=Program.regular
        )
        PaymentInfo.objects.create(
            registration_entry=reg_entry, stripe_payment_method_id='12341234142'
        )

        self.login_as(self.user, dest_url=f'/conclave/{self.conclave_config.pk}/register')
        self.assertIn('finalized', self.find('[data-testid=registration_finalized_message]').text)
        self.assertFalse(self.exists('[data-testid=registration_section_header]'))

    def test_conclave_team_can_edit_finalized_registration(self) -> None:
        reg_entry = RegistrationEntry.objects.create(
            conclave_config=self.conclave_config,
            user=self.user,
            program=Program.regular
        )
        PaymentInfo.objects.create(
            registration_entry=reg_entry, stripe_payment_method_id='12341234142'
        )

        user = self.make_conclave_team()
        self.login_as(user, dest_url=f'/conclave/register/{reg_entry.pk}/basic_info')
        self.assertEqual('Misc Info', self.find('[data-testid=registration_section_header]').text)


class StartRegistrationPermissionsTestCase(TestCase):
    conclave_config: ConclaveRegistrationConfig
    user: User

    def setUp(self) -> None:
        super().setUp()
        self.conclave_config = ConclaveRegistrationConfig.objects.create(
            year=2019, phase=RegistrationPhase.unpublished
        )
        self.user = User.objects.create_user('useron@user.edu', password='password')
        MembershipSubscription.objects.create(
            owner=self.user, membership_type=MembershipType.lifetime)

    def test_registration_unpublished_permission_denied(self) -> None:
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('conclave-reg-landing', kwargs={'conclave_config_pk': self.conclave_config.pk})
        )
        self.assertEqual(403, response.status_code)

    def test_registration_closed_permission_denied(self) -> None:
        self.client.force_login(self.user)
        self.conclave_config.phase = RegistrationPhase.closed
        self.conclave_config.save()

        response = self.client.post(
            reverse('conclave-reg-landing', kwargs={'conclave_config_pk': self.conclave_config.pk})
        )
        self.assertEqual(403, response.status_code)

    def test_membership_expired_permission_denied(self) -> None:
        self.client.force_login(self.user)
        self.user.subscription.delete()

        response = self.client.post(
            reverse('conclave-reg-landing', kwargs={'conclave_config_pk': self.conclave_config.pk})
        )
        self.assertEqual(403, response.status_code)

    # def test_editing_not_allowed_after_submitting_payment(self) -> None:
    #     reg_entry = RegistrationEntry.objects.create(
    #         conclave_config=self.conclave_config,
    #         user=self.user,
    #         program=Program.regular
    #     )
    #     PaymentInfo.objects.create(
    #         registration_entry=reg_entry, stripe_payment_method_id='12341234142'
    #     )

    #     # change url, have one of these tests for each registration step
    #     response = self.client.post(
    #         reverse('conclave-reg-landing', kwargs={'conclave_config_pk': self.conclave_config.pk})
    #     )
    #     self.assertEqual(403, response.status_code)


class _SetUpRegistrationEntry(_SetUp):
    registration_entry: RegistrationEntry

    def setUp(self) -> None:
        super().setUp()  # type: ignore

        self.registration_entry = RegistrationEntry.objects.create(
            conclave_config=self.conclave_config,
            user=self.user,
            program=Program.regular,
        )


# class RegistrationBaseViewTestCases(_SetUpRegistrationEntry, SeleniumTestCaseBase):
#     def test_sidebar_navigation_regular_flow(self) -> None:
#         self.fail()


# class BasicInfoViewTestCase(_SetUpRegistrationEntry, SeleniumTestCaseBase):
#     def test_required_fields_only(self) -> None:
#         self.fail()

#     def test_all_fields(self) -> None:
#         self.fail()

#     def test_liability_release_required(self) -> None:
#         self.fail()


# class WorkStudyViewTestCase(_SetUpRegistrationEntry, SeleniumTestCaseBase):
#     def test_form_initial_values(self) -> None:
#         self.fail()

#     def test_redirect_on_save(self) -> None:
#         self.fail()

#     # def test_data_persists_after_save(self) -> None:
#     #     self.fail()


class InstrumentsBringingViewTestCase(_SetUpRegistrationEntry, SeleniumTestCaseBase):
    def test_add_and_remove_mutiple_instruments(self) -> None:
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/instruments'
        )

        # Add instruments

        self.click_on(self.find_all('#id_size option')[2])
        self.click_on(self.find_all('#id_level option')[1])
        self.click_on(self.find('#id_clefs_0'))
        self.click_on(self.find('#id_clefs_2'))
        self.click_on(self.find('form button'))
        self.wait.until(lambda _: len(self.find_all('.instrument-row')) == 1)
        self._check_instrument_row_content(0, 'Tenor', 'B', 'Treble clef, Alto clef')

        self.click_on(self.find_all('#id_size option')[3])
        self.click_on(self.find_all('#id_level option')[8])
        self.click_on(self.find('#id_clefs_3'))
        self.click_on(self.find('form button'))
        self.wait.until(lambda _: len(self.find_all('.instrument-row')) == 2)
        self._check_instrument_row_content(1, 'Bass', 'UI+', 'Bass clef')

        self.click_on(self.find_all('#id_size option')[1])
        self.click_on(self.find_all('#id_level option')[5])
        self.click_on(self.find('#id_clefs_0'))
        self.click_on(self.find('#id_clefs_1'))
        self.click_on(self.find('form button'))
        self.wait.until(lambda _: len(self.find_all('.instrument-row')) == 3)
        self._check_instrument_row_content(2, 'Treble', 'I', 'Treble clef, Octave Treble clef')

        self.assertFalse(self.find('#id_name_if_other').is_displayed())
        self.click_on(self.find_all('#id_size option')[4])
        self.click_on(self.find_all('#id_level option')[-1])
        self.click_on(self.find('#id_clefs_0'))
        self.click_on(self.find('#id_clefs_1'))
        self.click_on(self.find('#id_clefs_2'))
        self.click_on(self.find('#id_clefs_3'))
        # Try submitting without required "name if other"
        self.click_on(self.find('form button'))
        time.sleep(1)
        self.assertEqual(3, len(self.find_all('.instrument-row')))

        self.set_value('#id_name_if_other', 'Kazoo')
        self.click_on(self.find('form button'))
        self.wait.until(lambda _: len(self.find_all('.instrument-row')) == 4)
        self._check_instrument_row_content(
            3, 'Kazoo', 'A+', 'Treble clef, Octave Treble clef, Alto clef, Bass clef')

        # Delete instruments

        self.assertEqual(4, self.registration_entry.instruments_bringing.count())
        self.selenium.refresh()
        self.wait.until(lambda _: len(self.find_all('.instrument-row')) == 4)

        self._check_instrument_row_content(0, 'Tenor', 'B', 'Treble clef, Alto clef')
        self._check_instrument_row_content(1, 'Bass', 'UI+', 'Bass clef')
        self._check_instrument_row_content(2, 'Treble', 'I', 'Treble clef, Octave Treble clef')
        self._check_instrument_row_content(
            3, 'Kazoo', 'A+', 'Treble clef, Octave Treble clef, Alto clef, Bass clef')

        self.click_on(self.find('.instrument-row:nth-child(3) .delete-instrument'))
        self.accept_alert()
        self.wait.until(lambda _: len(self.find_all('.instrument-row')) == 3)
        self.assertEqual(3, self.registration_entry.instruments_bringing.count())
        self.assertFalse(
            self.registration_entry.instruments_bringing.filter(
                size=InstrumentChoices.treble).exists())
        self._check_instrument_row_content(0, 'Tenor', 'B', 'Treble clef, Alto clef')
        self._check_instrument_row_content(1, 'Bass', 'UI+', 'Bass clef')
        self._check_instrument_row_content(
            2, 'Kazoo', 'A+', 'Treble clef, Octave Treble clef, Alto clef, Bass clef')

        self.click_on(self.find('.instrument-row:nth-child(1) .delete-instrument'))
        self.accept_alert()
        self.wait.until(lambda _: len(self.find_all('.instrument-row')) == 2)
        self.assertEqual(2, self.registration_entry.instruments_bringing.count())
        self.assertFalse(
            self.registration_entry.instruments_bringing.filter(
                size=InstrumentChoices.tenor).exists())
        self._check_instrument_row_content(0, 'Bass', 'UI+', 'Bass clef')
        self._check_instrument_row_content(
            1, 'Kazoo', 'A+', 'Treble clef, Octave Treble clef, Alto clef, Bass clef')

        self.click_on(self.find('.instrument-row:nth-child(2) .delete-instrument'))
        self.accept_alert()
        self.wait.until(lambda _: len(self.find_all('.instrument-row')) == 1)
        self.assertEqual(1, self.registration_entry.instruments_bringing.count())
        self.assertFalse(
            self.registration_entry.instruments_bringing.filter(
                size=InstrumentChoices.other).exists())
        self._check_instrument_row_content(0, 'Bass', 'UI+', 'Bass clef')

        self.click_on(self.find('.instrument-row:nth-child(1) .delete-instrument'))
        self.accept_alert()
        self.wait.until(lambda _: len(self.find_all('.instrument-row')) == 0)
        self.assertEqual(0, self.registration_entry.instruments_bringing.count())

    def _check_instrument_row_content(self, index: int, size: str, level: str, clefs: str) -> None:
        cells = self.find_all(f'.instrument-row:nth-child({index + 1}) div')
        self.assertEqual(size, cells[0].text)
        self.assertEqual('Level: ' + level, cells[1].text)
        self.assertEqual('Clefs: ' + clefs, cells[2].text)
        self.assertEqual('Delete', cells[3].text)

    def test_no_clefs_selected(self) -> None:
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/instruments'
        )

        self.click_on(self.find_all('#id_size option')[2])
        self.click_on(self.find_all('#id_level option')[1])
        self.click_on(self.find('form button'))
        self.wait.until(lambda _: len(self.find_all('#id_clefs_wrapper .errorlist li')) == 1)
        self.assertFalse(self.find('#id_name_if_other').is_displayed())

    def test_no_clefs_selected_other_size(self) -> None:
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/instruments'
        )

        self.click_on(self.find_all('#id_size option')[-1])
        self.click_on(self.find_all('#id_level option')[1])
        self.set_value('#id_name_if_other', 'Hurdy Gurdy')
        self.click_on(self.find('form button'))
        self.wait.until(lambda _: len(self.find_all('#id_clefs_wrapper .errorlist li')) == 1)
        self.assertTrue(self.find('#id_name_if_other').is_displayed())


class ClassesViewTestCase(_SetUpRegistrationEntry, SeleniumTestCaseBase):
    def test_invalid_no_classes_selected(self) -> None:
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/classes'
        )
        self.click_on(self.find('form button'))

        self.assertEqual(
            'Please specify your class preferences.',
            self.find('.non-field-errors .form-error:first-child').text
        )

#     def test_form_initial_values(self) -> None:
#         self.fail()

#     def test_redirect_on_save(self) -> None:
#         self.fail()

#     # def test_data_persists_after_save(self) -> None:
#     #     self.fail()

#     def test_show_hide_class_descriptions(self) -> None:
#         self.fail()


# class TShirtsViewTestCase(_SetUpRegistrationEntry, SeleniumTestCaseBase):
#     def test_form_initial_values(self) -> None:
#         self.fail()

#     def test_redirect_on_save(self) -> None:
#         self.fail()

    # def test_data_persists_after_save(self) -> None:
    #     self.fail()


_WORK_STUDY_DATA = {
    'first_time_applying': True,
    'alternate_address': 'nreostn',
    'phone_number': '1234',
    'age_if_under_22': '19',
    'is_full_time_student': True,
    'student_school': 'Schooly',
    'student_degree': 'Poke Master',
    'student_graduation_date': '2020',
    'can_arrive_before_sunday_morning': True,
    'earliest_could_arrive': 'Sunday',
    'has_car': True,
    'job_first_choice': WorkStudyJob.hospitality,
    'job_second_choice': WorkStudyJob.copy_crew_auction,
    'interest_in_work_study': 'Worky',
    'other_skills': 'Spam',
    'questions_comments': 'Hi',
}


# def _make_classes(conclave_config: ConclaveRegistrationConfig, num_classes: int) -> None:
#     for i in range(num_classes):
#         Class.objects.create(
#             name=f'Class {i}',
#             period=Period(i % 4 + 1),
#             level=[Level.any],
#             instructor=f'Instructo {i}',
#             description=f'This is Class {i}',
#         )


class PaymentViewSummaryTestCase(_SetUpRegistrationEntry, SeleniumTestCaseBase):
    def setUp(self) -> None:
        super().setUp()

        BasicRegistrationInfo.objects.create(
            registration_entry=self.registration_entry,
            is_first_time_attendee=False,
            buddy_willingness=YesNoMaybe.yes,
            willing_to_help_with_small_jobs=False,
            wants_display_space=False,
            photo_release_auth=True,
            liability_release=True,
            other_info=''
        )
        self.empty_class_choices = RegularProgramClassChoices.objects.create(
            registration_entry=self.registration_entry,
        )

    def test_summary_of_work_study(self) -> None:
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )

        self.assertIn('Applying for a work study position', self.find('#work-study-summary').text)
        self.assertIn('No', self.find('#work-study-summary').text)

        WorkStudyApplication.objects.create(
            registration_entry=self.registration_entry, **_WORK_STUDY_DATA)

        self.selenium.refresh()

        self.assertIn('Applying for a work study position', self.find('#work-study-summary').text)
        self.assertIn('Yes', self.find('#work-study-summary').text)

    def test_summary_of_instruments(self) -> None:
        InstrumentBringing.objects.create(
            registration_entry=self.registration_entry,
            size=InstrumentChoices.bass,
            level=Level.advanced,
            clefs=[Clef.bass]
        )
        InstrumentBringing.objects.create(
            registration_entry=self.registration_entry,
            size=InstrumentChoices.other,
            name_if_other='Whistle',
            level=Level.advanced,
            clefs=[Clef.bass]
        )

        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )
        instruments = self.find_all('#instruments-summary li')
        self.assertEqual(2, len(instruments))
        self.assertEqual('Bass', instruments[0].text)
        self.assertEqual('Whistle', instruments[1].text)

    def test_summary_no_instruments_bringing(self) -> None:
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )
        self.assertEqual(0, len(self.find_all('#instruments-summary li')))
        self.assertEqual(
            'You are not bringing any instruments.', self.find('#no-instruments-message').text
        )

    def test_summary_of_tshirts(self) -> None:
        shirts = TShirts.objects.create(
            registration_entry=self.registration_entry, tshirt1=TShirtSizes.small)

        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )
        tshirts = self.find_all('#tshirt-summary li')
        self.assertEqual(1, len(tshirts))
        self.assertEqual('T-Shirt 1: S', tshirts[0].text)

        shirts.tshirt2 = TShirtSizes.large
        shirts.save()
        self.selenium.refresh()

        tshirts = self.find_all('#tshirt-summary li')
        self.assertEqual(2, len(tshirts))
        self.assertEqual('T-Shirt 1: S', tshirts[0].text)
        self.assertEqual('T-Shirt 2: L', tshirts[1].text)

    def test_summary_no_tshirts(self) -> None:
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )
        self.assertEqual(0, len(self.find_all('#tshirt-summary li')))
        self.assertEqual(
            'No T-Shirts', self.find('#no-tshirts-message').text
        )

    def test_charges_part_time_tuition_and_tshirts(self) -> None:
        self.empty_class_choices.delete()
        RegularProgramClassChoices.objects.create(
            registration_entry=self.registration_entry,
            tuition_option=TuitionOption.part_time
        )
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )

        self.assertEqual(
            'Tuition: Part Time (1 Class)',
            self.find('#tuition-charge-row td:first-child').text
        )
        self.assertEqual('100', self.find('#tuition-charge-row td:last-child').text)

        self.assertEqual('T-Shirts: 0', self.find('#tshirts-charge-row td:first-child').text)
        self.assertEqual('0', self.find('#tshirts-charge-row td:last-child').text)

        self.assertEqual('100', self.find('#total-charges-cell').text)

        shirts = TShirts.objects.create(
            registration_entry=self.registration_entry, tshirt1=TShirtSizes.small)
        self.selenium.refresh()
        self.assertEqual('T-Shirts: 1', self.find('#tshirts-charge-row td:first-child').text)
        self.assertEqual('25', self.find('#tshirts-charge-row td:last-child').text)

        self.assertEqual('125', self.find('#total-charges-cell').text)

        shirts.tshirt2 = TShirtSizes.large
        shirts.save()
        self.selenium.refresh()

        self.assertEqual('T-Shirts: 2', self.find('#tshirts-charge-row td:first-child').text)
        self.assertEqual('50', self.find('#tshirts-charge-row td:last-child').text)

        self.assertEqual('150', self.find('#total-charges-cell').text)

    def test_charges_full_time_tuition_and_tshirts(self) -> None:
        self.empty_class_choices.delete()
        RegularProgramClassChoices.objects.create(
            registration_entry=self.registration_entry,
            tuition_option=TuitionOption.full_time
        )
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )

        self.assertEqual(
            'Tuition: Full Time (2-3 Classes)',
            self.find('#tuition-charge-row td:first-child').text
        )
        self.assertEqual('200', self.find('#tuition-charge-row td:last-child').text)

        self.assertEqual('200', self.find('#total-charges-cell').text)

        shirts = TShirts.objects.create(
            registration_entry=self.registration_entry, tshirt1=TShirtSizes.small)
        self.selenium.refresh()
        self.assertEqual('T-Shirts: 1', self.find('#tshirts-charge-row td:first-child').text)
        self.assertEqual('25', self.find('#tshirts-charge-row td:last-child').text)

        self.assertEqual('225', self.find('#total-charges-cell').text)

        shirts.tshirt2 = TShirtSizes.large
        shirts.save()
        self.selenium.refresh()

        self.assertEqual('T-Shirts: 2', self.find('#tshirts-charge-row td:first-child').text)
        self.assertEqual('50', self.find('#tshirts-charge-row td:last-child').text)

        self.assertEqual('250', self.find('#total-charges-cell').text)

    def test_charges_late_fee(self) -> None:
        self.registration_entry.is_late = True
        self.registration_entry.save()
        self.empty_class_choices.delete()
        RegularProgramClassChoices.objects.create(
            registration_entry=self.registration_entry,
            tuition_option=TuitionOption.full_time,
        )
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )
        self.assertEqual(
            'Late registration', self.find('#late-fee-charge-row td:first-child').text)
        self.assertEqual('25', self.find('#late-fee-charge-row td:last-child').text)

        self.assertEqual('225', self.find('#total-charges-cell').text)


class SubmitPaymentTestCase(_SetUpRegistrationEntry, SeleniumTestCaseBase):
    def setUp(self) -> None:
        super().setUp()

        class_ = Class.objects.create(
            conclave_config=self.conclave_config,
            name='Classy',
            period=Period.first,
            level=[Level.any],
            instructor='Steve',
            description='Wee',
        )
        self.basic_info = BasicRegistrationInfo.objects.create(
            registration_entry=self.registration_entry,
            is_first_time_attendee=False,
            buddy_willingness=YesNoMaybe.yes,
            willing_to_help_with_small_jobs=False,
            wants_display_space=False,
            photo_release_auth=True,
            liability_release=True,
            other_info=''
        )
        self.regular_class_choices = RegularProgramClassChoices.objects.create(
            registration_entry=self.registration_entry,
            period1_choice1=class_,
        )

    def test_submit_payment_no_donation(self) -> None:
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )
        self.set_value('#id_name_on_card', 'Steve the Llama')
        self.set_value('#id_card_number', '4242424242424242')
        self.click_on(self.find_all('#id_expiration_year option')[-1])
        self.set_value('#id_cvc', '111')

        self.click_on(self.find('form button'))
        self.assertEqual('Registration Complete', self.find('#registration-complete-header').text)

        self.registration_entry.refresh_from_db()
        self.assertNotEqual('', self.registration_entry.payment_info.stripe_payment_method_id)
        self.assertEqual(0, self.registration_entry.payment_info.donation)

    def test_submit_payment_with_donation(self) -> None:
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )
        self.set_value('#id_donation', '42')
        self.set_value('#id_name_on_card', 'Steve the Llama')
        self.set_value('#id_card_number', '4242424242424242')
        self.click_on(self.find_all('#id_expiration_year option')[-1])
        self.set_value('#id_cvc', '111')

        self.click_on(self.find('form button'))
        self.assertEqual('Registration Complete', self.find('#registration-complete-header').text)

        self.registration_entry.refresh_from_db()
        self.assertNotEqual('', self.registration_entry.payment_info.stripe_payment_method_id)
        self.assertEqual(42, self.registration_entry.payment_info.donation)

    def test_stripe_card_error(self) -> None:
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )
        self.set_value('#id_donation', '42')
        self.set_value('#id_name_on_card', 'Steve the Llama')
        self.set_value('#id_card_number', '3331023948438710')
        self.click_on(self.find_all('#id_expiration_year option')[-1])
        self.set_value('#id_cvc', '111')

        self.click_on(self.find('form button'))
        self.assertEqual('Your card number is incorrect.', self.find('#stripe-error').text)

        self.registration_entry.refresh_from_db()
        self.assertFalse(hasattr(self.registration_entry, 'payment_info'))

    def test_regular_flow_basic_info_not_finished(self) -> None:
        self.basic_info.delete()
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )
        missing_sections = self.find_all('#missing-sections-msg li')
        self.assertEqual(1, len(missing_sections))
        self.assertIn('Misc Info', missing_sections[0].text)
        self.assertFalse(self.exists('#summary'))
        self.assertFalse(self.exists('#conclave-go-to-payment-form'))

    def test_regular_flow_class_selection_not_finished(self) -> None:
        self.regular_class_choices.delete()
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )
        missing_sections = self.find_all('#missing-sections-msg li')
        self.assertEqual(1, len(missing_sections))
        self.assertIn('Classes', missing_sections[0].text)
        self.assertFalse(self.exists('#summary'))
        self.assertFalse(self.exists('#conclave-go-to-payment-form'))

    def test_regular_flow_no_required_sections_finished(self) -> None:
        self.basic_info.delete()
        self.regular_class_choices.delete()
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )
        missing_sections = self.find_all('#missing-sections-msg li')
        self.assertEqual(2, len(missing_sections))
        self.assertIn('Misc Info', missing_sections[0].text)
        self.assertIn('Classes', missing_sections[1].text)
        self.assertFalse(self.exists('#summary'))
        self.assertFalse(self.exists('#conclave-go-to-payment-form'))