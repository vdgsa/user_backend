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
from vdgsa_backend.rental_viols.models import Viol, Bow, Case, RentalProgram
from vdgsa_backend.rental_viols.managers.InstrumentManager import (AccessoryManager, ImageManager, 
                                                                   ViolManager, ViolSize)
from vdgsa_backend.rental_viols.managers.RentalItemBaseManager import (RentalState)
from vdgsa_backend.templatetags.filters import format_datetime_impl

from .selenium_test_rental_base import SeleniumTestCaseBase


class AddUserTestCase(SeleniumTestCaseBase):
    def test_rental_manager_sees_link(self) -> None:
        rental_manager = self.make_rental_manager()
        self.login_as(rental_manager, dest_url='/')
        self.assertTrue(self.exists('#add-user-link'))


class _TestData(Protocol):
    viols: List[User]
    num_viols: int
    num_active_users: int
    rental_manager: User

    exampleViol: Viol
    exampleBow: Bow
    exampleCase: Case


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
        for i in range(test_obj.num_users)
    ]
    test_obj.rental_manager = test_obj.users[-1]
    test_obj.rental_manager.user_permissions.add(
        Permission.objects.get(codename='rental_manager')
    )

