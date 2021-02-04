from django.db import models


class AccessoryQuerySet(models.QuerySet):
    def get_attached_status(self, attached):
        return self.filter(viol_num__isnull=not attached)


class ViolQuerySet(models.QuerySet):
    def get_rented_status(self, rented):
        return self.filter(renter__isnull=not rented)


class AccessoryManager(models.Manager):
    def get_queryset(self):
        return AccessoryQuerySet(self.model, using=self._db)

    def get_available(self):
        return self.get_queryset().get_rented_status(rented=False)

    def get_attached(self):
        return self.get_queryset().get_rented_status(rented=True)


class ViolManager(models.Manager):
    def get_queryset(self):
        return ViolQuerySet(self.model, using=self._db)

    def get_available(self):
        return self.get_queryset().get_rented_status(rented=False)

    def get_rented(self):
        return self.get_queryset().get_rented_status(rented=True)
