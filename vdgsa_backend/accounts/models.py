from __future__ import annotations

import uuid
from typing import Any, Dict, Final, Optional

from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields.array import ArrayField
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class _CreatedAndUpdatedTimestamps(models.Model):
    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)


class User(AbstractUser):
    class Meta:
        ordering = ('last_name', 'first_name', 'username')

    # Require that usernames are email addresses
    username = models.EmailField(unique=True, verbose_name='Email')

    # Django doesn't have a one-to-many field other than as the
    # reverse lookup of a foreign key.
    subscription_is_family_member_for = models.ForeignKey(
        'MembershipSubscription',
        on_delete=models.SET_NULL,
        related_name='family_members',
        blank=True,
        null=True,
        default=None
    )

    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    address_city = models.CharField(max_length=255, blank=True)
    address_state = models.CharField(max_length=255, blank=True)
    address_postal_code = models.CharField(max_length=255, blank=True)
    address_country = models.CharField(max_length=255, blank=True)
    phone1 = models.CharField(max_length=30, blank=True)
    phone2 = models.CharField(max_length=30, blank=True)

    is_young_player = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_remote_teacher = models.BooleanField(default=False)
    teacher_description = models.TextField(max_length=250, blank=True)
    is_instrument_maker = models.BooleanField(default=False)
    is_bow_maker = models.BooleanField(default=False)
    is_repairer = models.BooleanField(default=False)
    is_publisher = models.BooleanField(default=False)
    other_commercial = models.CharField(max_length=255, blank=True)
    educational_institution_affiliation = models.CharField(max_length=255, blank=True)

    do_not_email = models.BooleanField(default=False)

    include_name_in_membership_directory = models.BooleanField(default=True)
    include_email_in_membership_directory = models.BooleanField(default=True)
    include_address_in_membership_directory = models.BooleanField(default=True)
    include_phone_in_membership_directory = models.BooleanField(default=True)

    include_name_in_mailing_list = models.BooleanField(default=True)
    include_email_in_mailing_list = models.BooleanField(default=True)
    include_address_in_mailing_list = models.BooleanField(default=True)
    include_phone_in_mailing_list = models.BooleanField(default=True)

    # MEMBERSHIP SECRETARY ONLY
    is_deceased = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    # \MEMBERSHIP SECRETARY ONLY

    last_modified = models.DateTimeField(auto_now=True)

    @property
    def subscription(self) -> Optional[MembershipSubscription]:
        if hasattr(self, 'owned_subscription'):
            return self.owned_subscription

        return self.subscription_is_family_member_for

    @property
    def subscription_is_current(self) -> bool:
        if self.subscription is None:
            return False

        if self.subscription.membership_type == MembershipType.lifetime:
            return True

        return (
            self.subscription.valid_until is not None
            and timezone.now() <= self.subscription.valid_until
        )

    def save(self, *args: Any, **kwargs: Any) -> None:
        # User.email is used by some out-of-the-box features (like
        # password reset emails), so we want to make sure that
        # email is set to the same value as username.
        if self.email != self.username:
            self.email = self.username

        super().save(*args, **kwargs)


class ChangeEmailRequest(_CreatedAndUpdatedTimestamps, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    new_email = models.EmailField()


REGULAR_MEMBERSHIP_PRICE: Final[int] = 35
STUDENT_MEMBERSHIP_PRICE: Final[int] = 20
INTERNATIONAL_MEMBERSHIP_PRICE: Final[int] = 40


class MembershipType(models.TextChoices):
    regular = 'regular', f'Regular (${REGULAR_MEMBERSHIP_PRICE})'
    student = 'student', f'Student (${STUDENT_MEMBERSHIP_PRICE})'
    international = 'international', f'International (${INTERNATIONAL_MEMBERSHIP_PRICE})'
    lifetime = 'lifetime'
    complementary = 'complementary'
    organization = 'organization'


class PendingMembershipSubscriptionPurchase(_CreatedAndUpdatedTimestamps, models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="The user to purchase a subscription for."
    )

    membership_type = models.CharField(max_length=50, choices=MembershipType.choices)

    stripe_payment_intent_id = models.TextField(
        help_text="The PaymentIntent ID for the stripe checkout session for this purchase.")

    is_completed = models.BooleanField(
        blank=True,
        default=False,
        help_text="Indicates whether payment has succeeded"
                  " and the subscription has been purchased."
    )


class MembershipSubscription(_CreatedAndUpdatedTimestamps, models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='owned_subscription')
    # family_members is the reverse lookup of a foreign key defined in User.

    valid_until = models.DateTimeField(null=True)

    membership_type = models.CharField(max_length=50, choices=MembershipType.choices)
    years_renewed = ArrayField(models.IntegerField(), blank=True, default=list)

    def __str__(self) -> str:
        return (
            f'MembershipSubscription {self.owner.last_name}, {self.owner.first_name} '
            f'{self.owner.username}'
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
            ('board_member', 'Board Member')
        )
