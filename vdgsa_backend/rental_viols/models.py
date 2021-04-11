from __future__ import annotations
from vdgsa_backend.rental_viols.managers.RentalItemBaseManager import (
    RentalItemBaseManager, RentalEvent)
from django.db import models
from django.db.models.enums import TextChoices
from django.utils import timezone
from vdgsa_backend.accounts.models import User
from vdgsa_backend.rental_viols.managers.InstrumentManager import (AccessoryManager, ViolManager,
                                                                   ImageManager)


class RentalProgram(TextChoices):
    regular = 'regular'
    select_reserve = 'select_reserve'
    consort_loan = 'consort_loan'


class ItemType(TextChoices):
    viol = 'viol'
    bow = 'bow'
    case = 'case'


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
    Contains common fields for database hygiene
    """
    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    status = models.TextField(choices=RentalEvent.choices, default=RentalEvent.new)

    objects = RentalItemBaseManager()

    def get_fields(self, obj):
        return obj._meta.get_fields()


class RentalItemInstrument(RentalItemBase):
    """
    Contains common fields used in Viol, Case, and Bow
    """
    class Meta:
        abstract = True

    vdgsa_number = models.IntegerField(blank=True, null=True)
    maker = models.CharField(max_length=50, null=True)
    size = models.TextField(choices=ViolSize.choices, default=ViolSize.bass)
    state = models.CharField(max_length=10, blank=True, null=True)
    value = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    provenance = models.TextField(blank=True)
    description = models.TextField(blank=True)
    accession_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    storer = models.ForeignKey(
        User, blank=True, null=True, default=None, on_delete=models.SET_NULL, related_name='+')
    program = models.TextField(choices=RentalProgram.choices, default=RentalProgram.regular)


class Viol(RentalItemInstrument):
    viol_num = models.AutoField(primary_key=True)
    strings = models.PositiveIntegerField(blank=True)
    renter = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, default=None, related_name='+')

    objects = ViolManager()

    def __str__(self) -> str:
        return (
            f'Viol {self.vdgsa_number}: {self.size}, by: {self.maker} '
        )

    def get_cname(self):
        class_name = 'Viol'
        return class_name

    def get_pk_name(self):
        primary_key_name = 'viol_num'
        return primary_key_name

    def get_absolute_url(self):
        return u'/rentals/viols/%d' % self.viol_num


class Bow(RentalItemInstrument):
    bow_num = models.AutoField(primary_key=True)
    viol_num = models.ForeignKey(
        'Viol', db_column='viol_num',
        on_delete=models.SET_NULL, blank=True, null=True, default=None,
        related_name='bows'
    )

    objects = AccessoryManager()

    def __str__(self) -> str:
        return (
            f'Bow: {self.vdgsa_number}: {self.size}, by:  {self.maker} '
        )

    def get_cname(self):
        class_name = 'Bow'
        return class_name

    def get_pk_name(self):
        primary_key_name = 'bow_num'
        return primary_key_name

    def get_absolute_url(self):
        return u'/rentals/bows/%d' % self.bow_num


class Case(RentalItemInstrument):
    case_num = models.AutoField(primary_key=True)
    viol_num = models.ForeignKey(
        'Viol', db_column='viol_num',
        on_delete=models.SET_NULL, blank=True, null=True, default=None,
        related_name='cases'
    )

    objects = AccessoryManager()

    def __str__(self) -> str:
        return (
            f'Case: {self.vdgsa_number} : {self.size}, by:  {self.maker} '
        )

    def get_cname(self):
        class_name = 'Case'
        return class_name

    def get_pk_name(self):
        primary_key_name = 'case_num'
        return primary_key_name

    def get_absolute_url(self):
        return u'/rentals/cases/%d' % self.case_num


class Image(models.Model):
    picture_id = models.AutoField(primary_key=True)
    vbc_number = models.PositiveIntegerField()  # foreign key using type
    type = models.CharField(max_length=4)
    orig_image_file_name = models.CharField(max_length=250)

    image_file_name = models.ImageField(upload_to='images/', blank=True, null=True)
    # image_file_name = models.CharField(max_length=250)
    image_width = models.IntegerField(blank=True, null=True)
    image_height = models.IntegerField(blank=True, null=True)
    thumb_file_name = models.CharField(max_length=250, blank=True, null=True)
    thumb_width = models.IntegerField(blank=True, null=True)
    thumb_height = models.IntegerField(blank=True, null=True)
    caption = models.TextField(blank=True, null=True)

    objects = ImageManager()

    def __str__(self) -> str:
        return (
            f'{self.image_file_name} '
        )


class RentalContract(RentalItemBase):
    entry_num = models.AutoField(primary_key=True)
    # Leaving both for legacy data
    document = models.FileField(upload_to='contracts/%Y/', blank=True, null=True)
    file_name = models.CharField(max_length=100, blank=True, null=True)
    original_name = models.CharField(max_length=100, blank=True, null=True)


class WaitingList(RentalItemBase):
    class Meta:
        ordering = ('-entry_num',)

    entry_num = models.AutoField(primary_key=True)
    renter_num = models.ForeignKey(User, on_delete=models.CASCADE)
    size = models.TextField(choices=ViolSize.choices)
    viol_num = models.ForeignKey(
        Viol, db_column='viol_num',
        on_delete=models.SET_NULL, blank=True, null=True, default=None,
        related_name='waitingList'
    )
    date_req = models.DateField(blank=True, null=True)

    def get_pk_name(self):
        primary_key_name = 'entry_num'
        return primary_key_name

    def __str__(self) -> str:
        return (
            f'{self.entry_num}: {self.renter_num}, {self.viol_num.maker} '
        )


class RentalHistory(RentalItemBase):
    entry_num = models.AutoField(primary_key=True)
    viol_num = models.ForeignKey(
        Viol, db_column='viol_num',
        on_delete=models.SET_NULL, blank=True, null=True,
        related_name='history'
    )
    bow_num = models.ForeignKey(
        Bow, db_column='bow_num',
        on_delete=models.SET_NULL, blank=True, null=True,
        related_name='history'
    )
    case_num = models.ForeignKey(
        Case, db_column='case_num',
        on_delete=models.SET_NULL, blank=True, null=True,
        related_name='history'
    )
    renter_num = models.ForeignKey(User, blank=True, null=True,
                                   default=None, on_delete=models.SET_NULL, related_name='+')

    event = models.TextField(choices=RentalEvent.choices)
    # date = models.DateField(blank=True, null=True) in RentalItemBase
    notes = models.TextField(blank=True, null=True)
    rental_start = models.DateField(blank=True, null=True)
    rental_end = models.DateField(blank=True, null=True)
    contract_scan = models.ForeignKey(RentalContract, blank=True, null=True,
                                      default=None, on_delete=models.SET_NULL,
                                      related_name='rental')

    def get_pk_name(self):
        primary_key_name = 'entry_num'
        return primary_key_name

    def __str__(self) -> str:
        return (
            f'{self.entry_num}: {self.event} '
        )
