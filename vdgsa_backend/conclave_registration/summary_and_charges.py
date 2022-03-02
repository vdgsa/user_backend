"""
Contains business logic for summarizing registration choices and
charges. Provides top-level methods that return those summaries as
dictionaries that can be rendered with simple templates for display
on the "Summary" page and in confirmation emails.
"""

from __future__ import annotations

from typing import TypedDict

from vdgsa_backend.conclave_registration.models import (
    ConclaveRegistrationConfig, Housing, HousingRoomType, Program, RegistrationEntry,
    RegularProgramClassChoices, TShirts, YesNo
)


class ChargesSummary(TypedDict):
    charges: list[ChargeInfo]
    apply_work_study_scholarship: bool
    apply_housing_subsidy: bool
    apply_canadian_discount: bool
    subtotal: int
    total: int


class ChargeInfo(TypedDict):
    display_name: str
    amount: int


def get_charges_summary(registration_entry: RegistrationEntry) -> ChargesSummary:
    conclave_config: ConclaveRegistrationConfig = registration_entry.conclave_config
    charges: list[ChargeInfo] = []

    if (tuition_charge := get_tuition_charge(registration_entry)) is not None:
        charges.append(tuition_charge)

    if (add_on_class_charge := get_add_on_class_charge(registration_entry)) is not None:
        charges.append(add_on_class_charge)

    if (housing_charge := get_housing_charge(registration_entry)) is not None:
        charges.append(housing_charge)

    if (hasattr(registration_entry, 'housing')
            and registration_entry.housing.is_bringing_guest_to_banquet == YesNo.yes):
        charges.append({
            'display_name': 'Banquet Guest Fee',
            'amount': conclave_config.banquet_guest_fee
        })

    if (tshirts_charge := get_tshirts_charge(registration_entry)) is not None:
        charges.append(tshirts_charge)

    if (donation_charge := get_donation_charge(registration_entry)) is not None:
        charges.append(donation_charge)

    if registration_entry.is_late:
        charges.append({
            'display_name': 'Late Registration Fee',
            'amount': conclave_config.late_registration_fee
        })

    apply_work_study_scholarship = (
        hasattr(registration_entry, 'work_study')
        and registration_entry.work_study.wants_work_study == YesNo.yes
    )
    apply_housing_subsidy = (
        hasattr(registration_entry, 'housing')
        and registration_entry.housing.wants_housing_subsidy
    )
    apply_canadian_discount = (
        hasattr(registration_entry, 'housing')
        and registration_entry.housing.wants_canadian_currency_exchange_discount
    )

    subtotal = sum(charge['amount'] for charge in charges)
    if apply_work_study_scholarship:
        subtotal -= conclave_config.work_study_scholarship_amount
    if apply_housing_subsidy:
        subtotal -= conclave_config.housing_subsidy_amount

    total = subtotal
    if apply_canadian_discount:
        total *= 1 - conclave_config.canadian_discount_percent / 100
        total = int(total)  # round down
    return {
        'charges': charges,
        'apply_work_study_scholarship': apply_work_study_scholarship,
        'apply_housing_subsidy': apply_housing_subsidy,
        'apply_canadian_discount': apply_canadian_discount,
        'subtotal': subtotal,
        'total': total,
    }


def get_tuition_charge(registration_entry: RegistrationEntry) -> ChargeInfo | None:
    conclave_config: ConclaveRegistrationConfig = registration_entry.conclave_config
    display_name = f'Tuition ({Program(registration_entry.program).label})'

    match(registration_entry.program):
        case Program.regular:
            return {
                'display_name': display_name,
                'amount': conclave_config.regular_tuition
            }
        case Program.part_time:
            return {
                'display_name': display_name,
                'amount': conclave_config.part_time_tuition
            }
        case Program.consort_coop:
            return {
                'display_name': display_name,
                'amount': conclave_config.consort_coop_tuition
            }
        case Program.seasoned_players:
            return {
                'display_name': display_name,
                'amount': conclave_config.seasoned_players_tuition
            }
        case Program.beginners:
            return {
                'display_name': display_name,
                'amount': 0
            }
        case Program.faculty_guest_other:
            return None
        case Program.non_playing_attendee:
            return {
                'display_name': display_name,
                'amount': conclave_config.non_playing_attendee_fee
            }
        case _:
            assert False


def get_add_on_class_charge(registration_entry: RegistrationEntry) -> ChargeInfo | None:
    conclave_config: ConclaveRegistrationConfig = registration_entry.conclave_config
    if not hasattr(registration_entry, 'regular_class_choices'):
        return None
    class_choices: RegularProgramClassChoices = registration_entry.regular_class_choices

    match(registration_entry.program):
        case Program.beginners if registration_entry.wants_extra_beginner_class == YesNo.yes:
            return {
                'display_name': 'Beginners+ Add-On Class',
                'amount': conclave_config.beginners_extra_class_fee
            }
        case Program.consort_coop if class_choices.num_non_freebie_classes == 1:
            return {
                'display_name': '1 Add-On Class',
                'amount': conclave_config.consort_coop_one_extra_class_fee
            }
        case Program.consort_coop if class_choices.num_non_freebie_classes == 2:
            return {
                'display_name': '2 Add-On Classes',
                'amount': conclave_config.consort_coop_two_extra_classes_fee
            }
        case Program.seasoned_players if class_choices.num_non_freebie_classes == 1:
            return {
                'display_name': '1 Add-On Class',
                'amount': conclave_config.seasoned_players_extra_class_fee
            }

    return None


def get_housing_charge(registration_entry: RegistrationEntry) -> ChargeInfo | None:
    conclave_config: ConclaveRegistrationConfig = registration_entry.conclave_config
    if not hasattr(registration_entry, 'housing'):
        return None
    housing: Housing = registration_entry.housing

    match(housing.room_type):
        case HousingRoomType.single:
            return {
                'display_name': 'Housing: Single Room',
                'amount': conclave_config.single_room_cost
            }
        case HousingRoomType.double:
            return {
                'display_name': 'Housing: Double Room',
                'amount': conclave_config.double_room_cost
            }

    return None


def get_tshirts_charge(registration_entry: RegistrationEntry) -> ChargeInfo | None:
    conclave_config: ConclaveRegistrationConfig = registration_entry.conclave_config
    if not hasattr(registration_entry, 'tshirts'):
        return None
    tshirts: TShirts = registration_entry.tshirts

    num_tshirts = sum(1 for item in [tshirts.tshirt1, tshirts.tshirt2] if item)
    if num_tshirts == 0:
        return None

    return {
        'display_name': f'T-Shirts: {num_tshirts}',
        'amount': num_tshirts * conclave_config.tshirt_price
    }


def get_donation_charge(registration_entry: RegistrationEntry) -> ChargeInfo | None:
    if not hasattr(registration_entry, 'tshirts'):
        return None

    donation = registration_entry.tshirts.donation
    if donation == 0:
        return None

    return {
        'display_name': 'Donation',
        'amount': donation
    }
