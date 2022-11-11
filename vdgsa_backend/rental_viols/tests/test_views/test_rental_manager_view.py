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

from vdgsa_backend.accounts.models import User
from vdgsa_backend.rental_viols.managers.InstrumentManager import (
    AccessoryManager, ImageManager, ViolManager, ViolSize
)
from vdgsa_backend.rental_viols.managers.RentalItemBaseManager import RentalState
from vdgsa_backend.rental_viols.models import Bow, Case, RentalProgram, Viol
from vdgsa_backend.templatetags.filters import format_datetime_impl

from .selenium_test_rental_base import SeleniumTestCaseBase


class RentalHomeTestCase(SeleniumTestCaseBase):
    viols: List[Viol]
    rental_manager: User

    def setUp(self) -> None:
        super().setUp()
        _test_data_init(self)

    def test_rental_manager_sees_link(self) -> None:
        rental_manager = self.make_rental_manager()
        self.login_as(rental_manager, dest_url='/rentals')
        self.assertTrue(self.exists('#viols-home-link'))
        self.selenium.get(f'{self.live_server_url}' + reverse('viol-update', kwargs={
            'pk': self.viols[1].pk}))


class RentalViolManagerTestCase(SeleniumTestCaseBase):
    viols: List[Viol]
    rental_manager: User

    def setUp(self) -> None:
        super().setUp()
        _test_data_init(self)

    def test_access_to_edit_page(self) -> None:
        print('Rental Manager: test_access_to_edit_page')
        self.login_as(self.rental_manager, dest_url='/rentals/viols')
        self.selenium.find_element_by_id('viol-table')


class _TestData(Protocol):
    viols: List[Viol]
    bows: List[Bow]
    cases: List[Case]
    num_viols: int
    rental_manager: User


def _test_data_init(test_obj: _TestData) -> None:
    test_obj.num_viols = 10
    test_obj.viols = [
        Viol.objects.create(
            vdgsa_number=1234,
            maker='maker',
            size=ViolSize.bass,
            state='state',
            value=1234.56,
            provenance='provenance',
            description='Description',
            accession_date=timezone.now(),
            program=RentalProgram.regular,
            strings=6
        )
        for i in range(test_obj.num_viols)
    ]

    test_obj.bows = [
        Bow.objects.create(
            vdgsa_number=1234,
            maker='maker',
            size=ViolSize.bass,
            state='state',
            value=1234.56,
            provenance='provenance',
            description='Description',
            accession_date=timezone.now(),
            program=RentalProgram.regular
        )
        for i in range(3)
    ]

    test_obj.cases = [
        Case.objects.create(
            vdgsa_number=1234,
            maker='maker',
            size=ViolSize.bass,
            state='state',
            value=1234.56,
            provenance='provenance',
            description='Description',
            accession_date=timezone.now(),
            program=RentalProgram.regular
        )
        for i in range(5)
    ]

    test_obj.num_users = 10
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

    test_obj.rental_manager = test_obj.users[-1]
    test_obj.rental_manager.user_permissions.add(
        Permission.objects.get(codename='rental_manager')
    )
