from typing import Any, List, Union

from django.contrib.auth.models import Permission
from django.test import LiveServerTestCase
from selenium.common.exceptions import NoSuchElementException  # type: ignore
from selenium.webdriver.common.action_chains import ActionChains  # type: ignore
from selenium.webdriver.firefox.webdriver import WebDriver  # type: ignore
from selenium.webdriver.support import expected_conditions as EC  # type: ignore
from selenium.webdriver.support.wait import WebDriverWait  # type: ignore

from vdgsa_backend.accounts.models import MembershipSubscription, MembershipType, User


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

    def make_conclave_team(self) -> User:
        conclave_team = User.objects.create_user(
            username=f'boardo@wee.com', password='password'
        )
        conclave_team.user_permissions.add(
            Permission.objects.get(codename='conclave_team')
        )
        MembershipSubscription.objects.create(
            owner=conclave_team, membership_type=MembershipType.lifetime)
        return conclave_team

    def find(self, selector: str) -> Any:
        """
        Alias for self.selenium.find_element_by_css_selector('selector')
        """
        return self.selenium.find_element_by_css_selector(selector)

    def find_all(self, selector: str) -> Union[List[Any], Any]:
        """
        Alias for self.selenium.find_elements_by_css_selector('selector')
        """
        return self.selenium.find_elements_by_css_selector(selector)

    def exists(self, selector: str) -> bool:
        """
        Returns True if the element identified by selector exists.
        """
        try:
            self.selenium.find_element_by_css_selector(selector)
            return True
        except NoSuchElementException:
            return False

    def get_value(self, selector: str) -> Any:
        """
        Returns the "value" attribute of the element identified by selector.
        """
        return self.find(selector).get_attribute('value')

    def set_value(self, selector: str, text: str) -> None:
        """
        Clears the current value and sets the given text using send_keys.
        """
        element = self.find(selector)
        element.clear()
        element.send_keys(text)

    def click_on(self, element: Any) -> None:
        try:
            element.click()
        except Exception:
            ActionChains(self.selenium).move_to_element(element).click().perform()

    def accept_alert(self) -> None:
        self.wait.until(EC.alert_is_present())
        alert = self.selenium.switch_to.alert
        alert.accept()
