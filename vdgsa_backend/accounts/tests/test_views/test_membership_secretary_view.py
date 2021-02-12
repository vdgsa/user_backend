import csv
import tempfile
import time
from typing import List, Protocol, Sequence

from django.contrib.auth.models import Permission
from django.test.testcases import TestCase
from django.urls.base import reverse
from django.utils import timezone
from selenium.common.exceptions import NoSuchElementException  # type: ignore
from selenium.webdriver.remote.webelement import WebElement  # type: ignore
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore

from vdgsa_backend.accounts.models import MembershipSubscription, MembershipType, User
from vdgsa_backend.accounts.templatetags.filters import format_datetime_impl

from .selenium_test_base import SeleniumTestCaseBase


class AddUserTestCase(SeleniumTestCaseBase):
    def test_membership_secretary_sees_add_user_link(self) -> None:
        membership_secretary = self.make_membership_secretary()
        self.login_as(membership_secretary, dest_url='/accounts/directory')
        self.assertTrue(self.exists('#add-user-link'))

    def test_board_member_does_not_see_add_user_link(self) -> None:
        board_member = self.make_board_member()
        self.login_as(board_member, dest_url='/accounts/directory')
        self.assertFalse(self.exists('#add-user-link'))

    def test_membership_secretary_add_user_required_fields_only(self) -> None:
        membership_secretary = self.make_membership_secretary()
        self.login_as(membership_secretary, dest_url='/accounts/add_user')

        self.set_value('#id_username', 'an@user.com')
        self.set_value('#id_first_name', 'Lonk')
        self.set_value('#id_last_name', 'Zeldo')
        self.set_value('#id_address_line_1', '123 Lonk Ln')
        self.set_value('#id_address_city', 'Castle')
        self.set_value('#id_address_state', 'Hyrule')
        self.set_value('#id_address_postal_code', '98798')
        self.set_value('#id_address_country', 'Zeldoland')

        self.click_on(self.find('button[type=submit]'))
        self.assertEqual('an@user.com', self.get_value('#current-username'))

        user = User.objects.get(username='an@user.com')
        self.assertEqual('Lonk', user.first_name)
        self.assertEqual('Zeldo', user.last_name)
        self.assertEqual('123 Lonk Ln', user.address_line_1)
        self.assertEqual('Castle', user.address_city)
        self.assertEqual('Hyrule', user.address_state)
        self.assertEqual('98798', user.address_postal_code)
        self.assertEqual('Zeldoland', user.address_country)

    def test_membership_secretary_add_user_all_fields(self) -> None:
        membership_secretary = self.make_membership_secretary()
        self.login_as(membership_secretary, dest_url='/accounts/add_user')

        self.set_value('#id_username', 'sanic@user.com')
        self.set_value('#id_first_name', 'Lonk')
        self.set_value('#id_last_name', 'Zeldo')
        self.set_value('#id_address_line_1', '123 Lonk Ln')
        self.set_value('#id_address_line_2', 'Apt 7')
        self.set_value('#id_address_city', 'Castle')
        self.set_value('#id_address_state', 'Hyrule')
        self.set_value('#id_address_postal_code', '98798')
        self.set_value('#id_address_country', 'Zeldoland')
        self.set_value('#id_phone1', '1231231234')
        self.set_value('#id_phone2', '7897890789')

        self.click_on(self.find('button[type=submit]'))
        self.assertEqual('sanic@user.com', self.get_value('#current-username'))

        user = User.objects.get(username='sanic@user.com')
        self.assertEqual('Lonk', user.first_name)
        self.assertEqual('Zeldo', user.last_name)
        self.assertEqual('123 Lonk Ln', user.address_line_1)
        self.assertEqual('Apt 7', user.address_line_2)
        self.assertEqual('Castle', user.address_city)
        self.assertEqual('Hyrule', user.address_state)
        self.assertEqual('98798', user.address_postal_code)
        self.assertEqual('Zeldoland', user.address_country)
        self.assertEqual('1231231234', user.phone1)
        self.assertEqual('7897890789', user.phone2)

    def test_error_user_already_exists(self) -> None:
        username = 'waluigi@waa.com'
        User.objects.create(username=username)

        membership_secretary = self.make_membership_secretary()
        self.login_as(membership_secretary, dest_url='/accounts/add_user')

        self.set_value('#id_username', username)
        self.set_value('#id_first_name', 'Lonk')
        self.set_value('#id_last_name', 'Zeldo')
        self.set_value('#id_address_line_1', '123 Lonk Ln')
        self.set_value('#id_address_city', 'Castle')
        self.set_value('#id_address_state', 'Hyrule')
        self.set_value('#id_address_postal_code', '98798')
        self.set_value('#id_address_country', 'Zeldoland')

        self.click_on(self.find('button[type=submit]'))
        self.assertIn('User with this Email already exists', self.find('.form-field-errors').text)


class AddUserPermissionsTestCase(TestCase):
    def test_non_membership_secretary_add_user_permission_denied(self) -> None:
        board_member = User.objects.create_user(
            username=f'boardo@wee.com', password='password'
        )
        board_member.user_permissions.add(
            Permission.objects.get(codename='board_member')
        )

        self.client.force_login(board_member)
        response = self.client.get(reverse('add-user'))
        self.assertEqual(403, response.status_code)

        response = self.client.post(reverse('add-user'), {})
        self.assertEqual(403, response.status_code)

        user = User.objects.create_user(username='user@user.com')
        self.client.force_login(user)
        response = self.client.get(reverse('add-user'))
        self.assertEqual(403, response.status_code)

        response = self.client.post(reverse('add-user'), {})
        self.assertEqual(403, response.status_code)


class _TestData(Protocol):
    users: List[User]
    num_users: int
    num_active_users: int
    membership_secretary: User

    user0_expired_subscription: MembershipSubscription
    user4_current_subscription: MembershipSubscription
    user7_lifetime_subscription: MembershipSubscription


def _test_data_init(test_obj: _TestData) -> None:
    test_obj.num_users = 10
    # UPDATE ME if you change the MembershipSubscription objects
    test_obj.num_active_users = 2
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
        years_renewed=[2020]
    )
    test_obj.users[0].refresh_from_db()

    test_obj.user4_current_subscription = MembershipSubscription.objects.create(
        owner=test_obj.users[4],
        membership_type=MembershipType.student,
        valid_until=timezone.now() + timezone.timedelta(days=30),
        years_renewed=[2020]
    )
    test_obj.users[4].refresh_from_db()

    test_obj.user7_lifetime_subscription = MembershipSubscription.objects.create(
        owner=test_obj.users[7],
        membership_type=MembershipType.lifetime,
        valid_until=None,
        years_renewed=[2020]
    )
    test_obj.users[7].refresh_from_db()


class MembershipSecretaryDashboardUITestCase(SeleniumTestCaseBase):
    users: List[User]
    num_users: int
    num_active_users: int
    membership_secretary: User

    user0_expired_subscription: MembershipSubscription
    user4_current_subscription: MembershipSubscription
    user7_lifetime_subscription: MembershipSubscription

    def setUp(self) -> None:
        super().setUp()
        _test_data_init(self)

    def test_navigate_from_table_to_user_account(self) -> None:
        self.login_as(self.membership_secretary, dest_url='/accounts/directory/?all_users=true')
        self.click_on(self.find_all('.user-row')[3])
        self.assertEqual(self.users[3].username, self.get_value('#current-username'))

    def test_table_content(self) -> None:
        self.login_as(self.membership_secretary, dest_url='/accounts/directory/?all_users=true')
        user_rows = self.selenium.find_elements_by_class_name('user-row')
        self.assertEqual(len(self.users), len(user_rows))

        for (index, row) in enumerate(user_rows):
            cells = row.find_elements_by_css_selector('td')
            self.assertEqual(self.users[index].last_name, cells[0].text)  # last name
            self.assertEqual(self.users[index].first_name, cells[1].text)  # first name
            self.assertEqual(self.users[index].username, cells[2].text)  # email

        user0_subscription_cells = user_rows[0].find_elements_by_css_selector('td')
        self.assertIn('subscription-not-current', user_rows[0].get_attribute('class').split())
        self.assertEqual('regular', user0_subscription_cells[4].text)  # membership type
        assert self.users[0].subscription is not None
        self.assertEqual(
            format_datetime_impl(self.users[0].subscription.valid_until),
            user0_subscription_cells[5].text  # membership expires
        )
        self.assertNotEqual('', user0_subscription_cells[5].text)  # membership expires

        user4_subscription_cells = user_rows[4].find_elements_by_css_selector('td')
        self.assertNotIn('subscription-not-current', user_rows[4].get_attribute('class').split())
        self.assertEqual('student', user4_subscription_cells[4].text)  # membership type
        assert self.users[4].subscription is not None
        self.assertEqual(
            format_datetime_impl(self.users[4].subscription.valid_until),
            user4_subscription_cells[5].text  # membership expires
        )
        self.assertNotEqual('', user4_subscription_cells[5].text)  # membership expires

        user7_subscription_cells = user_rows[7].find_elements_by_css_selector('td')
        self.assertEqual('lifetime', user7_subscription_cells[4].text)  # membership type
        self.assertEqual('', user7_subscription_cells[5].text)  # membership expires

    def test_active_users_only(self) -> None:
        self.login_as(self.membership_secretary, dest_url='/accounts/directory/')
        user_rows = self.selenium.find_elements_by_class_name('user-row')
        self.assertEqual(self.num_active_users, len(user_rows))

        cells = user_rows[0].find_elements_by_css_selector('td')
        self.assertEqual(self.users[4].last_name, cells[0].text)  # last name
        self.assertEqual(self.users[4].first_name, cells[1].text)  # first name
        self.assertEqual(self.users[4].username, cells[2].text)  # email

        cells = user_rows[1].find_elements_by_css_selector('td')
        self.assertEqual(self.users[7].last_name, cells[0].text)  # last name
        self.assertEqual(self.users[7].first_name, cells[1].text)  # first name
        self.assertEqual(self.users[7].username, cells[2].text)  # email

    def test_navigation_between_all_and_active_users(self) -> None:
        self.login_as(self.membership_secretary, dest_url='/accounts/directory/')
        user_rows = self.selenium.find_elements_by_class_name('user-row')
        self.assertEqual(self.num_active_users, len(user_rows))

        wait = WebDriverWait(self.selenium, 5)

        self.selenium.find_element_by_id('all-users-toggle-link').click()
        wait.until(
            lambda _: (
                len(self.selenium.find_elements_by_class_name('user-row'))
                == self.num_users
            )
        )

        self.selenium.find_element_by_id('all-users-toggle-link').click()
        wait.until(
            lambda _: (
                len(self.selenium.find_elements_by_class_name('user-row'))
                == self.num_active_users
            )
        )

        self.selenium.find_element_by_id('all-users-toggle-link').click()
        wait.until(
            lambda _: (
                len(self.selenium.find_elements_by_class_name('user-row'))
                == self.num_users
            )
        )

    def test_filter_text(self) -> None:
        self.login_as(self.membership_secretary, dest_url='/accounts/directory/?all_users=true')
        user_rows = self.selenium.find_elements_by_class_name('user-row')
        self.assertEqual(len(self.users), len(user_rows))

        wait = WebDriverWait(self.selenium, 5)

        self.selenium.find_element_by_id('user-filter-input').send_keys(' regular')
        wait.until(
            lambda _: self.num_visible_elements(
                self.selenium.find_elements_by_class_name('user-row')
            ) == 1
        )
        self.assertEqual(
            1, self.num_visible_elements(self.selenium.find_elements_by_class_name('user-row')))

        self.selenium.find_element_by_id('user-filter-input').clear()
        # Should ignore case
        self.selenium.find_element_by_id('user-filter-input').send_keys('lasty 4  ')
        wait.until(
            lambda _: self.num_visible_elements(
                self.selenium.find_elements_by_class_name('user-row')
            ) == 1
        )
        self.assertEqual(
            1, self.num_visible_elements(self.selenium.find_elements_by_class_name('user-row')))

        self.selenium.find_element_by_id('user-filter-input').clear()
        self.selenium.find_element_by_id('user-filter-input').send_keys('Firsty 5')
        wait.until(
            lambda _: self.num_visible_elements(
                self.selenium.find_elements_by_class_name('user-row')
            ) == 1
        )
        self.assertEqual(
            1, self.num_visible_elements(self.selenium.find_elements_by_class_name('user-row')))

        self.selenium.find_element_by_id('user-filter-input').clear()
        self.selenium.find_element_by_id('user-filter-input').send_keys('nositenoriast')
        wait.until(
            lambda _: self.num_visible_elements(
                self.selenium.find_elements_by_class_name('user-row')
            ) == 0
        )
        self.assertEqual(
            0, self.num_visible_elements(self.selenium.find_elements_by_class_name('user-row')))

        self.selenium.find_element_by_id('user-filter-input').clear()
        self.selenium.find_element_by_id('user-filter-input').send_keys('  ')
        wait.until(
            lambda _: self.num_visible_elements(
                self.selenium.find_elements_by_class_name('user-row')
            ) == self.num_users
        )
        self.assertEqual(
            self.num_users,
            self.num_visible_elements(self.selenium.find_elements_by_class_name('user-row'))
        )

    def num_visible_elements(self, elements: Sequence[WebElement]) -> int:
        return sum(
            1 for item in elements if item.is_displayed()
        )

    def test_board_members_can_view_but_not_edit(self) -> None:
        self.login_as(self.make_board_member(), dest_url='/accounts/directory/?all_users=true')
        self.selenium.find_element_by_id('user-table')
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element_by_id('download-members-csv')

        self.selenium.find_elements_by_css_selector('.user-row td')[0].click()
        time.sleep(3)
        self.selenium.find_element_by_id('user-table')

    def test_non_membership_secretary_non_board_member_permission_denied(self) -> None:
        self.login_as(self.users[0], dest_url='/accounts/directory/')
        self.assertIn('Forbidden', self.selenium.find_element_by_css_selector('body').text)


class DownloadMembersSpreadsheetTestCase(TestCase):
    users: List[User]
    num_users: int
    num_active_users: int
    membership_secretary: User

    user0_expired_subscription: MembershipSubscription
    user4_current_subscription: MembershipSubscription
    user7_lifetime_subscription: MembershipSubscription

    def setUp(self) -> None:
        super().setUp()
        _test_data_init(self)

    def test_download_all(self) -> None:
        self.client.force_login(self.membership_secretary)
        response = self.client.get(reverse('all-users-csv') + '?all_users=true')
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

    def test_download_active_only(self) -> None:
        self.client.force_login(self.membership_secretary)
        response = self.client.get(reverse('all-users-csv'))

        with tempfile.TemporaryFile('w+') as f:
            f.write(response.content.decode())
            f.seek(0)
            reader = csv.reader(f)
            grid = [row[1:] for row in list(reader)[1:]]

        self.assertEqual(self.users[4].last_name, grid[0][0])  # last name
        self.assertEqual(self.users[4].first_name, grid[0][1])  # first name
        self.assertEqual(self.users[4].username, grid[0][2])  # email

        self.assertEqual(self.users[7].last_name, grid[1][0])  # last name
        self.assertEqual(self.users[7].first_name, grid[1][1])  # first name
        self.assertEqual(self.users[7].username, grid[1][2])  # email

    def test_download_all_non_membership_secretary_permission_denied(self) -> None:
        self.client.force_login(self.users[0])
        response = self.client.get(reverse('all-users-csv'))
        self.assertEqual(403, response.status_code)
