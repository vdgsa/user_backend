import time
import unittest

from django.test.testcases import TestCase
from django.urls import reverse

from vdgsa_backend.accounts.models import MembershipSubscription, MembershipType, User
from vdgsa_backend.conclave_registration.models import (
    ADVANCED_PROGRAMS, TSHIRT_SIZES, AdditionalRegistrationInfo, BeginnerInstrumentInfo, Class,
    Clef, ConclaveRegistrationConfig, InstrumentBringing, InstrumentChoices, Level, PaymentInfo,
    Period, Program, RegistrationEntry, RegistrationPhase, RegularProgramClassChoices, TShirts,
    WorkStudyApplication, WorkStudyJob, YesNo, YesNoMaybe
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
        self.assertIn(
            f'Conclave {self.conclave_config.year} Registration',
            self.find('#registration-landing-header').text
        )
        self.click_on(self.find_all('#id_program option')[1])

        button = self.find('form button')
        self.assertEqual('Start Registration', button.text)
        self.click_on(button)

        self.assertEqual(
            'Instruments', self.find('[data-testid=registration_section_header]').text)

        query = RegistrationEntry.objects.all()
        self.assertEqual(1, query.count())

        reg_entry = query.first()
        assert reg_entry is not None
        self.assertEqual(Program.regular, reg_entry.program)
        self.assertEqual(reg_entry.conclave_config, self.conclave_config)
        self.assertEqual(reg_entry.user, self.user)

    def test_select_faculty_registration_with_password(self) -> None:
        password = 'nrsoietanrsit'
        self.conclave_config.faculty_registration_password = password
        self.conclave_config.save()
        self.login_as(self.user, dest_url=f'/conclave/{self.conclave_config.pk}/register')
        self.assertFalse(self.find('#id_faculty_registration_password').is_displayed())
        self.click_on(self.find_all('#id_program option')[-1])
        self.set_value('#id_faculty_registration_password', password)
        self.click_on(self.find('form button'))
        self.assertEqual(
            'Additional Info', self.find('[data-testid=registration_section_header]').text)

        query = RegistrationEntry.objects.all()
        self.assertEqual(1, query.count())

        reg_entry = query.first()
        assert reg_entry is not None
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
        self.assertEqual(
            'Instruments', self.find('[data-testid=registration_section_header]').text)

    def test_membership_out_of_date_message(self) -> None:
        assert self.user is not None
        assert self.user.subscription is not None
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

        self.click_on(self.find_all('#id_program option')[1])
        button = self.find('form button')
        self.assertEqual('Start Registration', button.text)
        self.click_on(button)

        self.assertEqual(
            'Instruments', self.find('[data-testid=registration_section_header]').text)

        query = RegistrationEntry.objects.all()
        self.assertEqual(1, query.count())

        reg_entry = query.first()
        assert reg_entry is not None
        self.assertEqual(Program.regular, reg_entry.program)
        self.assertEqual(reg_entry.conclave_config, self.conclave_config)
        self.assertEqual(reg_entry.user, user)

    def test_late_registration_message(self) -> None:
        self.conclave_config.phase = RegistrationPhase.late
        self.conclave_config.save()

        self.login_as(self.user, dest_url=f'/conclave/{self.conclave_config.pk}/register')
        self.assertIn('(Late)', self.find('#registration-landing-header').text)

        self.click_on(self.find_all('#id_program option')[1])
        button = self.find('form button')
        self.assertEqual('Start Registration', button.text)
        self.click_on(button)

        self.assertEqual(
            'Instruments', self.find('[data-testid=registration_section_header]').text)

        query = RegistrationEntry.objects.all()
        self.assertEqual(1, query.count())

        reg_entry = query.first()
        assert reg_entry is not None
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

        self.login_as(self.user, dest_url=f'/conclave/register/{reg_entry.pk}/additional_info')
        self.assertIn('closed', self.find('[data-testid=registration_closed_message]').text)
        self.assertFalse(self.exists('[data-testid=registration_section_header]'))

    def test_conclave_team_start_closed_registration_for_self(self) -> None:
        self.conclave_config.phase = RegistrationPhase.closed
        self.conclave_config.save()

        user = self.make_conclave_team()
        self.login_as(user, dest_url=f'/conclave/{self.conclave_config.pk}/register')

        self.click_on(self.find_all('#id_program option')[1])
        button = self.find('form button')
        self.assertEqual('Start Registration', button.text)
        self.click_on(button)

        self.assertEqual(
            'Instruments', self.find('[data-testid=registration_section_header]').text)

        query = RegistrationEntry.objects.all()
        self.assertEqual(1, query.count())

        reg_entry = query.first()
        assert reg_entry is not None
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
        self.login_as(user, dest_url=f'/conclave/register/{reg_entry.pk}/additional_info')
        self.assertEqual(
            'Additional Info', self.find('[data-testid=registration_section_header]').text)

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
        self.assertFalse(self.exists('#start-over-link'))

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
        self.login_as(user, dest_url=f'/conclave/register/{reg_entry.pk}/additional_info')
        self.assertEqual(
            'Additional Info', self.find('[data-testid=registration_section_header]').text)

    @unittest.skip('')
    def test_user_cannot_reset_finalized_registration(self) -> None:
        self.fail()

    @unittest.skip('')
    def test_conclave_team_can_reset_finalized_registration(self) -> None:
        self.fail()


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
        assert self.user is not None
        assert self.user.subscription is not None
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
    #     reverse('conclave-reg-landing', kwargs={'conclave_config_pk': self.conclave_config.pk})
    #     )
    #     self.assertEqual(403, response.status_code)


class _SetUpRegistrationEntry(_SetUp):
    registration_entry: RegistrationEntry

    def setUp(self) -> None:
        super().setUp()

        self.registration_entry = RegistrationEntry.objects.create(
            conclave_config=self.conclave_config,
            user=self.user,
            program=Program.regular,
        )


# class RegistrationBaseViewTestCases(_SetUpRegistrationEntry, SeleniumTestCaseBase):
#     def test_sidebar_navigation_regular_flow(self) -> None:
#         self.fail()


# class AdditionalInfoViewTestCase(_SetUpRegistrationEntry, SeleniumTestCaseBase):
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
    pass
    # Currently, it's allowed to not select any classes
    # def test_invalid_no_classes_selected(self) -> None:
    #     self.login_as(
    #         self.user,
    #         dest_url=f'/conclave/register/{self.registration_entry.pk}/classes'
    #     )
    #     self.click_on(self.find('form button'))

    #     self.assertEqual(
    #         'Please specify your class preferences.',
    #         self.find('.non-field-errors .form-error:first-child').text
    #     )

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
    'nickname_and_pronouns': '',
    'phone_number': '1111111111',
    'can_receive_texts_at_phone_number': YesNo.yes,
    'home_timezone': 'EDT',
    'other_timezone': '',
    'has_been_to_conclave': YesNo.yes,
    'has_done_work_study': YesNo.yes,
    'student_info': '',
    'job_preferences': [WorkStudyJob.tech_support],
    'relevant_job_experience': 'noristearst',
    'other_skills': '',
    'other_info': '',
}


def _make_classes(conclave_config: ConclaveRegistrationConfig, num_classes: int) -> None:
    for i in range(num_classes):
        Class.objects.create(
            conclave_config=conclave_config,
            name=f'Class {i}',
            period=Period(i % 4 + 1),
            level=Level.any.label,
            instructor=f'Instructo {i}',
            description=f'This is Class {i}',
        )


class PaymentViewSummaryTestCase(_SetUpRegistrationEntry, SeleniumTestCaseBase):
    def setUp(self) -> None:
        super().setUp()

        AdditionalRegistrationInfo.objects.create(
            registration_entry=self.registration_entry,
            attended_conclave_before=YesNo.yes,
            buddy_willingness=YesNoMaybe.yes,
            # willing_to_help_with_small_jobs=False,
            wants_display_space=YesNo.yes,
            photo_release_auth=YesNo.yes,
            archival_video_release=True,
            # liability_release=True,
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

        self.assertIn('Applying for a work-study position', self.find('#work-study-summary').text)
        self.assertIn('No', self.find('#work-study-summary').text)

        WorkStudyApplication.objects.create(
            registration_entry=self.registration_entry, **_WORK_STUDY_DATA)

        self.selenium.refresh()

        self.assertIn('Applying for a work-study position', self.find('#work-study-summary').text)
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

    def test_summary_no_classes(self) -> None:
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )
        self.assertEqual(0, len(self.find_all('#classes-summary li')))
        self.assertEqual(
            'No classes selected.', self.find('#no-classes-message').text
        )

    def test_summary_of_tshirts(self) -> None:
        shirt1 = TSHIRT_SIZES[2]
        shirt2 = TSHIRT_SIZES[-1]
        shirts = TShirts.objects.create(registration_entry=self.registration_entry, tshirt1=shirt1)

        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )
        tshirts = self.find_all('#tshirt-summary li')
        self.assertEqual(1, len(tshirts))
        self.assertEqual(f'T-Shirt 1: {shirt1}', tshirts[0].text)

        shirts.tshirt2 = shirt2
        shirts.save()
        self.selenium.refresh()

        tshirts = self.find_all('#tshirt-summary li')
        self.assertEqual(2, len(tshirts))
        self.assertEqual(f'T-Shirt 1: {shirt1}', tshirts[0].text)
        self.assertEqual(f'T-Shirt 2: {shirt2}', tshirts[1].text)

    def test_summary_no_tshirts(self) -> None:
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )
        self.assertEqual(0, len(self.find_all('#tshirt-summary li')))
        self.assertEqual(
            'No T-Shirts', self.find('#no-tshirts-message').text
        )


class ChargesTestCase(_SetUpRegistrationEntry, SeleniumTestCaseBase):
    def setUp(self) -> None:
        super().setUp()

        _make_classes(self.conclave_config, 4)

        AdditionalRegistrationInfo.objects.create(
            registration_entry=self.registration_entry,
            attended_conclave_before=YesNo.yes,
            buddy_willingness=YesNoMaybe.yes,
            # willing_to_help_with_small_jobs=False,
            wants_display_space=YesNo.yes,
            photo_release_auth=YesNo.yes,
            archival_video_release=True,
            # liability_release=True,
            other_info=''
        )

    def test_charges_one_class_regular_tuition_and_tshirts_no_donation(self) -> None:
        RegularProgramClassChoices.objects.create(
            registration_entry=self.registration_entry,
            period1_choice1=self.conclave_config.classes.first()
        )
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )

        self.assertEqual(
            'Classes Selected: 1',
            self.find('#tuition-charge-row td:first-child').text
        )
        self.assertEqual('100', self.find('#tuition-charge-row td:last-child').text)

        self.assertEqual('T-Shirts: 0', self.find('#tshirts-charge-row td:first-child').text)
        self.assertEqual('0', self.find('#tshirts-charge-row td:last-child').text)

        self.assertEqual('Donation', self.find('#donation-charge-row td:first-child').text)
        self.assertEqual('0', self.find('#donation-charge-row td:last-child').text)

        self.assertEqual('100', self.find('#total-charges-cell').text)

        shirts = TShirts.objects.create(
            registration_entry=self.registration_entry, tshirt1=TSHIRT_SIZES[0])
        self.selenium.refresh()
        self.assertEqual('T-Shirts: 1', self.find('#tshirts-charge-row td:first-child').text)
        self.assertEqual('25', self.find('#tshirts-charge-row td:last-child').text)

        self.assertEqual('125', self.find('#total-charges-cell').text)

        shirts.tshirt2 = TSHIRT_SIZES[4]
        shirts.save()
        self.selenium.refresh()

        self.assertEqual('T-Shirts: 2', self.find('#tshirts-charge-row td:first-child').text)
        self.assertEqual('50', self.find('#tshirts-charge-row td:last-child').text)

        self.assertEqual('150', self.find('#total-charges-cell').text)

    def test_charges_three_classes_regular_tuition_and_tshirts(self) -> None:
        RegularProgramClassChoices.objects.create(
            registration_entry=self.registration_entry,
            period1_choice1=self.conclave_config.classes.all()[0],
            period2_choice1=self.conclave_config.classes.all()[1],
            period4_choice1=self.conclave_config.classes.all()[3],
        )
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )

        self.assertEqual(
            'Classes Selected: 3',
            self.find('#tuition-charge-row td:first-child').text
        )
        self.assertEqual('200', self.find('#tuition-charge-row td:last-child').text)

        self.assertEqual('200', self.find('#total-charges-cell').text)

        shirts = TShirts.objects.create(
            registration_entry=self.registration_entry, tshirt1=TSHIRT_SIZES[1])
        self.selenium.refresh()
        self.assertEqual('T-Shirts: 1', self.find('#tshirts-charge-row td:first-child').text)
        self.assertEqual('25', self.find('#tshirts-charge-row td:last-child').text)

        self.assertEqual('225', self.find('#total-charges-cell').text)

        shirts.tshirt2 = TSHIRT_SIZES[-2]
        shirts.save()
        self.selenium.refresh()

        self.assertEqual('T-Shirts: 2', self.find('#tshirts-charge-row td:first-child').text)
        self.assertEqual('50', self.find('#tshirts-charge-row td:last-child').text)

        self.assertEqual('250', self.find('#total-charges-cell').text)

    def test_charges_late_fee(self) -> None:
        self.registration_entry.is_late = True
        self.registration_entry.save()
        RegularProgramClassChoices.objects.create(registration_entry=self.registration_entry)
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )
        self.assertEqual(
            'Late registration', self.find('#late-fee-charge-row td:first-child').text)
        self.assertEqual('25', self.find('#late-fee-charge-row td:last-child').text)

        self.assertEqual('125', self.find('#total-charges-cell').text)

    def test_no_classes_regular_tuition(self) -> None:
        RegularProgramClassChoices.objects.create(registration_entry=self.registration_entry)
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )

        self.assertEqual(
            'Classes Selected: 0',
            self.find('#tuition-charge-row td:first-child').text
        )
        self.assertEqual('100', self.find('#tuition-charge-row td:last-child').text)
        self.assertEqual('100', self.find('#total-charges-cell').text)

    def test_two_classes_regular_tuition(self) -> None:
        RegularProgramClassChoices.objects.create(
            registration_entry=self.registration_entry,
            period2_choice1=self.conclave_config.classes.all()[1],
            period3_choice1=self.conclave_config.classes.all()[2],
        )
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )

        self.assertEqual(
            'Classes Selected: 2',
            self.find('#tuition-charge-row td:first-child').text
        )
        self.assertEqual('200', self.find('#tuition-charge-row td:last-child').text)
        self.assertEqual('200', self.find('#total-charges-cell').text)

    def test_four_classes_regular_tuition(self) -> None:
        RegularProgramClassChoices.objects.create(
            registration_entry=self.registration_entry,
            period1_choice1=self.conclave_config.classes.all()[0],
            period2_choice1=self.conclave_config.classes.all()[1],
            period3_choice1=self.conclave_config.classes.all()[2],
            period4_choice1=self.conclave_config.classes.all()[3],
        )
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )

        self.assertEqual(
            'Classes Selected: 4',
            self.find('#tuition-charge-row td:first-child').text
        )
        self.assertEqual('200', self.find('#tuition-charge-row td:last-child').text)
        self.assertEqual('200', self.find('#total-charges-cell').text)

    def test_no_classes_beginner_tuition(self) -> None:
        RegularProgramClassChoices.objects.create(registration_entry=self.registration_entry)
        self.registration_entry.program = Program.beginners
        self.registration_entry.save()
        BeginnerInstrumentInfo.objects.create(
            registration_entry=self.registration_entry,
            needs_instrument=YesNo.yes,
        )
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )

        self.assertEqual(
            'Add-on Classes Selected: 0',
            self.find('#tuition-charge-row td:first-child').text
        )
        self.assertEqual('0', self.find('#tuition-charge-row td:last-child').text)
        self.assertEqual('0', self.find('#total-charges-cell').text)

    def test_one_class_beginner_tuition(self) -> None:
        self.registration_entry.program = Program.beginners
        self.registration_entry.save()
        BeginnerInstrumentInfo.objects.create(
            registration_entry=self.registration_entry,
            needs_instrument=YesNo.yes,
        )
        RegularProgramClassChoices.objects.create(
            registration_entry=self.registration_entry,
            period2_choice1=self.conclave_config.classes.all()[1],
        )
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )

        self.assertEqual(
            'Add-on Classes Selected: 1',
            self.find('#tuition-charge-row td:first-child').text
        )
        self.assertEqual('100', self.find('#tuition-charge-row td:last-child').text)
        self.assertEqual('100', self.find('#total-charges-cell').text)

    def test_no_classes_advanced_programs(self) -> None:
        RegularProgramClassChoices.objects.create(registration_entry=self.registration_entry)
        for program in ADVANCED_PROGRAMS:
            self.registration_entry.program = program
            self.registration_entry.save()
            self.login_as(
                self.user,
                dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
            )

            self.assertEqual(
                'Add-on Classes Selected: 0',
                self.find('#tuition-charge-row td:first-child').text
            )
            self.assertEqual('100', self.find('#tuition-charge-row td:last-child').text)
            self.assertEqual('100', self.find('#total-charges-cell').text)

            self.selenium.delete_all_cookies()

    def test_one_class_advanced_programs(self) -> None:
        RegularProgramClassChoices.objects.create(
            registration_entry=self.registration_entry,
            period2_choice1=self.conclave_config.classes.all()[1],
        )
        for program in ADVANCED_PROGRAMS:
            self.registration_entry.program = program
            self.registration_entry.save()
            self.login_as(
                self.user,
                dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
            )

            self.assertEqual(
                'Add-on Classes Selected: 1',
                self.find('#tuition-charge-row td:first-child').text
            )
            self.assertEqual('200', self.find('#tuition-charge-row td:last-child').text)
            self.assertEqual('200', self.find('#total-charges-cell').text)

            self.selenium.delete_all_cookies()

    def test_two_classes_advanced_programs(self) -> None:
        RegularProgramClassChoices.objects.create(
            registration_entry=self.registration_entry,
            period1_choice1=self.conclave_config.classes.all()[0],
            period3_choice1=self.conclave_config.classes.all()[2],
        )
        for program in ADVANCED_PROGRAMS:
            self.registration_entry.program = program
            self.registration_entry.save()
            self.login_as(
                self.user,
                dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
            )

            self.assertEqual(
                'Add-on Classes Selected: 2',
                self.find('#tuition-charge-row td:first-child').text
            )
            self.assertEqual('200', self.find('#tuition-charge-row td:last-child').text)
            self.assertEqual('200', self.find('#total-charges-cell').text)

            self.selenium.delete_all_cookies()

    def test_tuition_and_donation(self) -> None:
        RegularProgramClassChoices.objects.create(registration_entry=self.registration_entry)
        TShirts.objects.create(registration_entry=self.registration_entry, donation=43)
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )

        self.assertEqual('100', self.find('#tuition-charge-row td:last-child').text)

        self.assertEqual('Donation', self.find('#donation-charge-row td:first-child').text)
        self.assertEqual('43', self.find('#donation-charge-row td:last-child').text)

        self.assertEqual('143', self.find('#total-charges-cell').text)


class SubmitPaymentTestCase(_SetUpRegistrationEntry, SeleniumTestCaseBase):
    def setUp(self) -> None:
        super().setUp()

        class_ = Class.objects.create(
            conclave_config=self.conclave_config,
            name='Classy',
            period=Period.first,
            level=Level.any.label,
            instructor='Steve',
            description='Wee',
        )
        self.additional_info = AdditionalRegistrationInfo.objects.create(
            registration_entry=self.registration_entry,
            attended_conclave_before=YesNo.yes,
            buddy_willingness=YesNoMaybe.yes,
            # willing_to_help_with_small_jobs=False,
            wants_display_space=YesNo.yes,
            photo_release_auth=YesNo.yes,
            archival_video_release=True,
            # liability_release=True,
            other_info=''
        )
        self.regular_class_choices = RegularProgramClassChoices.objects.create(
            registration_entry=self.registration_entry,
            period1_choice1=class_,
        )

    def test_submit_payment(self) -> None:
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )
        self.set_value('#id_name_on_card', 'Steve the Llama')
        self.set_value('#id_card_number', '4242424242424242')
        self.click_on(self.find_all('#id_expiration_year option')[-1])
        self.set_value('#id_cvc', '111')

        self.click_on(self.find('form button'))
        self.assertEqual('Registration Complete!', self.find('#registration-complete-header').text)

        self.registration_entry.refresh_from_db()
        self.assertNotEqual('', self.registration_entry.payment_info.stripe_payment_method_id)

    def test_stripe_card_error(self) -> None:
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )
        self.set_value('#id_name_on_card', 'Steve the Llama')
        self.set_value('#id_card_number', '3331023948438710')
        self.click_on(self.find_all('#id_expiration_year option')[-1])
        self.set_value('#id_cvc', '111')

        self.click_on(self.find('form button'))
        self.assertEqual('Your card number is incorrect.', self.find('#stripe-error').text)

        self.registration_entry.refresh_from_db()
        self.assertFalse(hasattr(self.registration_entry, 'payment_info'))

    def test_regular_flow_additional_info_not_finished(self) -> None:
        self.additional_info.delete()
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )
        missing_sections = self.find_all('#missing-sections-msg li')
        self.assertEqual(1, len(missing_sections))
        self.assertIn('Additional Info', missing_sections[0].text)
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
        self.additional_info.delete()
        self.regular_class_choices.delete()
        self.login_as(
            self.user,
            dest_url=f'/conclave/register/{self.registration_entry.pk}/payment'
        )
        missing_sections = self.find_all('#missing-sections-msg li')
        self.assertEqual(2, len(missing_sections))
        self.assertIn('Classes', missing_sections[0].text)
        self.assertIn('Additional Info', missing_sections[1].text)
        self.assertFalse(self.exists('#summary'))
        self.assertFalse(self.exists('#conclave-go-to-payment-form'))
