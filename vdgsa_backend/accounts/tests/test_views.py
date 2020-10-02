from django.test import TestCase


class UserViewTestCase(TestCase):
    def test_user_registration(self) -> None:
        self.fail()

    def test_membership_secretary_list_users(self) -> None:
        self.fail()

    def test_permission_denied_list_users(self) -> None:
        self.fail()

    def test_user_get_self(self) -> None:
        self.fail()

    def test_membership_secretary_get_user(self) -> None:
        self.fail()

    def test_permission_denied_user_get_other(self) -> None:
        self.fail()

    def test_user_update_self(self) -> None:
        self.fail()

    def test_membership_secretary_update_user(self) -> None:
        self.fail()

    def test_permission_denied_user_update_other(self) -> None:
        self.fail()


class MembershipSubscriptionViewTestCase(TestCase):
    def test_user_get_self_subscription_as_owner(self) -> None:
        self.fail()

    def test_user_get_self_subscription_as_family(self) -> None:
        self.fail()

    def test_membership_secretary_get_user_subscription(self) -> None:
        self.fail()

    def test_permission_denied_user_get_other_subscription(self) -> None:
        self.fail()

    # Note that this endpoint doesn't differentiate between purchasing
    # and renewing a subscription.
    def test_user_purchase_regular_subscription(self) -> None:
        self.fail()

    def test_user_purchase_student_subscription(self) -> None:
        self.fail()

    def test_permission_denied_user_purchase_for_other_user(self) -> None:
        self.fail()

    def test_membership_secretary_purchase_regular_subscription_for_user(self) -> None:
        self.fail()

    def test_membership_secretary_purchase_student_subscription_for_user(self) -> None:
        self.fail()

    def test_bad_request_purchase_subscription_for_lifetime_member(self) -> None:
        self.fail()

    def test_bad_request_purchase_lifetime_membership(self) -> None:
        self.fail()

    def test_bad_request_membership_type_not_included(self) -> None:
        self.fail()

    def test_purchase_subscription_with_donation(self) -> None:
        self.fail()

    def test_donation_amout_decimal_truncated(self) -> None:
        self.fail()

    def test_donation_zero_ignored(self) -> None:
        self.fail()

    def test_bad_request_donation_not_number(self) -> None:
        self.fail()

    def test_bad_request_donation_negative(self) -> None:
        self.fail()


class StripeWebhookViewTestCase(TestCase):
    def test_membership_payment_intent_succeeded(self) -> None:
        self.fail()

    def test_non_membership_payment_intent_succeeded_ignored(self) -> None:
        self.fail()

    def test_other_event_ignored(self) -> None:
        self.fail()
