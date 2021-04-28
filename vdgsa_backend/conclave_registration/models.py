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

    photo_release_text = models.TextField(blank=True)

    first_period_time_label = models.CharField(max_length=255, blank=True)
    second_period_time_label = models.CharField(max_length=255, blank=True)
    third_period_time_label = models.CharField(max_length=255, blank=True)
    fourth_period_time_label = models.CharField(max_length=255, blank=True)

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
    level = ArrayField(models.CharField(max_length=50, choices=Level.choices))
    instructor = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self) -> str:
        return f'{self.name} | {"/".join(self.level)} | {self.instructor}'


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


class YesNoMaybe(models.TextChoices):
    yes = 'yes'
    no = 'no'
    maybe = 'maybe'


class Program(models.TextChoices):
    regular = 'regular', 'Regular Curriculum (part- and full-time)'
    beginners = 'beginners', 'Beginner Programs (both teen and adult)'
    consort_coop = 'consort_coop', 'Consort Cooperative'
    seasoned_players = 'seasoned_players', 'Seasoned Players'
    advanced_projects = 'advanced_projects', 'Advanced Projects'
    faculty_guest_other = 'faculty_guest_other', 'Faculty/Guest/Other'
    # exhibitor = 'exhibitor', 'Vendors'
    # non_playing_attendee = 'non_playing_attendee'


ADVANCED_PROGRAMS = [Program.consort_coop, Program.seasoned_players, Program.advanced_projects]
NO_CLASS_PROGRAMS = [
    Program.faculty_guest_other,
    # Program.exhibitor,
    # Program.non_playing_attendee,
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
        non-playing attendee that will never select classes.
        """
        return self.program not in NO_CLASS_PROGRAMS

    @property
    def is_advanced_program(self) -> bool:
        return self.program in ADVANCED_PROGRAMS

    @property
    def is_finalized(self) -> bool:
        return self.payment_info is not None and self.payment_info.stripe_payment_method_id != ''

    @property
    def total_charges(self) -> int:
        return self.tuition_charge + self.tshirts_charge + self.late_fee + self.donation

    @property
    def donation(self) -> int:
        if not hasattr(self, 'tshirts'):
            return 0

        return self.tshirts.donation

    @property
    def total_minus_work_study(self) -> int:
        return self.total_charges - self.tuition_charge

    @property
    def tuition_charge(self) -> int:
        if self.program in NO_CLASS_PROGRAMS:
            return 0

        if self.program == Program.regular:
            if self.regular_class_choices.num_classes_selected <= 1:
                return 100
            else:
                return 200

        if self.program == Program.beginners:
            return 0 if self.regular_class_choices.num_classes_selected == 0 else 100

        if self.program in ADVANCED_PROGRAMS:
            return 100 if self.regular_class_choices.num_classes_selected == 0 else 200

        return 100

    @property
    def late_fee(self) -> int:
        return 25 if self.is_late else 0

    @property
    def num_tshirts(self) -> int:
        if not hasattr(self, 'tshirts'):
            return 0

        return sum((1 for item in [self.tshirts.tshirt1, self.tshirts.tshirt2] if item))

    @property
    def tshirts_charge(self) -> int:
        return self.num_tshirts * 25


class BasicRegistrationInfo(models.Model):
    registration_entry = models.OneToOneField(
        RegistrationEntry,
        on_delete=models.CASCADE,
        related_name='basic_info'
    )

    is_first_time_attendee = models.BooleanField()
    buddy_willingness = models.TextField(choices=YesNoMaybe.choices, blank=True)
    willing_to_help_with_small_jobs = models.BooleanField(blank=True)
    wants_display_space = models.BooleanField(blank=True)

    photo_release_auth = models.BooleanField()
    liability_release = models.BooleanField()

    other_info = models.TextField(blank=True)

    def clean(self) -> None:
        super().clean()
        if not self.is_first_time_attendee and not self.buddy_willingness:
            raise ValidationError({'buddy_willingness': 'This field is required.'})


class WorkStudyJob(models.TextChoices):
    hospitality = 'hospitality'
    moving_crew = 'moving_crew'
    copy_crew_auction = 'copy_crew_auction', 'Copy Crew/Auction'
    money_store = 'money_store', 'Money/Store'
    any = 'any'


class WorkStudyApplication(models.Model):
    registration_entry = models.OneToOneField(
        RegistrationEntry,
        on_delete=models.CASCADE,
        related_name='work_study'
    )

    first_time_applying = models.BooleanField()
    alternate_address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=50, blank=True)
    age_if_under_22 = models.IntegerField(blank=True, null=True, default=None)

    is_full_time_student = models.BooleanField()
    student_school = models.TextField(blank=True)
    student_degree = models.TextField(blank=True)
    student_graduation_date = models.TextField(blank=True)

    can_arrive_before_sunday_morning = models.BooleanField()
    earliest_could_arrive = models.TextField()
    has_car = models.BooleanField()

    job_first_choice = models.TextField(choices=WorkStudyJob.choices)
    job_second_choice = models.TextField(choices=WorkStudyJob.choices)

    interest_in_work_study = models.TextField(max_length=500)
    other_skills = models.TextField(max_length=500, blank=True)
    questions_comments = models.TextField(max_length=500, blank=True)

    def clean(self) -> None:
        super().clean()
        if self.is_full_time_student:
            if not self.student_school:
                raise ValidationError({'student_school': 'This field is required'})
            if not self.student_degree:
                raise ValidationError({'student_degree': 'This field is required'})
            if not self.student_graduation_date:
                raise ValidationError({'student_graduation_date': 'This field is required'})


class Clef(models.TextChoices):
    treble = 'treble', 'Treble clef'
    octave_treble = 'octave_treble', 'Octave Treble clef'
    alto = 'alto', 'Alto clef'
    bass = 'bass', 'Bass clef'


class InstrumentChoices(models.TextChoices):
    treble = 'treble'
    tenor = 'tenor'
    bass = 'bass'
    other = 'other'


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

    def clean(self) -> None:
        super().clean()
        if self.size == InstrumentChoices.other and not self.name_if_other:
            raise ValidationError({'name_if_other': 'This field is required'})

    def __str__(self) -> str:
        if self.size == InstrumentChoices.other:
            return self.name_if_other

        return InstrumentChoices(self.size).label


def _make_class_choice_field() -> Any:
    return models.ForeignKey(
        Class, on_delete=models.SET_NULL, related_name='+', null=True, blank=True)


def _make_class_instrument_field() -> Any:
    return models.ForeignKey(
        InstrumentBringing, on_delete=models.SET_NULL, related_name='+', null=True, blank=True)


class TuitionOption(models.TextChoices):
    full_time = 'full_time', 'Full Time (2-3 Classes)'
    part_time = 'part_time', 'Part Time (1 Class)'


_ClassChoiceDict = TypedDict(
    '_ClassChoiceDict', {'class': Class, 'instrument': InstrumentBringing})


class RegularProgramClassChoices(models.Model):
    registration_entry = models.OneToOneField(
        RegistrationEntry,
        on_delete=models.CASCADE,
        related_name='regular_class_choices',
    )

    comments = models.TextField(blank=True)

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

    @cached_property
    def period1_choices(self) -> list[_ClassChoiceDict]:
        return [
            {'class': self.period1_choice1, 'instrument': self.period1_choice1_instrument},
            {'class': self.period1_choice2, 'instrument': self.period1_choice2_instrument},
            {'class': self.period1_choice3, 'instrument': self.period1_choice3_instrument},
        ]

    @cached_property
    def period2_choices(self) -> list[_ClassChoiceDict]:
        return [
            {'class': self.period2_choice1, 'instrument': self.period2_choice1_instrument},
            {'class': self.period2_choice2, 'instrument': self.period2_choice2_instrument},
            {'class': self.period2_choice3, 'instrument': self.period2_choice3_instrument},
        ]

    @cached_property
    def period3_choices(self) -> list[_ClassChoiceDict]:
        return [
            {'class': self.period3_choice1, 'instrument': self.period3_choice1_instrument},
            {'class': self.period3_choice2, 'instrument': self.period3_choice2_instrument},
            {'class': self.period3_choice3, 'instrument': self.period3_choice3_instrument},
        ]

    @cached_property
    def period4_choices(self) -> list[_ClassChoiceDict]:
        return [
            {'class': self.period4_choice1, 'instrument': self.period4_choice1_instrument},
            {'class': self.period4_choice2, 'instrument': self.period4_choice2_instrument},
            {'class': self.period4_choice3, 'instrument': self.period4_choice3_instrument},
        ]

    @cached_property
    def by_period(self) -> dict[Period, list[_ClassChoiceDict]]:
        return {
            Period.first: self.period1_choices,
            Period.second: self.period2_choices,
            Period.third: self.period3_choices,
            Period.fourth: self.period4_choices,
        }

    @property
    def num_classes_selected(self) -> int:
        count = 0
        for choices in self.by_period.values():
            if any(choice['class'] is not None for choice in choices):
                count += 1

        return count


# We won't need this until 2022
# class RoomAndBoard(models.Model):
#     pass


class TShirtSizes(models.TextChoices):
    x_small = 'XS'
    x_small_fitted = 'XS (Fitted)'
    small = 'S'
    small_fitted = 'S (Fitted)'
    medium = 'M'
    medium_fitted = 'M (Fitted)'
    large = 'L'
    large_fitted = 'L (Fitted)'
    x_large = 'XL'
    x_large_fitted = 'XL (Fitted)'


class TShirts(models.Model):
    registration_entry = models.OneToOneField(
        RegistrationEntry,
        on_delete=models.CASCADE,
        related_name='tshirts',
    )

    tshirt1 = models.CharField(max_length=50, choices=TShirtSizes.choices, blank=True)
    tshirt2 = models.CharField(max_length=50, choices=TShirtSizes.choices, blank=True)
    donation = models.IntegerField(blank=True, default=0)


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
