from typing import Any, List, Optional, Union

from django.contrib.auth.models import Permission
from django.test import LiveServerTestCase
from selenium.common.exceptions import NoSuchElementException  # type: ignore
from selenium.webdriver.firefox.webdriver import WebDriver  # type: ignore
from selenium.webdriver.support.wait import WebDriverWait  # type: ignore

from vdgsa_backend.accounts.models import User


class SeleniumTestCaseBase(LiveServerTestCase):
    selenium: WebDriver
    wait: WebDriverWait

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self) -> None:
        super().setUp()
        self.wait = WebDriverWait(self.selenium, 5)

    def login_as(
        self,
        user: User,
        dest_url: str = '/accounts/',
        password: str = 'password'
    ) -> None:
        """
        Visit dest_url in selenium, get redirected to login page,
        login as the specified user, get redirected back to dest_url.
        """
        self.selenium.get(f'{self.live_server_url}{dest_url}')
        self.selenium.find_element_by_id('id_username').send_keys(user.username)
        self.selenium.find_element_by_id('id_password').send_keys(password)
        self.selenium.find_element_by_css_selector('button[type=submit]').click()

    def make_membership_secretary(self) -> User:
        membership_secretary = User.objects.create_user(
            username=f'memsec@wee.com', password='password'
        )
        membership_secretary.user_permissions.add(
            Permission.objects.get(codename='membership_secretary')
        )
        return membership_secretary

    def make_board_member(self) -> User:
        board_member = User.objects.create_user(
            username=f'boardo@wee.com', password='password'
        )
        board_member.user_permissions.add(
            Permission.objects.get(codename='board_member')
        )
        return board_member

    def find(self, selector: str) -> Optional[Any]:
        """
        Returns the element identified by selector.
        If no such element exists, returns None.
        """
        try:
            return self.selenium.find_element_by_css_selector(selector)
        except NoSuchElementException:
            return None

    def find_all(self, selector: str) -> Union[List[Any], Any]:
        """
        Alias for self.selenium.find_elements_by_css_selector('selector')
        """
        return self.selenium.find_elements_by_css_selector(selector)

    def exists(self, selector: str) -> bool:
        """
        Returns True if the element identified by selector exists.
        """
        return self.find(selector) is not None

    # def get_value(self, selector: str) -> str:
    #     """
    #     Returns the "value" attribute of the element identified by selector.
    #     """
    #     return self.find(selector).val
