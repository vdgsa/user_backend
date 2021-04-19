from __future__ import annotations

from typing import Any, Final

from django.contrib.postgres.fields.array import ArrayField
from django.core.exceptions import ValidationError
from django.db import models

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
    regular = 'regular'
    faculty_guest_other = 'faculty_guest_other', 'Faculty/Guest/Other'
    # beginners = 'beginners'
    # consort_coop = 'consort_coop'
    # seasoned_players = 'seasoned_players'
    # exhibitor = 'exhibitor'
    # non_playing_attendee = 'non_playing_attendee'


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

    # basic_info is the related name for BasicRegistrationInfo


class BasicRegistrationInfo(models.Model):
    registration_entry = models.OneToOneField(
        RegistrationEntry,
        on_delete=models.CASCADE,
        related_name='basic_info'
    )

    is_first_time_attendee = models.TextField(choices=YesNoMaybe.choices)
    buddy_willingness = models.TextField(choices=YesNoMaybe.choices)
    willing_to_help_with_small_jobs = models.BooleanField(blank=True)
    wants_display_space = models.BooleanField(blank=True)

    photo_release_auth = models.BooleanField()
    liability_release = models.BooleanField()

    other_info = models.TextField(blank=True)


class WorkStudyJob(models.TextChoices):
    fixme = 'fixme'


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
    registration_entry = models.ForeignKey(
        RegistrationEntry,
        on_delete=models.CASCADE,
        related_name='instruments_bringing',
    )

    size = models.CharField(max_length=100, choices=InstrumentChoices.choices)
    name_if_other = models.CharField(max_length=100, blank=True)
    level = models.TextField(choices=Level.choices)
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
    return models.ForeignKey(Class, on_delete=models.SET_NULL, related_name='+', null=True)


def _make_class_instrument_field() -> Any:
    return models.ForeignKey(
        InstrumentBringing, on_delete=models.SET_NULL, related_name='+', null=True, blank=True)


class RegularProgramClassChoices(models.Model):
    registration_entry = models.OneToOneField(
        RegistrationEntry,
        on_delete=models.CASCADE,
        related_name='regular_class_choices',
    )

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
    tshirt3 = models.CharField(max_length=50, choices=TShirtSizes.choices, blank=True)


class PaymentInfo(models.Model):
    registration_entry = models.OneToOneField(
        RegistrationEntry,
        on_delete=models.CASCADE,
        related_name='payment_info',
    )

    donation = models.IntegerField(blank=True)
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
