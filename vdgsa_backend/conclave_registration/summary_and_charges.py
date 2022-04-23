"""
Contains business logic for summarizing registration choices and
charges. Provides top-level methods that return those summaries as
dictionaries that can be rendered with simple templates for display
on the "Summary" page and in confirmation emails.
"""

from __future__ import annotations

from datetime import datetime
from typing import Final, TypedDict

from vdgsa_backend.conclave_registration.models import (
    NOT_ATTENDING_BANQUET_SENTINEL, AdditionalRegistrationInfo, BeginnerInstrumentInfo,
    ClassChoiceDict, ConclaveRegistrationConfig, DietaryNeeds, Housing, HousingRoomType,
    InstrumentBringing, InstrumentChoices, Period, Program, RegistrationEntry,
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
        'tshirts': get_tshirt_summary(registration_entry),
        'vendors': get_vendor_summary(registration_entry),
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

    flexible_class_prefs: list[ClassChoiceDict] = [
        {'class': registration_entry.regular_class_choices.flex_choice1,
         'instrument': registration_entry.regular_class_choices.flex_choice1_instrument},
        {'class': registration_entry.regular_class_choices.flex_choice2,
         'instrument': registration_entry.regular_class_choices.flex_choice2_instrument},
        {'class': registration_entry.regular_class_choices.flex_choice3,
         'instrument': registration_entry.regular_class_choices.flex_choice3_instrument},
    ]
    per_period_prefs = _get_per_period_class_preferences(class_choices)
    freebie_prefs = per_period_prefs.pop(Period.fourth)
    result = {
        # Note: All three choices are required, so this filter should leave us with
        # three or zero choices in the list
        'flexible_class_preferences': [
            f"{choice_dict['class']} ({_instrument_to_str(choice_dict['instrument'])}) "
            f"({Period(choice_dict['class'].period).label})"
            for choice_dict in flexible_class_prefs if choice_dict['class'] is not None
        ],
        'per_period_class_preferences': per_period_prefs,
        'freebie_preferences': freebie_prefs,
    }

    selected_any_classes = (
        result['flexible_class_preferences']
        or any(result['per_period_class_preferences'].values())
        or result['freebie_preferences']
    )
    return result if selected_any_classes else None


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
            f"{choice_dict['class']} ({_instrument_to_str(choice_dict['instrument'])})"
            for choice_dict in choices if choice_dict['class'] is not None
        ]
        for period, choices in class_choices.by_period.items()
    }


def _instrument_to_str(instrument: InstrumentBringing | None) -> str:
    return 'Any' if instrument is None else str(instrument)


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

    if housing.banquet_food_choice == NOT_ATTENDING_BANQUET_SENTINEL:
        summary_items.append('Attending Banquet: No')
    else:
        summary_items += [
            'Attending Banquet: Yes',
            f'Banquet Food Choice: {housing.banquet_food_choice}',
        ]

        if housing.is_bringing_guest_to_banquet == YesNo.yes:
            summary_items += [
                f'Banquet Guest: {housing.banquet_guest_name}',
                f'Banquet Guest Food Choice: {housing.banquet_guest_food_choice}',
            ]

    return summary_items


def get_tshirt_summary(registration_entry: RegistrationEntry) -> list[str]:
    if not hasattr(registration_entry, 'tshirts'):
        return []

    return [tshirt for tshirt in registration_entry.tshirts.as_list() if tshirt]


def get_vendor_summary(registration_entry: RegistrationEntry) -> list[str]:
    if not hasattr(registration_entry, 'additional_info'):
        return []

    additional_info: AdditionalRegistrationInfo = registration_entry.additional_info
    if additional_info.wants_display_space != YesNo.yes:
        return []

    return [
        f"Table in vendors' emporium: {additional_info.num_display_space_days} days"
    ]


class ChargesSummary(TypedDict):
    charges: list[ChargeInfo]
    work_study_scholarship_amount: int
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

    tuition_charge = get_tuition_charge(registration_entry)
    if tuition_charge is not None:
        charges.append(tuition_charge)

    add_on_class_charge = get_add_on_class_charge(registration_entry)
    if add_on_class_charge is not None:
        charges.append(add_on_class_charge)

    charges += get_housing_charges(registration_entry)

    if (vendor_table_charge := get_vendor_table_charge(registration_entry)) is not None:
        charges.append(vendor_table_charge)

    if (tshirts_charge := get_tshirts_charge(registration_entry)) is not None:
        charges.append(tshirts_charge)

    if (donation_charge := get_donation_charge(registration_entry)) is not None:
        charges.append(donation_charge)

    if registration_entry.is_late:
        charges.append({
            'display_name': 'Late Registration Fee',
            'amount': conclave_config.late_registration_fee
        })

    work_study_scholarship_amount = 0
    if (hasattr(registration_entry, 'work_study')
            and registration_entry.work_study.wants_work_study == YesNo.yes
            and tuition_charge is not None):
        work_study_scholarship_amount = tuition_charge['amount']
        if add_on_class_charge is not None:
            work_study_scholarship_amount += add_on_class_charge['amount']

    apply_housing_subsidy = (
        hasattr(registration_entry, 'housing')
        and registration_entry.housing.wants_housing_subsidy
    )
    apply_canadian_discount = (
        hasattr(registration_entry, 'housing')
        and registration_entry.housing.wants_canadian_currency_exchange_discount
    )

    subtotal = sum(charge['amount'] for charge in charges) - work_study_scholarship_amount
    if apply_housing_subsidy:
        subtotal -= conclave_config.housing_subsidy_amount

    total = subtotal
    if apply_canadian_discount:
        total *= 1 - conclave_config.canadian_discount_percent / 100
        total = int(total)  # round down
    return {
        'charges': charges,
        'work_study_scholarship_amount': work_study_scholarship_amount,
        'apply_housing_subsidy': apply_housing_subsidy,
        'apply_canadian_discount': apply_canadian_discount,
        'subtotal': subtotal,
        'total': total,
    }


def get_tuition_charge(registration_entry: RegistrationEntry) -> ChargeInfo | None:
    conclave_config: ConclaveRegistrationConfig = registration_entry.conclave_config
    program = registration_entry.program
    if program in [Program.non_playing_attendee, Program.beginners]:
        display_name = 'Workshop Fee'
    else:
        display_name = f'Tuition: {Program(program).label}'

    match(program):
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
        case Program.seasoned_players | Program.advanced_projects:
            return {
                'display_name': display_name,
                'amount': conclave_config.seasoned_players_tuition
            }
        case Program.beginners:
            staying_off_campus = (
                hasattr(registration_entry, 'housing')
                and registration_entry.housing.room_type == HousingRoomType.off_campus
            )
            return {
                'display_name': display_name,
                'amount': 0 if staying_off_campus else conclave_config.workshop_fee
            }
        case Program.faculty_guest_other:
            return None
        case Program.non_playing_attendee:
            return {
                'display_name': display_name,
                'amount': conclave_config.workshop_fee
            }
        case _:
            assert False


def get_add_on_class_charge(registration_entry: RegistrationEntry) -> ChargeInfo | None:
    conclave_config: ConclaveRegistrationConfig = registration_entry.conclave_config
    if not hasattr(registration_entry, 'regular_class_choices'):
        return None
    class_choices: RegularProgramClassChoices = registration_entry.regular_class_choices

    match(registration_entry.program):
        case Program.beginners if class_choices.num_non_freebie_classes == 1:
            return {
                'display_name': '1 Add-On Class',
                'amount': conclave_config.beginners_extra_class_fee
            }
        case Program.beginners if class_choices.num_non_freebie_classes == 2:
            return {
                'display_name': '2 Add-On Classes',
                'amount': conclave_config.beginners_two_extra_classes_fee
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
        case Program.seasoned_players | Program.advanced_projects \
                if class_choices.num_non_freebie_classes == 1:
            return {
                'display_name': '1 Add-On Class',
                'amount': conclave_config.seasoned_players_extra_class_fee
            }

    return None


def get_housing_charges(registration_entry: RegistrationEntry) -> list[ChargeInfo]:
    conclave_config: ConclaveRegistrationConfig = registration_entry.conclave_config
    if not hasattr(registration_entry, 'housing'):
        return []
    housing: Housing = registration_entry.housing

    charges: list[ChargeInfo] = []

    if registration_entry.program != Program.faculty_guest_other:
        match(housing.room_type):
            case HousingRoomType.single:
                charges += _room_and_board_charge(
                    housing,
                    conclave_config,
                    formatted_room_type='Single Room',
                    early_arrival_room_rate=(
                        conclave_config.single_room_early_arrival_per_night_cost),
                    per_night_room_rate=conclave_config.single_room_per_night_cost,
                    full_week_room_rate=conclave_config.single_room_full_week_cost,
                )
            case HousingRoomType.double:
                charges += _room_and_board_charge(
                    housing,
                    conclave_config,
                    formatted_room_type='Double Room',
                    early_arrival_room_rate=(
                        conclave_config.double_room_early_arrival_per_night_cost),
                    per_night_room_rate=conclave_config.double_room_per_night_cost,
                    full_week_room_rate=conclave_config.double_room_full_week_cost,
                )

    if housing.is_bringing_guest_to_banquet == YesNo.yes:
        charges.append({
            'display_name': 'Banquet Guest Fee',
            'amount': conclave_config.banquet_guest_fee
        })

    return charges


def _room_and_board_charge(
    housing: Housing,
    conclave_config: ConclaveRegistrationConfig,
    *,
    formatted_room_type: str,
    early_arrival_room_rate: int,
    per_night_room_rate: int,
    full_week_room_rate: int
) -> list[ChargeInfo]:
    arrival_date = datetime.strptime(
        housing.arrival_day, conclave_config.arrival_date_format
    ).date().replace(year=conclave_config.year)
    departure_date = datetime.strptime(
        housing.departure_day, conclave_config.arrival_date_format
    ).date().replace(year=conclave_config.year)

    num_nights = (departure_date - arrival_date).days
    num_early_arrival_nights = (
        (conclave_config.arrival_dates[0] - arrival_date).days
        if arrival_date in conclave_config.early_arrival_dates
        else 0
    )
    num_nights -= num_early_arrival_nights
    full_week_num_nights: Final = 7

    charges: list[ChargeInfo] = []
    if num_early_arrival_nights != 0:
        charges.append({
            'display_name': (
                f'Early Arrival: {formatted_room_type}, {num_early_arrival_nights} night(s)'
            ),
            'amount': early_arrival_room_rate * num_early_arrival_nights
        })

    if num_nights == full_week_num_nights:
        charges.append({
            'display_name': f'Full Week Room and Board: {formatted_room_type}',
            'amount': full_week_room_rate
        })
    else:
        charges.append({
            'display_name': f'{formatted_room_type}, {num_nights} night(s)',
            'amount': per_night_room_rate * num_nights
        })

    return charges


def get_vendor_table_charge(registration_entry: RegistrationEntry) -> ChargeInfo | None:
    if not hasattr(registration_entry, 'additional_info'):
        return None

    additional_info: AdditionalRegistrationInfo = registration_entry.additional_info
    conclave_config: ConclaveRegistrationConfig = registration_entry.conclave_config

    if additional_info.wants_display_space == YesNo.yes:
        num_days = additional_info.num_display_space_days
        return {
            'display_name': f"Table in vendor's emporium, {num_days} days",
            'amount': num_days * conclave_config.vendor_table_cost_per_day,
        }


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
