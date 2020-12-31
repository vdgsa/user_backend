from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone

from vdgsa_backend.accounts.models import MembershipSubscription, MembershipType, User


class UserTestCase(TestCase):
    def test_create_user(self) -> None:
        username = 'batman@batman.com'
        user = User.objects.create_user(username, password='noirestanoriesato')
        user.refresh_from_db()

        self.assertEqual(username, user.username)
        # email should automatically be set to username's value.
        self.assertEqual(username, user.email)
        self.assertFalse(user.is_superuser)

    def test_subscription_property_no_subscription(self) -> None:
        user = User.objects.create_user('user@user.user', password='noirestanoriesato')
        self.assertIsNone(user.subscription)
        self.assertFalse(user.subscription_is_current)

    def test_subscription_property_has_owned_subscription(self) -> None:
        user = User.objects.create_user('user@user.user', password='noirestanoriesato')
        subscription = MembershipSubscription.objects.create(
            owner=user,
            membership_type=MembershipType.regular,
            # Set valid_until to time in past
            valid_until=timezone.now() - timezone.timedelta(hours=1)
        )

        user.refresh_from_db()
        self.assertEqual(subscription, user.subscription)
        self.assertFalse(user.subscription_is_current)

        # Set valid_until to time in future
        subscription.valid_until = timezone.now() + timezone.timedelta(days=1)
        subscription.save()
        user.refresh_from_db()
        self.assertEqual(subscription, user.subscription)
        self.assertTrue(user.subscription_is_current)

    def test_subscription_property_is_family_member(self) -> None:
        owner = User.objects.create_user('user@user.user', password='noirestanoriesato')
        subscription = MembershipSubscription.objects.create(
            owner=owner,
            membership_type=MembershipType.regular,
            valid_until=timezone.now() - timezone.timedelta(hours=1)
        )

        family = User.objects.create_user(
            'family@user.user',
            password='noirestanoriesato',
            subscription_is_family_member_for=subscription,
        )

        family.refresh_from_db()
        self.assertEqual(subscription, family.subscription)
        self.assertFalse(family.subscription_is_current)

        subscription.valid_until = timezone.now() + timezone.timedelta(days=1)
        subscription.save()
        family.refresh_from_db()
        self.assertEqual(subscription, family.subscription)
        self.assertTrue(family.subscription_is_current)

    def test_subscription_property_owned_subscription_takes_precedence(self) -> None:
        user = User.objects.create_user('user@user.user', password='noirestanoriesato')

        subscription_owner_for = MembershipSubscription.objects.create(
            owner=user,
            membership_type=MembershipType.regular,
            valid_until=timezone.now() - timezone.timedelta(hours=1)
        )

        user2 = User.objects.create_user('wee@user.user', password='noirestanoriesato')
        subscription_family_for = MembershipSubscription.objects.create(
            owner=user2,
            membership_type=MembershipType.regular,
            valid_until=timezone.now() + timezone.timedelta(days=1)
        )
        user.subscription_is_family_member_for = subscription_family_for
        user.save()

        user.refresh_from_db()
        self.assertEqual(subscription_owner_for, user.subscription)

    def test_lifetime_member_subscription_is_current_property(self) -> None:
        owner = User.objects.create_user('user@user.user', password='noirestanoriesato')
        subscription = MembershipSubscription.objects.create(
            owner=owner,
            membership_type=MembershipType.lifetime,
        )

        owner.refresh_from_db()
        self.assertEqual(subscription, owner.subscription)
        self.assertTrue(owner.subscription_is_current)

    def test_error_username_not_unique(self) -> None:
        username = 'spam@spam.com'
        User.objects.create_user(username, password='noirestanoriesato')

        with self.assertRaises(IntegrityError):
            User.objects.create_user(username, password='owqfuplno')

    def test_error_username_not_email(self) -> None:
        user = User(username='waaaaluigi')
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_create_superuser(self) -> None:
        # Email (2nd arg to create_superuser) being required
        # may be a type stub error.
        user = User.objects.create_superuser('steve@steve.com', '', password='nfowhnowivnf')
        user.refresh_from_db()
        self.assertTrue(user.is_superuser)


class MembershipSubscriptionTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.owner = User.objects.create_user('an_user@user.com', password='inesranosetra')

    def test_create_with_owner_and_add_family_members(self) -> None:
        family = [
            User.objects.create_user(f'user{i}@user.com', password='norseitnorest')
            for i in range(3)
        ]
        now = timezone.now()
        subscription = MembershipSubscription.objects.create(
            owner=self.owner,
            valid_until=now,
            membership_type=MembershipType.regular
        )
        subscription.family_members.set(family)

        subscription.refresh_from_db()
        self.assertEqual(self.owner, subscription.owner)
        self.assertCountEqual(family, subscription.family_members.all())
        self.assertEqual(now, subscription.valid_until)
        self.assertEqual(
            MembershipType.regular,
            subscription.membership_type
        )

    def test_valid_until_null(self) -> None:
        subscription = MembershipSubscription.objects.create(
            owner=self.owner,
            valid_until=None,
            membership_type=MembershipType.lifetime
        )
        subscription.refresh_from_db()
        self.assertEqual(self.owner, subscription.owner)
        self.assertEqual(0, subscription.family_members.count())
        self.assertIsNone(subscription.valid_until)

    def test_error_invalid_membership_type(self) -> None:
        with self.assertRaises(ValidationError) as cm:
            subscription = MembershipSubscription(
                owner=self.owner,
                valid_until=None,
                membership_type='nooope'
            )
            subscription.full_clean()

        self.assertIn('membership_type', cm.exception.message_dict)

    def test_error_no_owner(self) -> None:
        with self.assertRaises(IntegrityError):
            MembershipSubscription.objects.create(
                valid_until=None,
                membership_type=MembershipType.lifetime
            )
