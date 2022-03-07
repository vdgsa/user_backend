"""
Contains business logic for summarizing registration choices and
charges. Provides top-level methods that return those summaries as
dictionaries that can be rendered with simple templates for display
on the "Summary" page and in confirmation emails.
"""

from __future__ import annotations

from typing import TypedDict

from vdgsa_backend.conclave_registration.models import (
    BeginnerInstrumentInfo, ConclaveRegistrationConfig, DietaryNeeds, Housing, HousingRoomType,
    InstrumentChoices, Period, Program, RegistrationEntry,
    RegularProgramClassChoices, TShirts, YesNo
)


# Registration summary data that can be easily rendered in a template.
class RegistrationSummary(TypedDict):
    program: Program
    applying_for_work_study: bool
    instruments: list[str]  # Instrument names to display verbatim
    classes: ClassSummary | None
    housing: list[str]  # Housing info summary lines to display verbatim
    tshirts: list[str]  # T-shirt sizes


class ClassSummary(TypedDict):
    wants_beginners_plus_class: bool
    flexible_class_preferences: list[str]
    per_period_class_preferences: dict[Period, list[str]]
    freebie_preferences: list[str]


def get_registration_summary(registration_entry: RegistrationEntry) -> RegistrationSummary:
    return {
        'program': registration_entry.program,
        'applying_for_work_study': registration_entry.is_applying_for_work_study,
        'instruments': get_instruments_summary(registration_entry),
        'classes': get_class_summary(registration_entry),
        'housing': get_housing_summary(registration_entry),
        'tshirts': get_tshirt_summary(registration_entry)
    }


def get_instruments_summary(registration_entry: RegistrationEntry) -> list[str]:
    match(registration_entry.program):
        case(Program.beginners) if hasattr(registration_entry, 'beginner_instruments'):
            beginner_instruments: BeginnerInstrumentInfo = registration_entry.beginner_instruments
            if beginner_instruments.needs_instrument == YesNo.yes:
                return ['I need to borrow an instrument']
            else:
                return [InstrumentChoices(beginner_instruments.instrument_bringing).label]
        case _:
            return [
                str(instrument)
                for instrument in registration_entry.instruments_bringing.all()
            ]


def get_class_summary(registration_entry: RegistrationEntry) -> ClassSummary | None:
    if not hasattr(registration_entry, 'regular_class_choices'):
        return None

    class_choices: RegularProgramClassChoices = registration_entry.regular_class_choices

    flexible_class_prefs = [
        registration_entry.regular_class_choices.flex_choice1,
        registration_entry.regular_class_choices.flex_choice2,
        registration_entry.regular_class_choices.flex_choice3
    ]
    # Note: All three choices are required, so this filter should leave us with
    # three on zero choices in the list
    flexible_class_prefs = [str(choice) for choice in flexible_class_prefs if choice is not None]
    per_period_prefs = _get_per_period_class_preferences(class_choices)
    freebie_prefs = per_period_prefs.pop(Period.fourth)
    result = {
        'wants_beginners_plus_class': class_choices.wants_extra_beginner_class == YesNo.yes,
        'flexible_class_preferences': flexible_class_prefs,
        'per_period_class_preferences': per_period_prefs,
        'freebie_preferences': freebie_prefs,
    }
    return result if any(result.values()) else None


def _get_per_period_class_preferences(
    class_choices: RegularProgramClassChoices
) -> dict[Period, list[str]]:
    # Map Period to list of class names, filtering out None ("no class" selections).
    # For non-freebie periods, users are required to select either 3 or zero
    # choices for a period, so we won't disturb the ordering.
    # For the freebie period, users can choose up to 3 choices in any
    # order, so the first non-None choice will be labelled as their first choice.
    return {
        period: [
            # Display class as "{Name} ({Preferred Instrument})"
            f"{choice_dict['class']} ({instr if (instr := choice_dict['instrument']) else 'Any'})"
            for choice_dict in choices if choice_dict['class'] is not None
        ]
        for period, choices in class_choices.by_period.items()
    }


def get_housing_summary(registration_entry: RegistrationEntry) -> list[str]:
    if not hasattr(registration_entry, 'housing'):
        return

    housing: Housing = registration_entry.housing
    summary_items = [f'Room type: {HousingRoomType(housing.room_type).label}']

    if housing.room_type == HousingRoomType.double:
        roommate_pref = req if (req := housing.roommate_request) else 'No preference'
        summary_items.append(f'Requested roommate: {roommate_pref}')

    if housing.room_type != HousingRoomType.off_campus:
        suitemate_pref = req if (req := housing.share_suite_request) else 'No preference'
        summary_items.append(f'Requesting a suite with: {suitemate_pref}')

        room_near_pref = req if (req := housing.room_near_person_request) else 'No preference'
        summary_items.append(f'Requesting a room near: {room_near_pref}')


    summary_items += [
        f'Arrival date: {housing.arrival_day}',
        f'Departure date: {housing.departure_day}',
    ]

    if housing.dietary_needs:
        summary_items.append(
            'Dietary needs: '
            + ', '.join(DietaryNeeds(val).label for val in housing.dietary_needs)
        )
    if housing.other_dietary_needs:
        summary_items.append('Additional dietary needs: ' + housing.other_dietary_needs)

    return summary_items


def get_tshirt_summary(registration_entry: RegistrationEntry) -> list[str]:
    if not hasattr(registration_entry, 'tshirts'):
        return []

    return [tshirt for tshirt in registration_entry.tshirts.as_list() if tshirt]


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
