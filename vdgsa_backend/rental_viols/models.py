from __future__ import annotations
from django.db import models
from django.db.models.enums import TextChoices
from django.utils import timezone


class RentalProgramChoices(TextChoices):
    regular = 'regular'
    select_reserve = 'select_reserve'
    consort_loan = 'consort_loan'


class Bow(models.Model):
    bow_num = models.AutoField(primary_key=True)
    vdgsa_number = models.IntegerField(blank=True, null=True)
    maker = models.CharField(max_length=50, blank=True, null=True)
    size = models.CharField(max_length=9, blank=True, null=True)
    state = models.CharField(max_length=10, blank=True, null=True)
    value = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    provenance = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    accession_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    viol_num = models.ForeignKey(
        'Viol', db_column='viol_num',
        on_delete=models.PROTECT, blank=True, null=True
    )
    storer = models.IntegerField(blank=True, null=True)

    program = models.TextField(
        choices=RentalProgramChoices.choices, default=RentalProgramChoices.regular)
    # program = models.ForeignKey(
    #     'Program', db_column='program',
    #     on_delete=models.PROTECT, blank=True, null=True
    # )

    def __str__(self) -> str:
        return (
            f'{self.bow_num}: {self.maker}'
        )

    class Meta:
        managed = True


class Case(models.Model):
    case_num = models.AutoField(primary_key=True)
    vdgsa_number = models.IntegerField(blank=True, null=True)
    maker = models.CharField(max_length=50, blank=True, null=True)
    size = models.CharField(max_length=9, blank=True, null=True)
    state = models.CharField(max_length=10, blank=True, null=True)
    value = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    provenance = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    accession_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    viol_num = models.ForeignKey(
        'Viol', db_column='viol_num',
        on_delete=models.PROTECT, blank=True, null=True
    )
    storer = models.ForeignKey(
        'Storer', db_column='storer',
        on_delete=models.PROTECT, blank=True, null=True
    )
    program = models.ForeignKey(
        'Program', db_column='program',
        on_delete=models.PROTECT, blank=True, null=True
    )

    def __str__(self) -> str:
        return (
            f'{self.case_num} : {self.size} {self.maker} '
        )

    class Meta:
        managed = True


class Image(models.Model):
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
    caption = models.CharField(max_length=3000)

    def __str__(self) -> str:
        return (
            f'{self.image_file_name} '
        )

    class Meta:
        managed = True


class Manager(models.Model):
    entry_num = models.AutoField(primary_key=True)
    login_name = models.CharField(max_length=50)
    full_name = models.CharField(max_length=50)
    mail = models.CharField(max_length=100)
    salt = models.CharField(max_length=30)
    digest = models.CharField(max_length=64)
    active = models.IntegerField()
    may_edit = models.IntegerField()

    class Meta:
        managed = True


class Program(models.Model):
    prog_num = models.AutoField(primary_key=True)
    prog_name = models.TextField()

    def __str__(self) -> str:
        return (
            f'{self.prog_name} '
        )

    class Meta:
        managed = True


class Renter(models.Model):
    renter_num = models.AutoField(primary_key=True)
    lastname = models.CharField(max_length=50, blank=True, null=True)
    firstname = models.CharField(max_length=50, blank=True, null=True)
    address1 = models.CharField(max_length=100, blank=True, null=True)
    address2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    stateprov = models.CharField(max_length=2, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=2, blank=True, null=True)
    phone_day = models.CharField(max_length=12, blank=True, null=True)
    phone_eve = models.CharField(max_length=12, blank=True, null=True)
    phone_cell = models.CharField(max_length=12, blank=True, null=True)
    email = models.EmailField(unique=True)
    status = models.CharField(max_length=8, blank=True, null=True)

    def __str__(self) -> str:
        return (
            f'{self.renter_num}: {self.lastname}, {self.firstname} '
        )

    class Meta:
        managed = True


class ScanFiles(models.Model):
    entry_num = models.AutoField(primary_key=True)
    file_name = models.CharField(max_length=100, blank=True, null=True)
    original_name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = True


class Storer(models.Model):
    lastname = models.CharField(max_length=50, blank=True, null=True)
    firstname = models.CharField(max_length=50, blank=True, null=True)
    address1 = models.CharField(max_length=100, blank=True, null=True)
    address2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    stateprov = models.CharField(max_length=2, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=2, blank=True, null=True)
    phone_day = models.CharField(max_length=20, blank=True, null=True)
    phone_eve = models.CharField(max_length=20, blank=True, null=True)
    phone_cell = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(unique=True)
    status = models.CharField(max_length=8, blank=True, null=True)
    storer_num = models.AutoField(primary_key=True)

    def __str__(self) -> str:
        return (
            f'{self.storer_num}: {self.lastname}, {self.firstname} '
        )

    class Meta:
        managed = True


class Viol(models.Model):
    viol_num = models.AutoField(primary_key=True)
    vdgsa_number = models.IntegerField(blank=True, null=True)
    size = models.CharField(max_length=17, blank=True, null=True)
    strings = models.PositiveIntegerField(blank=True, null=True)
    maker = models.CharField(max_length=50, blank=True, null=True)
    inst_value = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    provenance = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    accession_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    state = models.CharField(max_length=9, blank=True, null=True)
    renter = models.ForeignKey(
        'Renter', db_column='renter',
        on_delete=models.PROTECT, blank=True, null=True
    )
    storer = models.ForeignKey(
        'Storer', db_column='storer',
        on_delete=models.PROTECT, blank=True, null=True
    )
    program = models.ForeignKey(
        'Program', db_column='program',
        on_delete=models.PROTECT, blank=True, null=True
    )

    def __str__(self) -> str:
        return (
            f'Viol {self.viol_num}: {self.size}, {self.maker} '
            f'{self.description}'
        )

    class Meta:
        managed = True


class WaitingList(models.Model):
    entry_num = models.AutoField(primary_key=True)
    renter_num = models.ForeignKey(
        'Renter', db_column='renter_num',
        on_delete=models.PROTECT
    )
    size = models.CharField(max_length=17, blank=True, null=True)
    viol_num = models.ForeignKey(
        'Viol', db_column='viol_num',
        on_delete=models.PROTECT, blank=True, null=True
    )
    date_req = models.DateField(blank=True, null=True)

    def __str__(self) -> str:
        return (
            f'{self.entry_num}: {self.renter_num.lastname}, {self.Viol.maker} '
        )

    class Meta:
        managed = True


class RentalHistory(models.Model):
    entry_num = models.AutoField(primary_key=True)
    viol_num = models.ForeignKey(
        'Viol', db_column='viol_num',
        on_delete=models.PROTECT, blank=True, null=True
    )
    bow_num = models.ForeignKey(
        'Bow', db_column='bow_num',
        on_delete=models.PROTECT, blank=True, null=True
    )
    case_num = models.ForeignKey(
        'Case', db_column='case_num',
        on_delete=models.PROTECT, blank=True, null=True
    )
    renter_num = models.ForeignKey(
        'Renter', db_column='renter_num',
        on_delete=models.PROTECT
    )
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

    class Meta:
        managed = True


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
