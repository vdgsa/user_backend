from django.db import models
from vdgsa_backend.rental_viols.models import RentalEvent

# entry_num
# viol_num
# bow_num
# case_num
# renter_num
# event
# notes
# rental_start
# rental_end
# contract_scan



class RentalHistoryQuerySet(models.QuerySet):
    def addRentalHistory(self, rented):
        return self.filter(renter__isnull=not rented)


class RentalActionsManager(models.Manager):

    def get_query_set(self):
        return self.model.QuerySet(self.model)

    def __getattr__(self, attr, *args):
        return getattr(self.get_query_set(), attr, *args)
