from django.test import TestCase
from django.utils import timezone

from vdgsa_backend.rental_viols.managers.InstrumentManager import ViolSize
from vdgsa_backend.rental_viols.models import Bow, Case, RentalProgram, Viol


class ViolTestCase(TestCase):
    def test_create_viol(self) -> None:
        newviol = Viol.objects.create(
            vdgsa_number=1234,
            maker='maker',
            size=ViolSize.bass,
            strings=6,
            state='state',
            value=1234.56,
            provenance='provenance',
            description='Description',
            accession_date=timezone.now(),
            program=RentalProgram.regular)
        newviol.refresh_from_db()
        print(newviol)
        self.assertEqual(1234, newviol.vdgsa_number)
        self.assertTrue(newviol.value)
        self.assertIsNotNone(newviol.viol_num)


class BowTestCase(TestCase):
    def test_create_bow(self) -> None:
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


class CaseTestCase(TestCase):
    def test_create_case(self) -> None:
        newcase = Case.objects.create(
            vdgsa_number=1234,
            maker='Acme',
            size=ViolSize.bass,
            state='state',
            value=1234.56,
            provenance='provenance',
            description='Description',
            accession_date=timezone.now(),
            program=RentalProgram.regular)
        newcase.refresh_from_db()
        print(newcase)
        self.assertEqual(1234, newcase.vdgsa_number)
        self.assertTrue(newcase.value)
        self.assertIsNotNone(newcase.case_num)


class AttachTestCase(TestCase):
    def test_attachBow(self) -> None:
        newviol = Viol.objects.create(
            vdgsa_number=12345,
            maker='maker',
            size=ViolSize.bass,
            strings=6,
            state='state',
            value=1234.56,
            provenance='provenance',
            description='Description',
            accession_date=timezone.now(),
            program=RentalProgram.regular)
        newviol.refresh_from_db()

        newbow = Bow.objects.create(
            vdgsa_number=33,
            maker='maker',
            size=ViolSize.bass,
            state='state',
            value=1234.56,
            provenance='provenance',
            description='Description',
            accession_date=timezone.now(),
            program=RentalProgram.regular)
        newbow.refresh_from_db()

        newviol.bows.add(newbow)
        newviol.save()
        print(newbow.viol_num.bows.exists())
        self.assertTrue(newbow.viol_num.bows.exists())
        self.assertEquals(newbow.viol_num.vdgsa_number, 12345)
