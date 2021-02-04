from django.db import models


class ViolQuerySet(models.QuerySet):
    def get_rented_status(self, rented):
        return self.filter(renter__isnull=not rented)


class InstrumentManager(models.Manager):
    def get_queryset(self):
        return ViolQuerySet(self.model, using=self._db)

    def get_available(self):
        return self.get_queryset().get_rented_status(rented=False)

    def get_rented(self):
        return self.get_queryset().get_rented_status(rented=True)
