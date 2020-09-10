from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import last_modified


class _CreatedAndUpdatedTimestamps(models.Model):
    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)


class User(AbstractUser):
    username = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )

    # Django doesn't have a one-to-many field other than as the
    # reverse lookup of a foreign key.
    subscription_is_family_member_for = models.ForeignKey(
        'MembershipSubscription',
        on_delete=models.PROTECT,
        related_name='family_members',
        blank=True,
        null=True,
        default=None
    )

    last_modified = models.DateTimeField(auto_now=True)


class MembershipSubscription(_CreatedAndUpdatedTimestamps, models.Model):
    owner = models.OneToOneField(User, on_delete=models.PROTECT, related_name='owned_subscription')
    # family_members is the reverse lookup of a foreign key defined in User.

    valid_until = models.DateTimeField(null=True)

    class MembershipType(models.TextChoices):
        regular = 'regular'
        student = 'student'
        lifetime = 'lifetime'

    membership_type = models.CharField(max_length=50, choices=MembershipType.choices)


class MembershipSubscriptionHistory(_CreatedAndUpdatedTimestamps, models.Model):
    owner = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='owned_subscription_history')
    family_members = models.ManyToManyField(
        User, related_name='subscription_history_as_family_member')

    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(null=True)

    membership_type = models.CharField(
        max_length=50,
        choices=MembershipSubscription.MembershipType.choices
    )
