from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db.models import Count, F, IntegerField, Max, Q
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone

from vdgsa_backend.accounts.models import MembershipSubscription, MembershipType, User
from vdgsa_backend.emails.views import (ExpiringEmails, EXPIRING_THIS_MONTH, EXPIRED_LAST_MONTH, EXPIRED_PAST)


class MembershipSubscriptionExpiredEmailsTestCase(TestCase):
    # def setUp(self) -> None:
    #     super().setUp()
    #     self.owner = User.objects.create_user('an_user@user.com', password='inesranosetra')

    # def test_create_with_owner_and_add_family_members(self) -> None:
    #     family = [
    #         User.objects.create_user(f'user{i}@user.com', password='norseitnorest')
    #         for i in range(3)
    #     ]
    #     now = date.today()

    #     startdate = date.today() + timedelta(days=4)
    #     subscription = MembershipSubscription.objects.create(
    #         owner=self.owner,
    #         valid_until=now,
    #         membership_type=MembershipType.regular
    #     )
    #     subscription.family_members.set(family)

    #     subscription.refresh_from_db()
    #     self.assertEqual(self.owner, subscription.owner)
    #     self.assertCountEqual(family, subscription.family_members.all())
    #     self.assertEqual(now, subscription.valid_until)
    #     self.assertEqual(
    #         MembershipType.regular,
    #         subscription.membership_type
    #     )

    def test_expiring_emails(self) -> None:
        user = User.objects.create_user('expired-year-ago@user.user', password='fakefakefake')
        subscription = MembershipSubscription.objects.create(
            owner=user,
            membership_type=MembershipType.regular,
            valid_until=timezone.now() - timezone.timedelta(days=365)
        )
        user = User.objects.create_user('6-month-ago@user.user', password='fakefakefake')
        subscription = MembershipSubscription.objects.create(
            owner=user,
            membership_type=MembershipType.regular,
            valid_until=timezone.now() - timezone.timedelta(days=180)
        )
        user = User.objects.create_user('expired-month-ago@user.user',
                                        password='fakefakefake')
        subscription = MembershipSubscription.objects.create(
            owner=user,
            membership_type=MembershipType.regular,
            valid_until=timezone.now() - timezone.timedelta(days=28)
        )
        user = User.objects.create_user('10days-ago@user.user', password='fakefakefake')
        subscription = MembershipSubscription.objects.create(
            owner=user,
            membership_type=MembershipType.regular,
            valid_until=timezone.now() - timezone.timedelta(days=10)
        )
        user = User.objects.create_user('exp-yesterday@user.user', password='fakefakefake')
        subscription = MembershipSubscription.objects.create(
            owner=user,
            membership_type=MembershipType.regular,
            valid_until=timezone.now() - timezone.timedelta(days=1)
        )
        user = User.objects.create_user('exp-in-an-hour@user.user', password='fakefakefake')
        subscription = MembershipSubscription.objects.create(
            owner=user,
            membership_type=MembershipType.regular,
            valid_until=timezone.now() + timezone.timedelta(hours=1)
        )
        user = User.objects.create_user('expires32days@user.user', password='fakefakefake')
        subscription = MembershipSubscription.objects.create(
            owner=user,
            membership_type=MembershipType.regular,
            valid_until=timezone.now() + timezone.timedelta(days=32)
        )
        user = User.objects.create_user('expires35days@user.user', password='fakefakefake')
        subscription = MembershipSubscription.objects.create(
            owner=user,
            membership_type=MembershipType.regular,
            valid_until=timezone.now() + timezone.timedelta(days=45)
        )
        user = User.objects.create_user('next0year@user.user', password='fakefakefake')
        subscription = MembershipSubscription.objects.create(
            owner=user,
            membership_type=MembershipType.regular,
            valid_until=timezone.now() + timezone.timedelta(days=365)
        )

        expemails = ExpiringEmails()
        emailcounter = 0
        jobs = [EXPIRING_THIS_MONTH, EXPIRED_LAST_MONTH, EXPIRED_PAST]
        for job in jobs:
            expiring_members = expemails.list_expiring_members(job['months'])
            for member in expiring_members:
                print(job['title'], member.email,
                      member.subscription.valid_until.strftime("%m/%d/%Y"))
                emailcounter += 1

        # ONLY 3 TEST USERS SHOULD PRODUCE AN EMAIL.
        self.assertEqual(emailcounter, 5)
