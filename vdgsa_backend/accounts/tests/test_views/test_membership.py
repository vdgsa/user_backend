from django.test import LiveServerTestCase, TestCase


class MembershipUITestCase(LiveServerTestCase):
    def test_purchase_subscription(self) -> None:
        self.fail()

    def test_renew_subscription(self) -> None:
        self.fail()

    def test_add_remove_family_members(self) -> None:
        self.fail()


class MembershipFormsPermission(TestCase):
    def test_membership_purchase_form_permissions(self) -> None:
        self.fail()

    def test_add_remove_family_permissions(self) -> None:
        self.fail()
