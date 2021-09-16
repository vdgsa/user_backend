from django.db import models
from django.db.models import Q, Max, Count
from vdgsa_backend.rental_viols.managers.RentalItemBaseManager import (
    RentalItemBaseManager, RentalEvent, RentalState)


class AccessoryQuerySet(models.QuerySet):
    def get_attached_status(self, attached, size):
        if size:
            return self.filter(size=size).filter(viol_num__isnull=not attached)

    def get_status(self, status, size):
        if size:
            return self.filter(size=size).filter(status=status)
        return self.filter(status=status)


class ViolQuerySet(models.QuerySet):
    def get_rented_status(self, rented, size):
        if size:
            return self.filter(size=size).filter(renter__isnull=not rented)

        return self.filter(renter__isnull=not rented)

    def get_status(self, status, size):
        if size:
            return self.filter(size=size).filter(status=status)
        return self.filter(status=status)


class AccessoryManager(models.Manager):
    def get_queryset(self):
        return AccessoryQuerySet(self.model, using=self._db)

    # def get_next_vdgsa_num(self):
    #     maxVal = self.get_queryset().aggregate(Max('vdgsa_number')).get('vdgsa_number__max')
    #     maxVal = maxVal or 0
    #     return maxVal + 1

    def get_available(self, size=None):
        return self.get_queryset().get_attached_status(attached=False, size=size)

    def get_attached(self):
        return self.get_queryset().get_attached_status(attached=True)

    def get_unattached(self, size):
        return self.get_queryset().get_attached_status(attached=False, size=size)

    def get_next_vdgsa_num(self):
        maxVal = self.get_queryset().aggregate(Max('vdgsa_number')).get('vdgsa_number__max')
        maxVal = maxVal or 0
        return maxVal + 1
        

class ViolManager(models.Manager):
    def get_queryset(self):
        return ViolQuerySet(self.model, using=self._db)

    def get_next_vdgsa_num(self):
        maxVal = self.get_queryset().aggregate(Max('vdgsa_number')).get('vdgsa_number__max')
        maxVal = maxVal or 0
        return maxVal + 1

    def get_available(self, size=None):
        return self.get_queryset().get_rented_status(rented=False, size=size).filter(status=RentalState.available)

    def get_attachable(self, size=None):
        return self.get_queryset().get_rented_status(rented=False, size=size)

    def get_rented(self, size=None):
        return self.get_queryset().get_rented_status(rented=True, size=size)

    def get_retired(self, size=None):
        return self.get_queryset().get_status(status='retired', size=size)


class ImageManager(models.Manager):
    def get_queryset(self):
        return ImageQuerySet(self.model, using=self._db)

    def get_images(self, type, pk):
        return self.get_queryset().get_images(type, pk)


class ImageQuerySet(models.QuerySet):
    def get_images(self, type, pk):
        return self.filter(vbc_number=pk).filter(type=type)
