from django.db import models


class AccessoryQuerySet(models.QuerySet):
    def get_attached_status(self, attached, size):
        if size:
            return self.filter(size=size).filter(viol_num__isnull=not attached)

        return self.filter(viol_num__isnull=not attached)


class ViolQuerySet(models.QuerySet):
    def get_rented_status(self, rented, size):
        if size:
            return self.filter(size=size).filter(renter__isnull=not rented)
        return self.filter(renter__isnull=not rented)


class AccessoryManager(models.Manager):
    def get_queryset(self):
        return AccessoryQuerySet(self.model, using=self._db)

    def get_available(self, size=None):
        return self.get_queryset().get_rented_status(rented=False, size=size)

    def get_attached(self):
        return self.get_queryset().get_attached_status(attached=True)

    def get_unattached(self, size):
        return self.get_queryset().get_attached_status(attached=False, size=size)


class ViolManager(models.Manager):
    def get_queryset(self):
        return ViolQuerySet(self.model, using=self._db)

    def get_available(self, size=None):
        return self.get_queryset().get_rented_status(rented=False, size=size)

    def get_rented(self):
        return self.get_queryset().get_rented_status(rented=True)
