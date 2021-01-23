from __future__ import annotations
from django.db import models
from django.db.models.enums import TextChoices

from vdgsa_backend.accounts.models import User


class RentalProgram(TextChoices):
    regular = 'regular'
    select_reserve = 'select_reserve'
    consort_loan = 'consort_loan'


class ViolSize(TextChoices):
    pardessus = 'pardessus'
    treble = 'treble'
    alto = 'alto'
    tenor = 'tenor'
    bass = 'bass'
    seven_string_bass = 'seven_string_bass', 'Seven-String Bass'
    other = 'other'


class RentalItemBase(models.Model):
    """
    Contains common fields used in Viol, Case, and Bow
    """
    class Meta:
        abstract = True

    vdgsa_number = models.IntegerField()
    maker = models.CharField(max_length=50)
    size = models.TextField(choices=ViolSize.choices)
    state = models.CharField(max_length=10, blank=True, null=True)
    value = models.DecimalField(max_digits=8, decimal_places=2)
    provenance = models.TextField(blank=True)
    description = models.TextField(blank=True)
    accession_date = models.DateField(blank=True)
    notes = models.TextField(blank=True)
    storer = models.ForeignKey(
        User, blank=True, null=True, default=None, on_delete=models.SET_NULL, related_name='+')
    program = models.TextField(choices=RentalProgram.choices, default=RentalProgram.regular)


class Viol(RentalItemBase):
    viol_num = models.AutoField(primary_key=True)

    strings = models.PositiveIntegerField(blank=True)

    # TODO: Either 1) convert the legacy data to use the inherited "value" field
    # or 2) after populating the legacy data, copy from "inst_value" to "value" and
    # then remove "inst_value"
    inst_value = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    renter = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, default=None, related_name='+')

    def __str__(self) -> str:
        return (
            f'Viol {self.viol_num}: {self.size}, {self.maker} '
            f'{self.description}'
        )


class Bow(RentalItemBase):
    bow_num = models.AutoField(primary_key=True)

    viol_num = models.ForeignKey(
        'Viol', db_column='viol_num',
        on_delete=models.SET_NULL, blank=True, null=True, default=None,
        related_name='bows'
    )

    def __str__(self) -> str:
        return (
            f'Viol {self.viol_num}: {self.size}, {self.maker} '
            f'{self.description}'
        )


class Case(models.Model):
    case_num = models.AutoField(primary_key=True)

    viol_num = models.ForeignKey(
        'Viol', db_column='viol_num',
        on_delete=models.SET_NULL, blank=True, null=True, default=None,
        related_name='cases'
    )

    def __str__(self) -> str:
        return (
            f'{self.case_num} : {self.size} {self.maker} '
        )


class Image(models.Model):
    # TODO: Use ImageField
    picture_id = models.AutoField(primary_key=True)
    vbc_number = models.PositiveIntegerField()
    type = models.CharField(max_length=4)
    orig_image_file_name = models.CharField(max_length=250)
    image_file_name = models.CharField(max_length=250)
    image_width = models.IntegerField()
    image_height = models.IntegerField()
    thumb_file_name = models.CharField(max_length=250)
    thumb_width = models.IntegerField()
    thumb_height = models.IntegerField()
    caption = models.TextField()

    def __str__(self) -> str:
        return (
            f'{self.image_file_name} '
        )


class RentalContract(models.Model):
    entry_num = models.AutoField(primary_key=True)
    # Possibly change to ImageField
    file_name = models.CharField(max_length=100, blank=True, null=True)
    original_name = models.CharField(max_length=100, blank=True, null=True)


class WaitingList(models.Model):
    class Meta:
        ordering = ('entry_num',)

    entry_num = models.AutoField(primary_key=True)
    renter_num = models.ForeignKey(User, on_delete=models.CASCADE)
    size = models.TextField(choices=TextChoices.choices)
    viol_num = models.ForeignKey(
        Viol, db_column='viol_num',
        on_delete=models.SET_NULL, blank=True, null=True, default=None
    )
    date_req = models.DateField(blank=True, null=True)

    def __str__(self) -> str:
        return (
            f'{self.entry_num}: {self.renter_num.lastname}, {self.viol.maker} '
        )


class RentalHistory(models.Model):
    entry_num = models.AutoField(primary_key=True)
    viol_num = models.ForeignKey(
        Viol, db_column='viol_num',
        on_delete=models.SET_NULL, blank=True, null=True
    )
    bow_num = models.ForeignKey(
        Bow, db_column='bow_num',
        on_delete=models.SET_NULL, blank=True, null=True
    )
    case_num = models.ForeignKey(
        Case, db_column='case_num',
        on_delete=models.SET_NULL, blank=True, null=True
    )
    renter_num = models.ForeignKey(User, on_delete=models.PROTECT)
    event = models.TextField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    rental_start = models.DateField(blank=True, null=True)
    rental_end = models.DateField(blank=True, null=True)
    contract_scan = models.IntegerField(blank=True, null=True)

    def __str__(self) -> str:
        return (
            f'{self.entry_num}: {self.renter_num.lastname}, {self.viol_num.maker} '
        )


# See https://stackoverflow.com/a/37988537
# This class is used to define our custom permissions.
class RentalPermissions(models.Model):
    class Meta:
        # No database table creation or deletion
        # operations will be performed for this model.
        managed = False
        # disable "add", "change", "delete"
        # and "view" default permissions
        default_permissions = ()

        # Our custom permissions.
        permissions = (
            ('rental_manager', 'Rental Manager'),
        )
