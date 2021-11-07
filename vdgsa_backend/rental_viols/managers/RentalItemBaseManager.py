from django.db.models import QuerySet, Manager
from django.db.models.enums import TextChoices


# created_at = DateTimeField(auto_now_add=True)
# last_modified = DateTimeField(auto_now=True)
# status = TextField(choices=RentalState.choices, default=RentalState.available)

# def get_fields(obj):
#     return obj._meta.get_fields()


class RentalEvent(TextChoices):
    available = 'Available'
    attached = 'Attached'
    deleted = 'Deleted'
    detached = 'Detached'
    new = 'New'
    rented = 'Rented'
    retired = 'Retired'
    renewed = 'Renewed'
    reserved = 'Reserved'
    returned = 'Returned'


class RentalState(TextChoices):
    attached = 'Attached'
    available = 'Available'
    deleted = 'Deleted'
    detached = 'Detached'
    new = 'New'
    rented = 'Rented'
    reserved = 'Reserved'
    retired = 'Retired'
    unattached = 'Unattached'
    unknown = 'Unknown'

    # shipped = 'shipped; ?
    # invoiced = 'invoiced' ? if we integrate stripe payment


class RentalItemBaseQuerySet(QuerySet):
    def delete(self):
        return super(RentalItemBaseQuerySet, self).update(status=RentalState.deleted)

    def hard_delete(self):
        return super(RentalItemBaseQuerySet, self).delete()

    # def alive(self):
    #     return self.filter(status=RentalState.available)

    # def dead(self):
    #     return self.exclude(status=RentalState.deleted)


class RentalItemBaseManager(Manager):
    def __init__(self, *args, **kwargs):
        self.active_only = kwargs.pop('active_only', True)
        super(RentalItemBaseManager, self).__init__(*args, **kwargs)

    def get_queryset(self):
        if self.active_only:
            return RentalItemBaseQuerySet(self.model).exclude(status__in=[RentalState.deleted,
                                                                          RentalState.retired])
        return RentalItemBaseQuerySet(self.model)
