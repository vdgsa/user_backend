from __future__ import annotations
from typing import Any

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db import transaction
from django.utils.translation import gettext_lazy as _


class _CreatedAndUpdatedTimestamps(models.Model):
    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)


class User(AbstractUser):
    # Require that usernames are email addresses
    username = models.EmailField(unique=True)

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

    def save(self, *args: Any, **kwargs: Any) -> None:
        # User.email is used by some out-of-the-box features (like
        # password reset emails), so we want to make sure that
        # email is set to the same value as username.
        if self.email != self.username:
            self.email = self.username

        super().save(*args, **kwargs)


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
