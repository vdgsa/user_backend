from __future__ import annotations

import uuid
from typing import Any, Optional

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
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

    @property
    def subscription(self) -> Optional[MembershipSubscription]:
        if hasattr(self, 'owned_subscription'):
            return self.owned_subscription

        return self.subscription_is_family_member_for

    def save(self, *args: Any, **kwargs: Any) -> None:
        # User.email is used by some out-of-the-box features (like
        # password reset emails), so we want to make sure that
        # email is set to the same value as username.
        if self.email != self.username:
            self.email = self.username

        super().save(*args, **kwargs)


class ChangeEmailRequest(_CreatedAndUpdatedTimestamps, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    new_email = models.EmailField()


class PendingMembershipSubscriptionPurchase(_CreatedAndUpdatedTimestamps, models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        help_text="The user to purchase a subscription for."
    )

    stripe_payment_intent_id = models.TextField(
        help_text="The PaymentIntent ID for the stripe checkout session for this purchase.")

    is_completed = models.BooleanField(
        blank=True,
        default=False,
        help_text="Indicates whether payment has succeeded"
                  " and the subscription has been purchased."
    )


class MembershipType(models.TextChoices):
    regular = 'regular', 'Regular ($40)'
    student = 'student', 'Student ($35)'
    lifetime = 'lifetime'


class MembershipSubscription(_CreatedAndUpdatedTimestamps, models.Model):
    owner = models.OneToOneField(User, on_delete=models.PROTECT, related_name='owned_subscription')
    # family_members is the reverse lookup of a foreign key defined in User.

    valid_until = models.DateTimeField(null=True)

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
        choices=MembershipType.choices
    )


# See https://stackoverflow.com/a/37988537
# This class is used to define our custom permissions.
class AccountPermissions(models.Model):
    class Meta:
        # No database table creation or deletion
        # operations will be performed for this model.
        managed = False
        # disable "add", "change", "delete"
        # and "view" default permissions
        default_permissions = ()

        # Our custom permissions.
        permissions = (
            ('membership_secretary', 'Membership Secretary'),
        )
