from django.db import models
from django.db.models import Q, Max, Count, Subquery, OuterRef
from django.db.models.enums import TextChoices
from vdgsa_backend.rental_viols.managers.RentalItemBaseManager import (
    RentalItemBaseManager, RentalEvent, RentalState)
from django.utils.translation import gettext_lazy as _


class ViolSize(TextChoices):
    pardessus = 'pardessus', _('Pardessus')
    treble = 'treble', _('Treble')
    alto = 'alto', _('Alto')
    tenor = 'tenor', _('Tenor')
    bass = 'bass', _('Bass')
    seven_string_bass = 'seven-string bass', _('Seven-String Bass')
    other = 'other', _('Other')


class AccessoryQuerySet(models.QuerySet):

    def get_all(self, size):
        if size:
            return self.filter(size=size)
        return self

    def get_attached_status(self, attached, size):
        if size:
            return self.filter(size=size).filter(viol_num__isnull=not attached)
        return self.filter(viol_num__isnull=not attached)

    def get_status(self, status, size):
        if size:
            return self.filter(size=size).filter(state=status)
        return self.filter(state=status)

    def get_rented_status(self, rented, size):
        if size:
            return self.filter(size=size).filter(viol_num__renter__isnull=not rented)
        return self.filter(viol_num__renter__isnull=not rented)


class ViolQuerySet(models.QuerySet):
    def get_all(self, size):
        if size:
            return self.filter(size=size)
        return self

    def get_rented_status(self, rented, size):
        if size:
            return self.filter(size=size).filter(renter__isnull=not rented)

        return self.filter(renter__isnull=not rented)

    def get_status(self, status, size):
        if size:
            return self.filter(size=size).filter(state=status)
        return self.filter(state=status)


class AccessoryManager(models.Manager):
    def sizeMatch(self, size):
        if size == ViolSize.seven_string_bass:
            return ViolSize.bass
        return size

    def get_queryset(self):
        return AccessoryQuerySet(self.model, using=self._db)

    def get_available(self, size=None):
        return self.get_queryset().get_attached_status(
            attached=False, size=self.sizeMatch(size)).filter(~Q(state=RentalState.retired))
            
    def get_rented(self, size=None):
        return self.get_queryset().get_rented_status(rented=True, size=size)

    def get_retired(self, size=None):
        return self.get_queryset().get_status(status=RentalState.retired, size=size)

    def get_attached(self):
        return self.get_queryset().get_attached_status(viol_num__attached=True)

    def get_unattached(self, size):
        return self.get_queryset().get_attached_status(attached=False, size=self.sizeMatch(size))

    def get_next_accessory_vdgsa_num(self):
        maxVal = self.get_queryset().aggregate(Max('vdgsa_number')).get('vdgsa_number__max')
        maxVal = maxVal or 0
        return maxVal + 1

    def get_all(self, size=None):
        return self.get_queryset().get_all(size=size)


class ViolManager(models.Manager):
    def get_queryset(self):
        return ViolQuerySet(self.model, using=self._db)

    def get_next_vdgsa_num(self):
        maxVal = self.get_queryset().aggregate(Max('vdgsa_number')).get('vdgsa_number__max')
        maxVal = maxVal or 0
        return maxVal + 1

    def get_all(self, size=None):
        return self.get_queryset().get_all(size=size)

    def get_available(self, size=None):
        return self.get_queryset().get_rented_status(rented=False, size=size).filter(
            status=RentalState.available)

    def get_attachable(self, size=None):
        return self.get_queryset().get_rented_status(rented=False, size=size)

    def get_rented(self, size=None):
        return self.get_queryset().get_rented_status(rented=True, size=size)

    def get_retired(self, size=None):
        return self.get_queryset().get_status(status=RentalState.retired, size=size)


class ImageManager(models.Manager):
    def get_queryset(self):
        return ImageQuerySet(self.model, using=self._db)

    def get_images(self, type, pk):
        return self.get_queryset().get_images(type, pk)


class ImageQuerySet(models.QuerySet):
    def get_images(self, type, pk):
        return self.filter(vbc_number=pk).filter(type=type)
