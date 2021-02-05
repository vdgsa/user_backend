from unittest.case import skip
from django.test import LiveServerTestCase, TestCase


@skip('TODO')
class UserProfileFormUI(LiveServerTestCase):
    def test_contact_info(self) -> None:
        self.fail()

    def test_affiliations(self) -> None:
        self.fail()

    def test_teachers(self) -> None:
        self.fail()

    def test_commercial_members(self) -> None:
        self.fail()

    def test_privacy(self) -> None:
        self.fail()


@skip('TODO')
class UserProfileFormPermissions(TestCase):
    def test_user_profile_form_permissions(self) -> None:
        self.fail()
