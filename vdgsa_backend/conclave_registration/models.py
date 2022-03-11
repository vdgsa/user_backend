from __future__ import annotations

from typing import Any, Final, TypedDict

from django.contrib.postgres.fields.array import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property

from vdgsa_backend.accounts.models import User


class RegistrationPhase(models.TextChoices):
    unpublished = 'unpublished'
    open = 'open'
    late = 'late', 'Late Registration'
    closed = 'closed'


class ConclaveRegistrationConfig(models.Model):
    year = models.IntegerField(unique=True)
    phase = models.CharField(
        max_length=50,
        choices=RegistrationPhase.choices,
        default=RegistrationPhase.unpublished
    )
    faculty_registration_password = models.CharField(max_length=50, blank=True)

    liability_release_text = models.TextField(blank=True)
    archival_video_release_text = models.TextField(blank=True)
    photo_release_text = models.TextField(blank=True)

    first_period_time_label = models.CharField(max_length=255, blank=True)
    second_period_time_label = models.CharField(max_length=255, blank=True)
    third_period_time_label = models.CharField(max_length=255, blank=True)
    fourth_period_time_label = models.CharField(max_length=255, blank=True)

    # Markdown text to go at the beginning of the housing form.
    housing_form_top_markdown = models.TextField(blank=True)

    arrival_date_options = models.TextField(blank=True)
    departure_date_options = models.TextField(blank=True)
    # Markdown text to go in the housing form just before the arrival/departure fields.
    housing_form_pre_arrival_markdown = models.TextField(blank=True)

    tshirt_image_url = models.URLField(blank=True)

    # Fees and such
    regular_tuition = models.IntegerField(blank=True, default=0)
    part_time_tuition = models.IntegerField(blank=True, default=0)
    consort_coop_tuition = models.IntegerField(blank=True, default=0)
    seasoned_players_tuition = models.IntegerField(blank=True, default=0)
    non_playing_attendee_fee = models.IntegerField(blank=True, default=0)

    beginners_extra_class_fee = models.IntegerField(blank=True, default=0)
    consort_coop_one_extra_class_fee = models.IntegerField(blank=True, default=0)
    consort_coop_two_extra_classes_fee = models.IntegerField(blank=True, default=0)
    seasoned_players_extra_class_fee = models.IntegerField(blank=True, default=0)

    single_room_cost = models.IntegerField(blank=True, default=0)
    double_room_cost = models.IntegerField(blank=True, default=0)
    banquet_guest_fee = models.IntegerField(blank=True, default=0)

    tshirt_price = models.IntegerField(blank=True, default=25)
    late_registration_fee = models.IntegerField(blank=True, default=0)

    work_study_scholarship_amount = models.IntegerField(blank=True, default=0)
    housing_subsidy_amount = models.IntegerField(blank=True, default=150)
    canadian_discount_percent = models.IntegerField(blank=True, default=5)

    @property
    def is_open(self) -> bool:
        return self.phase in [RegistrationPhase.open, RegistrationPhase.late]

    # classes is the reverse lookup of a foreign key defined in Class
    # registration_entries is the reverse lookup of a foreign key defined in RegistrationEntry


class Period(models.IntegerChoices):
    first = 1, '1st Period'
    second = 2, '2nd Period'
    third = 3, '3rd Period'
    fourth = 4, '4th Period'


class Level(models.TextChoices):
    any = 'Any'
    beginner = 'B', 'B'
    beginner_plus = 'B+', 'B+'
    lower_intermediate = 'LI', 'LI'
    lower_intermediate_plus = 'LI+', 'LI+'
    intermediate = 'I', 'I'
    intermediate_plus = 'I+', 'I+'
    upper_intermediate = 'UI', 'UI'
    upper_intermediate_plus = 'UI+', 'UI+'
    advanced = 'A', 'A'
    advanced_plus = 'A+', 'A+'


LEVEL_ORDERING: Final = dict((level, i) for i, level in enumerate(Level))


class Class(models.Model):
    class Meta:
        unique_together = ('name', 'period')
        order_with_respect_to = 'conclave_config'

    conclave_config = models.ForeignKey(
        ConclaveRegistrationConfig,
        related_name='classes',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    period = models.IntegerField(choices=Period.choices)
    level = models.CharField(max_length=255)
    instructor = models.CharField(max_length=255)
    description = models.TextField()
    notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return f'{self.instructor} | {self.name} | {self.level}'


def get_classes_by_period(conclave_config_pk: int) -> dict[int, list[Class]]:
    classes_by_period: dict[int, list[Class]] = {
        Period.first: [],
        Period.second: [],
        Period.third: [],
        Period.fourth: []
    }
    for class_ in Class.objects.filter(conclave_config=conclave_config_pk):
        classes_by_period[class_.period].append(class_)

    return classes_by_period


# =================================================================================================


# We use this instead of a bool when we want to have "yes/no" radio buttons.
class YesNo(models.TextChoices):
    yes = 'yes'
    no = 'no'


class YesNoMaybe(models.TextChoices):
    yes = 'yes'
    no = 'no'
    maybe = 'maybe'


class Program(models.TextChoices):
    regular = 'regular', 'Regular Curriculum'
    part_time = 'part_time', 'Part-Time Curriculum (1 class + optional freebie)'
    beginners = 'beginners', 'Introduction to the Viol (free)'
    consort_coop = 'consort_coop', 'Consort Cooperative'
    seasoned_players = 'seasoned_players', 'Seasoned Players'
    advanced_projects = 'advanced_projects', 'Advanced Projects'
    faculty_guest_other = 'faculty_guest_other', 'Faculty'
    non_playing_attendee = 'non_playing_attendee', 'Non-Playing Attendee'


BEGINNER_PROGRAMS = [Program.beginners]
FLEXIBLE_CLASS_SELECTION_PROGRAMS = [
    Program.part_time,
    Program.seasoned_players,
    Program.advanced_projects,
]
NO_CLASS_PROGRAMS = [
    Program.faculty_guest_other,
    Program.non_playing_attendee,
]


class RegistrationEntry(models.Model):
    class Meta:
        unique_together = ('conclave_config', 'user')

    conclave_config = models.ForeignKey(
        ConclaveRegistrationConfig,
        related_name='registration_entries',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    program = models.CharField(max_length=50, choices=Program.choices)
    is_late = models.BooleanField(blank=True, default=False)

    @property
    def class_selection_is_required(self) -> bool:
        """
        Returns True if the registrant is required to complete the
        class selection form. Note that this includes programs where
        class selections are add-ons. For example, Seasoned Players
        registrants must complete the class selection form even if
        they choose "No class" for all periods.
        Returns False for programs such as faculty/guest/other or
        non-playing attendee that will never select classes using
        the regular class selection page.
        """
        return self.program not in NO_CLASS_PROGRAMS

    @property
    def uses_flexible_class_selection(self) -> bool:
        return self.program in FLEXIBLE_CLASS_SELECTION_PROGRAMS

    @property
    def is_applying_for_work_study(self) -> bool:
        return (
            hasattr(self, 'work_study')
            and self.work_study.wants_work_study == YesNo.yes
        )

    @property
    def is_finalized(self) -> bool:
        return self.payment_info is not None and self.payment_info.stripe_payment_method_id != ''


class AdditionalRegistrationInfo(models.Model):
    registration_entry = models.OneToOneField(
        RegistrationEntry,
        on_delete=models.CASCADE,
        related_name='additional_info'
    )

    phone = models.CharField(max_length=30)
    include_in_whos_coming_to_conclave_list = models.TextField(choices=YesNo.choices)

    attended_conclave_before = models.TextField(choices=YesNo.choices)
    buddy_willingness = models.TextField(choices=YesNoMaybe.choices, blank=True)
    # willing_to_help_with_small_jobs = models.BooleanField(blank=True)
    wants_display_space = models.TextField(choices=YesNo.choices)

    liability_release = models.BooleanField()
    archival_video_release = models.BooleanField()
    photo_release_auth = models.TextField(choices=YesNo.choices)

    other_info = models.TextField(blank=True)

    def clean(self) -> None:
        super().clean()
        if self.attended_conclave_before == YesNo.yes and not self.buddy_willingness:
            raise ValidationError({'buddy_willingness': 'This field is required.'})


class WorkStudyJob(models.TextChoices):
    google_drive_file_organizing = (
        'google_drive_file_organizing',
        'Collecting and organizing files on DropBox and Google Drive (before Conclave)',
    )
    video_editing = (
        'video_editing',
        'Video editing (before Conclave)',
    )
    assist_music_director_before_conclave = (
        'assist_music_director_before_conclave',
        'Assisting the music director (before Conclave)',
    )
    auction_prep_before_conclave = (
        'auction_prep_before_conclave',
        'Auction preparation: collecting photos, writing descriptions of '
        'items (mostly in the few days before Conclave)',
    )
    auction_prep_during_conclave = (
        'auction_prep_during_conclave',
        'Auction preparation: collecting photos, writing descriptions of '
        'items (mostly Sun-Tues during Conclave)',
    )
    social_event_helper = (
        'social_event_helper',
        'Social event helpers '
        '(specific times, e.g. lunchtime, ice cream social, Conclave banquet)',
    )
    tech_support = (
        'tech_support',
        'Answering tech-support type questions, like Zoom help, accessing YouTube, '
        'downloading files, etc. (specific shifts during Conclave)',
    )
    auction_event_helper = (
        'auction_event_helper',
        'Auction event helpers (during the Conclave auction)',
    )
    assist_music_director_during_conclave = (
        'assist_music_director_during_conclave',
        'Assisting the music director (during Conclave)',
    )


class WorkStudyApplication(models.Model):
    registration_entry = models.OneToOneField(
        RegistrationEntry,
        on_delete=models.CASCADE,
        related_name='work_study'
    )

    wants_work_study = models.TextField(choices=YesNo.choices, blank=False, default='')

    nickname_and_pronouns = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=50)
    can_receive_texts_at_phone_number = models.TextField(choices=YesNo.choices)

    has_been_to_conclave = models.TextField(choices=YesNo.choices)
    has_done_work_study = models.TextField(choices=YesNo.choices)

    student_info = models.TextField(blank=True)

    job_preferences = ArrayField(
        models.CharField(max_length=100, choices=WorkStudyJob.choices),
        default=list
    )
    relevant_job_experience = models.TextField()

    other_skills = models.TextField(blank=True)
    other_info = models.TextField(blank=True)

    def full_clean(self, *args: Any, **kwargs: Any) -> None:
        # If the user doesn't want to apply for work study, don't perform
        # any other validation.
        if self.wants_work_study == YesNo.no:
            pass
        else:
            super().full_clean(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if len(self.job_preferences) < 2:
            raise ValidationError({'job_preferences': 'Please choose at least two options.'})


class Clef(models.TextChoices):
    treble = 'treble', 'Treble clef'
    octave_treble = 'octave_treble', 'Octave Treble clef'
    alto = 'alto', 'Alto clef'
    bass = 'bass', 'Bass clef'


class InstrumentChoices(models.TextChoices):
    treble = 'treble'
    tenor = 'tenor'
    bass = 'bass', '6-string Bass'
    bass_7_string = 'bass_7_string', '7-string Bass'
    other = 'other', 'Other Instrument or Rennaissance Viol'


class InstrumentPurpose(models.TextChoices):
    bringing_for_self = 'bringing_for_self', "I'm bringing this instrument for myself"
    willing_to_loan = 'willing_to_loan', "I'm willing to loan this instrument to someone else"
    wants_to_borrow = 'wants_to_borrow', "I need to borrow this instrument"


class InstrumentBringing(models.Model):
    class Meta:
        order_with_respect_to = 'registration_entry'

    registration_entry = models.ForeignKey(
        RegistrationEntry,
        on_delete=models.CASCADE,
        related_name='instruments_bringing',
    )

    size = models.CharField(max_length=100, choices=InstrumentChoices.choices)
    name_if_other = models.CharField(max_length=100, blank=True)
    level = models.TextField(choices=Level.choices[1:])
    clefs = ArrayField(models.CharField(max_length=50, choices=Clef.choices))
    purpose = models.CharField(max_length=100, choices=InstrumentPurpose.choices)

    comments = models.TextField(blank=True)

    def clean(self) -> None:
        super().clean()
        if self.size == InstrumentChoices.other and not self.name_if_other:
            raise ValidationError({'name_if_other': 'This field is required'})

    def __str__(self) -> str:
        if self.size == InstrumentChoices.other:
            return self.name_if_other

        return InstrumentChoices(self.size).label


class BeginnerInstrumentInfo(models.Model):
    registration_entry = models.OneToOneField(
        RegistrationEntry,
        on_delete=models.CASCADE,
        related_name='beginner_instruments',
    )

    needs_instrument = models.TextField(choices=YesNo.choices)
    instrument_bringing = models.TextField(
        blank=True,
        choices=InstrumentChoices.choices[:-1]  # Don't include "other"
    )

    def clean(self) -> None:
        if self.needs_instrument == YesNo.no and not self.instrument_bringing:
            raise ValidationError({'instrument_bringing': 'This field is required.'})


def _make_class_choice_field() -> Any:
    return models.ForeignKey(
        Class, on_delete=models.SET_NULL, related_name='+', null=True, blank=True)


def _make_class_instrument_field() -> Any:
    return models.ForeignKey(
        InstrumentBringing, on_delete=models.SET_NULL, related_name='+', null=True, blank=True)


ClassChoiceDict = TypedDict(
    'ClassChoiceDict', {'class': Class, 'instrument': InstrumentBringing})


# Note: The name of this class (and related classes and files) is out of date.
# It should be called "ClassSelection", and it functions as a fat interface for all
# types of class selection.
class RegularProgramClassChoices(models.Model):
    registration_entry = models.OneToOneField(
        RegistrationEntry,
        on_delete=models.CASCADE,
        related_name='regular_class_choices',
    )

    comments = models.TextField(blank=True)

    # This field lets Beginner registrants sign up for an extra
    # beginners+ class (costs money).
    wants_extra_beginner_class = models.TextField(
        choices=YesNo.choices, default=YesNo.no, blank=True)

    # These fields are for programs that choose courses in specific
    # periods (e.g. regular, consort coop)
    period1_choice1 = _make_class_choice_field()
    period1_choice1_instrument = _make_class_instrument_field()
    period1_choice2 = _make_class_choice_field()
    period1_choice2_instrument = _make_class_instrument_field()
    period1_choice3 = _make_class_choice_field()
    period1_choice3_instrument = _make_class_instrument_field()

    period2_choice1 = _make_class_choice_field()
    period2_choice1_instrument = _make_class_instrument_field()
    period2_choice2 = _make_class_choice_field()
    period2_choice2_instrument = _make_class_instrument_field()
    period2_choice3 = _make_class_choice_field()
    period2_choice3_instrument = _make_class_instrument_field()

    period3_choice1 = _make_class_choice_field()
    period3_choice1_instrument = _make_class_instrument_field()
    period3_choice2 = _make_class_choice_field()
    period3_choice2_instrument = _make_class_instrument_field()
    period3_choice3 = _make_class_choice_field()
    period3_choice3_instrument = _make_class_instrument_field()

    period4_choice1 = _make_class_choice_field()
    period4_choice1_instrument = _make_class_instrument_field()
    period4_choice2 = _make_class_choice_field()
    period4_choice2_instrument = _make_class_instrument_field()
    period4_choice3 = _make_class_choice_field()
    period4_choice3_instrument = _make_class_instrument_field()
    # end period-specific fields

    # These fields are for programs that can choose classes
    # across periods because they can only take one class
    # (e.g. part-time, seasoned players)
    flex_choice1 = _make_class_choice_field()
    flex_choice1_instrument = _make_class_instrument_field()

    flex_choice2 = _make_class_choice_field()
    flex_choice2_instrument = _make_class_instrument_field()

    flex_choice3 = _make_class_choice_field()
    flex_choice3_instrument = _make_class_instrument_field()

    @cached_property
    def by_period(self) -> dict[Period, list[ClassChoiceDict]]:
        return {
            Period.first: [
                {'class': self.period1_choice1, 'instrument': self.period1_choice1_instrument},
                {'class': self.period1_choice2, 'instrument': self.period1_choice2_instrument},
                {'class': self.period1_choice3, 'instrument': self.period1_choice3_instrument},
            ],
            Period.second: [
                {'class': self.period2_choice1, 'instrument': self.period2_choice1_instrument},
                {'class': self.period2_choice2, 'instrument': self.period2_choice2_instrument},
                {'class': self.period2_choice3, 'instrument': self.period2_choice3_instrument},
            ],
            Period.third: [
                {'class': self.period3_choice1, 'instrument': self.period3_choice1_instrument},
                {'class': self.period3_choice2, 'instrument': self.period3_choice2_instrument},
                {'class': self.period3_choice3, 'instrument': self.period3_choice3_instrument},
            ],
            Period.fourth: [
                {'class': self.period4_choice1, 'instrument': self.period4_choice1_instrument},
                {'class': self.period4_choice2, 'instrument': self.period4_choice2_instrument},
                {'class': self.period4_choice3, 'instrument': self.period4_choice3_instrument},
            ]
        }

    @cached_property
    def num_non_freebie_classes(self) -> int:
        if self.registration_entry.program in FLEXIBLE_CLASS_SELECTION_PROGRAMS:
            return 1 if self.flex_choice1 else 0

        count = 0

        choices_by_period = dict(self.by_period)
        choices_by_period.pop(Period.fourth)
        for choices in choices_by_period.values():
            if any(choice['class'] is not None for choice in choices):
                count += 1

        return count


class AdvancedProjectsParticipationOptions(models.TextChoices):
    participate = 'participate', 'I would like to participate in other projects'
    propose_a_project = 'propose_a_project', 'I would like to propose a project'


class AdvancedProjectsInfo(models.Model):
    registration_entry = models.OneToOneField(
        RegistrationEntry,
        on_delete=models.CASCADE,
        related_name='advanced_projects',
    )

    participation = models.TextField(
        choices=AdvancedProjectsParticipationOptions.choices, blank=False, default=''
    )
    project_proposal = models.TextField(blank=True)


class HousingRoomType(models.TextChoices):
    single = 'single'
    double = 'double'
    off_campus = 'off_campus'


class NormalBedtime(models.TextChoices):
    no_preference = 'no_preference'
    early = 'early', 'Early to bed (11pm)'
    late = 'late', 'Late night (could be 2am!)'


class DietaryNeeds(models.TextChoices):
    vegetarian = 'vegetarian'
    vegan = 'vegan'
    dairy_free = 'dairy_free'
    gluten_free = 'gluten_free'
    nut_allergy = 'nut_allergy'
    shellfish_allergy = 'shellfish_allergy'


class BanquetFoodChoices(models.TextChoices):
    beef = 'beef'
    salmon = 'salmon'
    vegan = 'vegan'
    not_attending = 'not_attending'


class Housing(models.Model):
    registration_entry = models.OneToOneField(
        RegistrationEntry,
        on_delete=models.CASCADE,
        related_name='housing',
    )

    room_type = models.TextField(choices=HousingRoomType.choices, blank=False, default='')
    roommate_request = models.TextField(blank=True)
    share_suite_request = models.TextField(blank=True)
    room_near_person_request = models.TextField(blank=True)

    normal_bed_time = models.TextField(
        choices=NormalBedtime.choices, blank=False, default=NormalBedtime.no_preference)

    arrival_day = models.TextField()
    departure_day = models.TextField()

    is_bringing_child = models.TextField(choices=YesNo.choices, default=YesNo.no)
    contact_others_bringing_children = models.TextField(choices=YesNo.choices, default=YesNo.no)

    wants_housing_subsidy = models.BooleanField(default=False)
    wants_canadian_currency_exchange_discount = models.BooleanField(default=False)

    additional_housing_info = models.TextField(blank=True)

    dietary_needs = ArrayField(
        models.CharField(max_length=50, choices=DietaryNeeds.choices), blank=True, default=list)
    other_dietary_needs = models.TextField(blank=True)

    banquet_food_choice = models.TextField(
        choices=BanquetFoodChoices.choices, blank=False, default='')
    is_bringing_guest_to_banquet = models.TextField(choices=YesNo.choices)
    banquet_guest_name = models.TextField(blank=True)
    banquet_guest_food_choice = models.TextField(
        choices=BanquetFoodChoices.choices[:-1], blank=True)


TSHIRT_SIZES: Final = [
    "Men's S",
    "Men's M",
    "Men's L",
    "Men's XL",
    "Men's XXL",
    "Men's XXXL",

    "Women's Fitted S",
    "Women's Fitted M",
    "Women's Fitted L",
    "Women's V-neck S",
    "Women's V-neck M",
    "Women's V-neck L",
    "Women's V-neck XL",
]


class TShirts(models.Model):
    registration_entry = models.OneToOneField(
        RegistrationEntry,
        on_delete=models.CASCADE,
        related_name='tshirts',
    )

    tshirt1 = models.CharField(
        max_length=50,
        choices=tuple(zip(TSHIRT_SIZES, TSHIRT_SIZES)),
        blank=True
    )
    tshirt2 = models.CharField(
        max_length=50,
        choices=tuple(zip(TSHIRT_SIZES, TSHIRT_SIZES)),
        blank=True
    )
    donation = models.IntegerField(blank=True, default=0)

    def as_list(self) -> list[str]:
        return [self.tshirt1, self.tshirt2]


class PaymentInfo(models.Model):
    registration_entry = models.OneToOneField(
        RegistrationEntry,
        on_delete=models.CASCADE,
        related_name='payment_info',
    )

    # We'll consider registration to be finalized when
    # this field has a value.
    stripe_payment_method_id = models.TextField(blank=True)

# =================================================================================================


# See https://stackoverflow.com/a/37988537
# This class is used to define our custom permissions.
class ConclavePermissions(models.Model):
    class Meta:
        # No database table creation or deletion
        # operations will be performed for this model.
        managed = False
        # disable "add", "change", "delete"
        # and "view" default permissions
        default_permissions = ()

        # Our custom permissions.
        permissions = (
            ('conclave_team', 'Conclave Team'),
        )
