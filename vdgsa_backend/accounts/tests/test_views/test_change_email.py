from django.contrib.auth.models import Permission
from django.test import LiveServerTestCase, TestCase

from vdgsa_backend.accounts.models import User


class ChangeEmailUITestCase(LiveServerTestCase):
    def test_change_email(self) -> None:
        self.fail()

    def test_membership_secretary_change_email(self) -> None:
        self.fail()


class ChangeEmailFormTestCase(TestCase):
    def test_change_email_permissions(self) -> None:
        self.fail()
