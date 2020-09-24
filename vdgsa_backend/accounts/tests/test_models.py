from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone

from vdgsa_backend.accounts.models import (
    MembershipSubscription,
    MembershipSubscriptionHistory,
    User
)
from vdgsa_backend.exceptions import DjangoValidationError


class UserTestCase(TestCase):
    def test_create_user(self) -> None:
        username = 'batman@batman.com'
        user = User.objects.create_user(username, password='noirestanoriesato')
        user.refresh_from_db()

        self.assertEqual(username, user.username)
        # email should automatically be set to username's value.
        self.assertEqual(username, user.email)
        self.assertFalse(user.is_superuser)

    def test_error_username_not_unique(self) -> None:
        username = 'spam@spam.com'
        User.objects.create_user(username, password='noirestanoriesato')

        with self.assertRaises(IntegrityError):
            User.objects.create_user(username, password='owqfuplno')

    def test_error_username_not_email(self) -> None:
        user = User(username='waaaaluigi')
        with self.assertRaises(DjangoValidationError):
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
            membership_type=MembershipSubscription.MembershipType.regular
        )
        subscription.family_members.set(family)

        subscription.refresh_from_db()
        self.assertEqual(self.owner, subscription.owner)
        self.assertCountEqual(family, subscription.family_members.all())
        self.assertEqual(now, subscription.valid_until)
        self.assertEqual(
            MembershipSubscription.MembershipType.regular,
            subscription.membership_type
        )

    def test_valid_until_null(self) -> None:
        subscription = MembershipSubscription.objects.create(
            owner=self.owner,
            valid_until=None,
            membership_type=MembershipSubscription.MembershipType.lifetime
        )
        subscription.refresh_from_db()
        self.assertEqual(self.owner, subscription.owner)
        self.assertEqual(0, subscription.family_members.count())
        self.assertIsNone(subscription.valid_until)

    def test_error_invalid_membership_type(self) -> None:
        with self.assertRaises(DjangoValidationError) as cm:
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
                membership_type=MembershipSubscription.MembershipType.lifetime
            )


class MembershipSubscriptionHistoryTestCase(TestCase):
    def test_create_with_all_fields(self) -> None:
        owner = User.objects.create_user('someone@me.com', password='noweifvknowfv')
        family = [
            User.objects.create_user(f'user{i}@user.com', password='novrfunofvi')
            for i in range(4)
        ]

        valid_from = timezone.now()
        valid_until = valid_from + timezone.timedelta(hours=4)
        history = MembershipSubscriptionHistory.objects.create(
            owner=owner,
            valid_from=valid_from,
            valid_until=valid_until,
            membership_type=MembershipSubscription.MembershipType.student
        )
        history.family_members.set(family)

        history.refresh_from_db()
        self.assertEqual(owner, history.owner)
        self.assertCountEqual(family, history.family_members.all())
        self.assertEqual(valid_from, history.valid_from)
        self.assertEqual(valid_until, history.valid_until)
        self.assertEqual(
            MembershipSubscription.MembershipType.student,
            history.membership_type
        )

        # Owner and family can have multiple history entries
        history2 = MembershipSubscriptionHistory.objects.create(
            owner=owner,
            valid_from=valid_from,
            valid_until=valid_until,
            membership_type=MembershipSubscription.MembershipType.student
        )
        history2.family_members.set(family)

        history2.refresh_from_db()
        self.assertEqual(owner, history2.owner)
        self.assertCountEqual(family, history2.family_members.all())
        self.assertEqual(valid_from, history2.valid_from)
        self.assertEqual(valid_until, history2.valid_until)
        self.assertEqual(
            MembershipSubscription.MembershipType.student,
            history2.membership_type
        )
