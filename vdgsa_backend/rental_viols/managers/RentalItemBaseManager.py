from django.db.models import QuerySet, Manager
from django.db.models.enums import TextChoices


# created_at = DateTimeField(auto_now_add=True)
# last_modified = DateTimeField(auto_now=True)
# status = TextField(choices=RentalEvent.choices, default=RentalEvent.active)

# def get_fields(obj):
#     return obj._meta.get_fields()


class RentalEvent(TextChoices):
    active = 'active'
    attached = 'attached'
    deleted = 'deleted'
    detached = 'detached'
    new = 'new'
    reserved = 'reserved_for'
    rented = 'rented'
    retired = 'retired'
    returned = 'returned'

    # shipped = 'shipped; ?
    # invoiced = 'invoiced' ? if we integrate stripe payment


class RentalItemBaseQuerySet(QuerySet):
    def delete(self):
        return super(RentalItemBaseQuerySet, self).update(status=RentalEvent.deleted)

    def hard_delete(self):
        return super(RentalItemBaseQuerySet, self).delete()

    # def alive(self):
    #     return self.filter(status=RentalEvent.active)

    # def dead(self):
    #     return self.exclude(status=RentalEvent.deleted)


class RentalItemBaseManager(Manager):
    def __init__(self, *args, **kwargs):
        self.active_only = kwargs.pop('active_only', True)
        super(RentalItemBaseManager, self).__init__(*args, **kwargs)

    def get_queryset(self):
        if self.active_only:
            return RentalItemBaseQuerySet(self.model).exclude(status__in=[RentalEvent.deleted,
                                                                          RentalEvent.retired])
        return RentalItemBaseQuerySet(self.model)
