from vdgsa_backend.accounts.models import User
from app_backend.vdgsa_backend.testing.playwright_test_base import (
    PlaywrightDriver, PlaywrightTestCase as BrowserTestCase
)


class PlaywrightTestCase(BrowserTestCase):
    test_password = 'valid-password'
    users: list[User]

    def setUp(self) -> None:
        super().setUp()
        self.users = [
            User.objects.create_user(
                username=f'playwright-user-{index + 1}@example.com',
                password=self.test_password
            )
            for index in range(10)
        ]

    def start_browser(self) -> PlaywrightDriver:
        return self.selenium
