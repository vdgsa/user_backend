from concurrent.futures import Future
from queue import Queue
import re
import time
from threading import Event, Thread
from typing import Any, Callable, List, Optional, Tuple

from django.contrib.auth.models import Permission
from django.test import LiveServerTestCase
from playwright.sync_api import (
    Dialog, Locator, Page, TimeoutError as PlaywrightTimeoutError, sync_playwright
)

from vdgsa_backend.accounts.models import MembershipSubscription, MembershipType, User

LocatorPath = Tuple[Tuple[str, Optional[int]], ...]


class NoSuchElementException(Exception):
    pass


class NoAlertPresentException(Exception):
    pass


class LocatorStrategy:
    ID = 'id'
    NAME = 'name'
    CLASS_NAME = 'class name'
    TAG_NAME = 'tag name'
    CSS_SELECTOR = 'css selector'


class PlaywrightWait:
    def __init__(self, timeout: float = 5, poll_interval: float = 0.1) -> None:
        self.timeout = timeout
        self.poll_interval = poll_interval

    def until(self, condition: Callable[[Any], Any]) -> Any:
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                result = condition(None)
                if result:
                    return result
            except (NoSuchElementException, PlaywrightTimeoutError):
                pass
            if time.monotonic() >= deadline:
                raise TimeoutError(f'Timed out after {self.timeout} seconds')
            time.sleep(self.poll_interval)


class _PlaywrightBrowser:
    def __init__(self) -> None:
        self._requests: Queue[object] = Queue()
        self._ready = Event()
        self._startup_error: Optional[BaseException] = None
        self._thread = Thread(target=self._run, daemon=True)
        self._dialog: Optional[Dialog] = None
        self._thread.start()
        self._ready.wait()
        if self._startup_error is not None:
            raise self._startup_error

    def _run(self) -> None:
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                page = browser.new_page()
                page.set_default_timeout(5000)
                page.on('dialog', self._remember_dialog)
                self._ready.set()
                while True:
                    request = self._requests.get()
                    if request is None:
                        break
                    operation, result = request
                    try:
                        result.set_result(operation(page))
                    except BaseException as error:
                        result.set_exception(error)
                browser.close()
        except BaseException as error:
            self._startup_error = error
            self._ready.set()

    def _remember_dialog(self, dialog: Dialog) -> None:
        self._dialog = dialog

    def call(self, operation: Callable[[Page], Any]) -> Any:
        result: Future[Any] = Future()
        self._requests.put((operation, result))
        return result.result()

    def close(self) -> None:
        self._requests.put(None)
        self._thread.join()


class PlaywrightElement:
    def __init__(self, browser: _PlaywrightBrowser, path: LocatorPath) -> None:
        self._browser = browser
        self._path = path

    def _with_locator(self, operation: Callable[[Locator], Any]) -> Any:
        def run(page: Page) -> Any:
            locator: Any = page
            for selector, index in self._path:
                locator = locator.locator(selector)
                if index is not None:
                    locator = locator.nth(index)
            return operation(locator)

        return self._browser.call(run)

    @property
    def text(self) -> str:
        text = self._with_locator(
            lambda locator: locator.evaluate(
                '(element) => element.innerText || element.textContent || ""'
            )
        )
        return re.sub(r'\s+', ' ', text).strip()

    @property
    def tag_name(self) -> str:
        return self._with_locator(
            lambda locator: locator.evaluate('(element) => element.tagName.toLowerCase()')
        )

    def click(self) -> None:
        def click(locator: Locator) -> None:
            if locator.evaluate('(element) => element.tagName') == 'OPTION':
                locator.evaluate(
                    '(option) => { option.selected = true; '
                    'option.parentElement.dispatchEvent(new Event("change", { bubbles: true })); }'
                )
            else:
                locator.click()

        self._with_locator(click)

    def clear(self) -> None:
        def clear(locator: Locator) -> None:
            if locator.evaluate('(element) => element.tagName') == 'SELECT':
                if locator.locator('option[value=""]').count():
                    locator.select_option(value='')
            else:
                locator.fill('')

        self._with_locator(clear)

    def send_keys(self, text: str) -> None:
        def send(locator: Locator) -> None:
            if locator.evaluate('(element) => element.tagName') == 'SELECT':
                options = locator.locator('option').evaluate_all(
                    '(options) => options.map((option) => ({label: option.label, value: option.value}))'
                )
                match = next(
                    (
                        option for option in options
                        if option['label'] == text or option['value'] == text
                    ),
                    None
                )
                if match is not None:
                    locator.select_option(value=match['value'])
            else:
                locator.press_sequentially(text)

        self._with_locator(send)

    def get_attribute(self, name: str) -> Optional[str]:
        def get(locator: Locator) -> Optional[str]:
            tag_name = locator.evaluate('(element) => element.tagName.toLowerCase()')
            if name == 'value' and tag_name in {'input', 'textarea', 'select'}:
                return locator.input_value()
            return locator.get_attribute(name)

        return self._with_locator(get)

    def is_displayed(self) -> bool:
        return self._with_locator(lambda locator: locator.is_visible())

    def is_enabled(self) -> bool:
        return self._with_locator(lambda locator: locator.is_enabled())

    def is_selected(self) -> bool:
        return self._with_locator(
            lambda locator: locator.evaluate(
                "(element) => 'checked' in element ? element.checked : Boolean(element.selected)"
            )
        )

    def find_element_by_css_selector(self, selector: str) -> 'PlaywrightElement':
        return _first_element(self._browser, self._path + ((selector, None),))

    def find_elements_by_css_selector(self, selector: str) -> List['PlaywrightElement']:
        return _elements(self._browser, self._path + ((selector, None),))

    def find_elements_by_tag_name(self, tag_name: str) -> List['PlaywrightElement']:
        return self.find_elements_by_css_selector(tag_name)


class _SwitchTo:
    def __init__(self, page: 'PlaywrightPage') -> None:
        self.page = page

    @property
    def alert(self) -> 'PlaywrightAlert':
        if not self.page._browser.call(
            lambda _page: self.page._browser._dialog is not None
        ):
            raise NoAlertPresentException()
        return PlaywrightAlert(self.page._browser)


class PlaywrightAlert:
    def __init__(self, browser: _PlaywrightBrowser) -> None:
        self._browser = browser

    def accept(self) -> None:
        def accept(_page: Page) -> None:
            dialog = self._browser._dialog
            if dialog is None:
                raise NoAlertPresentException()
            dialog.accept()
            self._browser._dialog = None

        self._browser.call(accept)


class PlaywrightPage:
    def __init__(self, browser: _PlaywrightBrowser) -> None:
        self._browser = browser
        self.switch_to = _SwitchTo(self)

    @property
    def alert_present(self) -> bool:
        return self._browser.call(
            lambda _page: self._browser._dialog is not None
        )

    def get(self, url: str) -> None:
        self._browser.call(lambda page: page.goto(url, wait_until='load'))

    def refresh(self) -> None:
        self._browser.call(lambda page: page.reload(wait_until='load'))

    @property
    def current_url(self) -> str:
        return self._browser.call(lambda page: page.url)

    def implicitly_wait(self, _seconds: int) -> None:
        self._browser.call(lambda page: page.set_default_timeout(5000))

    def find_element(self, by: str, value: str) -> PlaywrightElement:
        return _first_element(self._browser, ((self._selector(by, value), 0),))

    def find_elements(self, by: str, value: str) -> List[PlaywrightElement]:
        return _elements(self._browser, ((self._selector(by, value), None),))

    def _selector(self, by: str, value: str) -> str:
        if by == LocatorStrategy.ID:
            return f'#{value}'
        if by == LocatorStrategy.NAME:
            return f'[name="{value}"]'
        if by == LocatorStrategy.CLASS_NAME:
            return f'.{value}'
        if by in {LocatorStrategy.TAG_NAME, LocatorStrategy.CSS_SELECTOR}:
            return value
        raise ValueError(f'Unsupported locator strategy: {by}')

    def find_element_by_id(self, element_id: str) -> PlaywrightElement:
        return self.find_element(LocatorStrategy.ID, element_id)

    def find_elements_by_id(self, element_id: str) -> List[PlaywrightElement]:
        return self.find_elements(LocatorStrategy.ID, element_id)

    def find_element_by_name(self, name: str) -> PlaywrightElement:
        return self.find_element(LocatorStrategy.NAME, name)

    def find_elements_by_name(self, name: str) -> List[PlaywrightElement]:
        return self.find_elements(LocatorStrategy.NAME, name)

    def find_element_by_class_name(self, class_name: str) -> PlaywrightElement:
        return self.find_element(LocatorStrategy.CLASS_NAME, class_name)

    def find_elements_by_class_name(self, class_name: str) -> List[PlaywrightElement]:
        return self.find_elements(LocatorStrategy.CLASS_NAME, class_name)

    def find_element_by_tag_name(self, tag_name: str) -> PlaywrightElement:
        return self.find_element(LocatorStrategy.TAG_NAME, tag_name)

    def find_elements_by_tag_name(self, tag_name: str) -> List[PlaywrightElement]:
        return self.find_elements(LocatorStrategy.TAG_NAME, tag_name)

    def find_element_by_css_selector(self, selector: str) -> PlaywrightElement:
        return self.find_element(LocatorStrategy.CSS_SELECTOR, selector)

    def find_elements_by_css_selector(self, selector: str) -> List[PlaywrightElement]:
        return self.find_elements(LocatorStrategy.CSS_SELECTOR, selector)

    def execute_script(self, script: str, *args: Any) -> Any:
        return self._browser.call(lambda page: page.evaluate(script, *args))


def _first_element(browser: _PlaywrightBrowser, path: LocatorPath) -> PlaywrightElement:
    try:
        browser.call(
            lambda page: _resolve(page, path).wait_for(state='attached', timeout=5000)
        )
    except PlaywrightTimeoutError:
        raise NoSuchElementException()
    return PlaywrightElement(browser, path)


def _elements(browser: _PlaywrightBrowser, path: LocatorPath) -> List[PlaywrightElement]:
    count = browser.call(lambda page: _resolve(page, path).count())
    return [
        PlaywrightElement(browser, path[:-1] + ((path[-1][0], index),))
        for index in range(count)
    ]


def _resolve(page: Page, path: LocatorPath) -> Locator:
    locator: Any = page
    for selector, index in path:
        locator = locator.locator(selector)
        if index is not None:
            locator = locator.nth(index)
    return locator


class PlaywrightTestCase(LiveServerTestCase):
    browser: Optional[_PlaywrightBrowser] = None
    page: PlaywrightPage
    wait: PlaywrightWait

    def setUp(self) -> None:
        super().setUp()
        browser = _PlaywrightBrowser()
        self.browser = browser
        self.page = PlaywrightPage(browser)
        self.wait = PlaywrightWait(5)

    def tearDown(self) -> None:
        if self.browser is not None:
            self.browser.close()
        super().tearDown()

    def login_as(
        self,
        user: User,
        dest_url: str = '/accounts/',
        password: str = 'password'
    ) -> None:
        self.page.get(f'{self.live_server_url}{dest_url}')
        self.page.find_element_by_id('id_username').send_keys(user.username)
        self.page.find_element_by_id('id_password').send_keys(password)
        self.page.find_element_by_css_selector('button[type=submit]').click()

    def find(self, selector: str) -> PlaywrightElement:
        return self.page.find_element_by_css_selector(selector)

    def find_all(self, selector: str) -> List[PlaywrightElement]:
        return self.page.find_elements_by_css_selector(selector)

    def exists(self, selector: str) -> bool:
        return bool(self.page.find_elements_by_css_selector(selector))

    def get_value(self, selector: str) -> Optional[str]:
        return self.find(selector).get_attribute('value')

    def set_value(self, selector: str, text: str) -> None:
        element = self.find(selector)
        element.clear()
        element.send_keys(text)

    def click_on(self, element: PlaywrightElement) -> None:
        element.click()

    def accept_alert(self) -> None:
        self.wait.until(lambda _driver: self.browser is not None
                        and self.browser.call(lambda _page: self.browser._dialog is not None))
        self.page.switch_to.alert.accept()

    def _make_user_with_permission(
        self, username: str, permission_codename: str
    ) -> User:
        user = User.objects.create_user(username=username, password='password')
        user.user_permissions.add(Permission.objects.get(codename=permission_codename))
        return user

    def make_membership_secretary(self) -> User:
        return self._make_user_with_permission('memsec@wee.com', 'membership_secretary')

    def make_board_member(self) -> User:
        return self._make_user_with_permission('boardo@wee.com', 'board_member')

    def make_rental_manager(self) -> User:
        return self._make_user_with_permission('rental_manager@wee.com', 'rental_manager')

    def make_rental_viewer(self) -> User:
        return self._make_user_with_permission('rental_viewer@wee.com', 'rental_viewer')

    def make_conclave_team(self) -> User:
        user = self._make_user_with_permission('conclave@wee.com', 'conclave_team')
        MembershipSubscription.objects.create(
            owner=user, membership_type=MembershipType.lifetime
        )
        return user
