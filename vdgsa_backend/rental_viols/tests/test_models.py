from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone

from vdgsa_backend.rental_viols.models import Bow, Case, Viol, RentalHistory, WaitingList, ViolSize, RentalProgram


vdgsa_number = 22
maker = 'maker'
size = ViolSize.bass
state = 'state'
value = 1234.56
provenance = 'provenance'
description = 'Description'
accession_date = timezone.now()
program = default = RentalProgram.regular


class ViolTestCase(TestCase):
    def test_create_viol(self) -> None:
        newbow = Bow.objects.create(
            vdgsa_number=1234,
            maker='maker',
            size=ViolSize.bass,
            state='state',
            value=1234.56,
            provenance='provenance',
            description='Description',
            accession_date=timezone.now(),
            program=RentalProgram.regular)
        newbow.refresh_from_db()
        print(newbow)
        self.assertEqual(1234, newbow.vdgsa_number)
        self.assertTrue(newbow.value)
        self.assertIsNotNone(newbow.bow_num)
