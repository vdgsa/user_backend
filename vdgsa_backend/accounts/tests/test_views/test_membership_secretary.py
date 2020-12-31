import tempfile
import csv
from typing import List, Protocol, Sequence
from django.contrib.auth.models import Permission
from django.test.testcases import TestCase
from django.urls.base import reverse

from django.utils import timezone
from selenium.webdriver.remote.webelement import WebElement  # type: ignore

from vdgsa_backend.accounts.models import MembershipSubscription, MembershipType, User
from vdgsa_backend.accounts.templatetags.filters import format_datetime_impl

from .selenium_test_base import SeleniumTestCaseBase


class _TestData(Protocol):
    users: List[User]
    num_users: int
    membership_secretary: User

    user0_expired_subscription: MembershipSubscription
    user4_current_subscription: MembershipSubscription
    user7_lifetime_subscription: MembershipSubscription


def _test_data_init(test_obj: _TestData) -> None:
    test_obj.num_users = 10
    test_obj.users = [
        User.objects.create_user(
            username=f'user{i}@waa.com',
            first_name=f'Firsty {i}',
            last_name=f'Lasty {i}',
            password='password',
        )
        for i in range(test_obj.num_users)
    ]
    test_obj.membership_secretary = test_obj.users[-1]
    test_obj.membership_secretary.user_permissions.add(
        Permission.objects.get(codename='membership_secretary')
    )

    test_obj.user0_expired_subscription = MembershipSubscription.objects.create(
        owner=test_obj.users[0],
        membership_type=MembershipType.regular,
        valid_until=timezone.now() - timezone.timedelta(hours=1),
    )
    test_obj.users[0].refresh_from_db()

    test_obj.user4_current_subscription = MembershipSubscription.objects.create(
        owner=test_obj.users[4],
        membership_type=MembershipType.student,
        valid_until=timezone.now() + timezone.timedelta(days=30),
    )
    test_obj.users[4].refresh_from_db()

    test_obj.user7_lifetime_subscription = MembershipSubscription.objects.create(
        owner=test_obj.users[7],
        membership_type=MembershipType.lifetime,
        valid_until=None,
    )
    test_obj.users[7].refresh_from_db()


class MembershipSecretaryDashboardUITestCase(SeleniumTestCaseBase):
    users: List[User]
    num_users: int
    membership_secretary: User

    user0_expired_subscription: MembershipSubscription
    user4_current_subscription: MembershipSubscription
    user7_lifetime_subscription: MembershipSubscription

    def setUp(self) -> None:
        super().setUp()
        _test_data_init(self)

    def test_table_content(self) -> None:
        self.login_as(self.membership_secretary, dest_url='/accounts/membership_secretary/')
        user_rows = self.selenium.find_elements_by_class_name('user-row')
        self.assertEqual(len(self.users), len(user_rows))

        for (index, row) in enumerate(user_rows):
            cells = row.find_elements_by_css_selector('td')
            self.assertEqual(self.users[index].last_name, cells[0].text)  # last name
            self.assertEqual(self.users[index].first_name, cells[1].text)  # first name
            self.assertEqual(self.users[index].username, cells[2].text)  # email

        user0_subscription_cells = user_rows[0].find_elements_by_css_selector('td')
        self.assertIn('subscription-not-current', user_rows[0].get_attribute('class').split())
        self.assertEqual('regular', user0_subscription_cells[3].text)  # membership type
        assert self.users[0].subscription is not None
        self.assertEqual(
            format_datetime_impl(self.users[0].subscription.valid_until),
            user0_subscription_cells[4].text  # membership expires
        )
        self.assertNotEqual('', user0_subscription_cells[4].text)  # membership expires

        user4_subscription_cells = user_rows[4].find_elements_by_css_selector('td')
        self.assertNotIn('subscription-not-current', user_rows[4].get_attribute('class').split())
        self.assertEqual('student', user4_subscription_cells[3].text)  # membership type
        assert self.users[4].subscription is not None
        self.assertEqual(
            format_datetime_impl(self.users[4].subscription.valid_until),
            user4_subscription_cells[4].text  # membership expires
        )
        self.assertNotEqual('', user4_subscription_cells[4].text)  # membership expires

        user7_subscription_cells = user_rows[7].find_elements_by_css_selector('td')
        self.assertEqual('lifetime', user7_subscription_cells[3].text)  # membership type
        self.assertEqual('', user7_subscription_cells[4].text)  # membership expires

    def test_filter_text(self) -> None:
        self.login_as(self.membership_secretary, dest_url='/accounts/membership_secretary/')
        user_rows = self.selenium.find_elements_by_class_name('user-row')
        self.assertEqual(len(self.users), len(user_rows))

        self.selenium.find_element_by_id('user-filter-input').send_keys(' regular')
        self.assertEqual(
            1, self.num_visible_elements(self.selenium.find_elements_by_class_name('user-row')))

        self.selenium.find_element_by_id('user-filter-input').clear()
        # Should ignore case
        self.selenium.find_element_by_id('user-filter-input').send_keys('lasty 4  ')
        self.assertEqual(
            1, self.num_visible_elements(self.selenium.find_elements_by_class_name('user-row')))

        self.selenium.find_element_by_id('user-filter-input').clear()
        self.selenium.find_element_by_id('user-filter-input').send_keys('Firsty 5')
        self.assertEqual(
            1, self.num_visible_elements(self.selenium.find_elements_by_class_name('user-row')))

        self.selenium.find_element_by_id('user-filter-input').clear()
        self.selenium.find_element_by_id('user-filter-input').send_keys('nositenoriast')
        self.assertEqual(
            0, self.num_visible_elements(self.selenium.find_elements_by_class_name('user-row')))

        self.selenium.find_element_by_id('user-filter-input').clear()
        self.selenium.find_element_by_id('user-filter-input').send_keys('  ')
        self.assertEqual(
            self.num_users,
            self.num_visible_elements(self.selenium.find_elements_by_class_name('user-row'))
        )

    def num_visible_elements(self, elements: Sequence[WebElement]) -> int:
        return sum(
            1 for item in elements if item.is_displayed()
        )

    def test_non_membership_secretary_permission_denied(self) -> None:
        self.login_as(self.users[0], dest_url='/accounts/membership_secretary/')
        self.assertIn('Forbidden', self.selenium.find_element_by_css_selector('body').text)


class DownloadMembersSpreadsheetTestCase(TestCase):
    users: List[User]
    num_users: int
    membership_secretary: User

    user0_expired_subscription: MembershipSubscription
    user4_current_subscription: MembershipSubscription
    user7_lifetime_subscription: MembershipSubscription

    def setUp(self) -> None:
        super().setUp()
        _test_data_init(self)

    def test_download_all(self) -> None:
        self.client.force_login(self.membership_secretary)
        response = self.client.get(reverse('all-users-csv'))
        with tempfile.TemporaryFile('w+') as f:
            f.write(response.content.decode())
            f.seek(0)
            reader = csv.reader(f)
            grid = [row[1:] for row in list(reader)[1:]]

        for (index, row) in enumerate(grid):
            self.assertEqual(self.users[index].last_name, row[0])  # last name
            self.assertEqual(self.users[index].first_name, row[1])  # first name
            self.assertEqual(self.users[index].username, row[2])  # email

        self.assertEqual('regular', grid[0][3])  # membership type
        assert self.users[0].subscription is not None
        self.assertNotEqual('', grid[0][4])  # membership expires
        self.assertEqual(
            format_datetime_impl(self.users[0].subscription.valid_until),
            grid[0][4]  # membership expires
        )

        self.assertEqual('student', grid[4][3])  # membership type
        assert self.users[4].subscription is not None
        self.assertNotEqual('', grid[4][4])  # membership expires
        self.assertEqual(
            format_datetime_impl(self.users[4].subscription.valid_until),
            grid[4][4]  # membership expires
        )

        self.assertEqual('lifetime', grid[7][3])  # membership type
        self.assertEqual('', grid[7][4])  # membership expires

    def test_download_all_non_membership_secretary_permission_denied(self) -> None:
        self.client.force_login(self.users[0])
        response = self.client.get(reverse('all-users-csv'))
        self.assertEqual(403, response.status_code)
