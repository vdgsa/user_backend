Skip to content
Search or jump to…
Pull requests
Issues
Marketplace
Explore
 
@ponticello 
vdgsa
/
user_backend
Public
Code
Issues
2
Pull requests
1
Actions
Projects
1
Wiki
Security
Insights
Settings
user_backend/vdgsa_backend/rental_viols/tests/test_views/test_rental_viewer_view.py /
@ponticello
ponticello Custodian detail - Viol status fix
Latest commit 7efa757 on Feb 5
 History
 1 contributor
119 lines (102 sloc)  3.53 KB
   
import csv
import tempfile
import time
from typing import List, Protocol, Sequence

from django.contrib.auth.models import Permission
from django.test.testcases import TestCase
from django.urls.base import reverse
from django.utils import timezone
from selenium.common.exceptions import NoSuchElementException  # type: ignore
from selenium.webdriver.common.by import By
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


class RentalViolLIstTestCase(SeleniumTestCaseBase):
    viols: List[Viol]
    rental_viewer: User

    def setUp(self) -> None:
        super().setUp()
        _test_data_init(self)

    def test_no_access_to_edit_page(self) -> None:
        self.login_as(self.rental_viewer, dest_url='/rentals/viols')
        self.selenium.find_element_by_id('viol-table')

        self.selenium.get(f'{self.live_server_url}' + reverse('viol-update', kwargs={
            'pk': self.viols[1].pk}))
        print('.current_url', self.selenium.current_url)

        try:
            self.selenium.find_element_by_id('viol-update-form')
        except NoSuchElementException:
            self.assertTrue(True)


class _TestData(Protocol):
    viols: List[Viol]
    bows: List[Bow]
    cases: List[Case]
    num_viols: int
    rental_viewer: User


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

    test_obj.rental_viewer = test_obj.users[-1]
    test_obj.rental_viewer.user_permissions.add(
        Permission.objects.get(codename='rental_viewer')
    )
© 2022 GitHub, Inc.
Terms
Privacy
Security
Status
Docs
Contact GitHub
Pricing
API
Training
Blog
About
Loading complete