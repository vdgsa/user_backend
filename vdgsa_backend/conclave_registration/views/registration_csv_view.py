from __future__ import annotations

import csv
import itertools
import json
from typing import Any, Dict, get_args

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View

from vdgsa_backend.conclave_registration.models import (
    AdditionalRegistrationInfo, ConclaveRegistrationConfig, Housing, Period, RegistrationEntry,
    WorkStudyApplication, YesNo
)
from vdgsa_backend.conclave_registration.summary_and_charges import (
    ChargeCSVLabel, get_charges_summary
)

from .permissions import is_conclave_team


class DownloadRegistrationEntriesCSVView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
        return make_reg_csv(
            get_object_or_404(ConclaveRegistrationConfig, pk=self.kwargs['conclave_config_pk'])
        )

    def test_func(self) -> bool:
        return is_conclave_team(self.request.user)


def make_reg_csv(conclave_config: ConclaveRegistrationConfig) -> HttpResponse:
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="conclave_{conclave_config.year}_registration.csv"')

    # IMPORTANT: Update CSV_HEADERS below if you
    # update the CSV dicts.
    writer = csv.DictWriter(response, fieldnames=CSV_HEADERS)
    writer.writeheader()

    entries = RegistrationEntry.objects.filter(
        conclave_config=conclave_config).order_by('payment_info__pk')
    for entry in entries:
        if not hasattr(entry, 'payment_info') or entry.payment_info.stripe_payment_method_id == '':
            continue

        writer.writerow({
            'sequence_id': entry.payment_info.id,

            'USER INFO': '',
            **user_info_to_dict(entry),

            'program': entry.program,
            'is_late': entry.is_late,
            'stripe_payment_method_id': entry.payment_info.stripe_payment_method_id,

            'INSTRUMENTS': '',
            **instruments_to_dict(entry),

            'CLASSES': '',
            **classes_to_dict(entry),

            'ADVANCED PROJECTS': '',
            **advanced_projects_to_dict(entry),

            'WORK-STUDY': '',
            **work_study_to_dict(entry),

            'HOUSING': '',
            **housing_to_dict(entry),

            'EXTRAS': '',
            **extras_to_dict(entry),

            'CHARGES': '',
            **charges_to_dict(entry),
            'charges': json.dumps(get_charges_summary(entry), indent=4),
        })

    return response


def user_info_to_dict(entry: RegistrationEntry) -> dict[str, object]:
    result: dict[str, object] = {
        'email': entry.user.username,
        'first_name': entry.user.first_name,
        'last_name': entry.user.last_name,
    }

    if not hasattr(entry, 'additional_info'):
        return result

    info: AdditionalRegistrationInfo = entry.additional_info

    result.update({
        'nickname': info.nickname,
        'address_line_1': entry.user.address_line_1,
        'address_line_2': entry.user.address_line_2,
        'address_city': entry.user.address_city,
        'address_state': entry.user.address_state,
        'address_postal_code': entry.user.address_postal_code,
        'address_country': entry.user.address_country,
        'conclave_phone': entry.additional_info.phone,
        'phone1': entry.user.phone1,
        'phone2': entry.user.phone2,

        'age': info.age,
        'gender': info.gender,
        'pronouns': info.pronouns,

        'include_in_whos_coming_to_conclave_list': info.include_in_whos_coming_to_conclave_list,
        'attended_conclave_before': info.attended_conclave_before,
        'buddy_willingness': info.buddy_willingness,
        'wants_display_space': info.wants_display_space,
        'num_display_space_days': (
            info.num_display_space_days if info.wants_display_space == YesNo.yes else 0
        ),
        'liability_release': info.liability_release,
        'covid_policy': info.covid_policy,
        'photo_release_auth': info.photo_release_auth,
        'other_info': info.other_info,
    })

    return result


def instruments_to_dict(entry: RegistrationEntry) -> Dict[str, Any]:
    instruments_str = ''
    for instr in entry.instruments_bringing.all():
        instruments_str += (
            str(instr) + f' | {instr.level} | {",".join(instr.clefs)} '
            f'| {instr.purpose} | {instr.comments}\n'
        )

    result = {
        'instruments_bringing': instruments_str,
    }
    if hasattr(entry, 'beginner_instruments'):
        result['beginner_needs_instrument'] = entry.beginner_instruments.needs_instrument
        result['beginner_instrument_bringing'] = entry.beginner_instruments.instrument_bringing

    return result


def classes_to_dict(entry: RegistrationEntry) -> dict[str, str]:
    if not hasattr(entry, 'regular_class_choices'):
        return {}

    class_prefs = entry.regular_class_choices
    result = {'comments': class_prefs.comments}

    # periodX_choiceY and periodX_choiceY_instrument fields
    for period in Period:
        for choice in range(1, 4):
            choice_attr = f'period{period}_choice{choice}'
            instr_attr = choice_attr + '_instrument'
            result[choice_attr] = getattr(class_prefs, choice_attr)
            result[instr_attr] = getattr(class_prefs, instr_attr)

    result.update({
        'flex_choice1': class_prefs.flex_choice1,
        'flex_choice1_instrument': class_prefs.flex_choice1_instrument,
        'flex_choice2': class_prefs.flex_choice2,
        'flex_choice2_instrument': class_prefs.flex_choice2_instrument,
        'flex_choice3': class_prefs.flex_choice3,
        'flex_choice3_instrument': class_prefs.flex_choice3_instrument,
    })

    return result


def advanced_projects_to_dict(entry: RegistrationEntry) -> Dict[str, str]:
    if not hasattr(entry, 'advanced_projects'):
        return {}

    return {
        'participation': entry.advanced_projects.participation,
        'project_proposal': entry.advanced_projects.project_proposal,
    }


def work_study_to_dict(entry: RegistrationEntry) -> Dict[str, str]:
    if not hasattr(entry, 'work_study'):
        return {}

    work_study: WorkStudyApplication = entry.work_study
    return {
        'applying_for_work_study': work_study.wants_work_study,
        'phone_number': work_study.phone_number,
        'can_receive_texts_at_phone_number': work_study.can_receive_texts_at_phone_number,
        'has_been_to_conclave': work_study.has_been_to_conclave,
        'has_done_work_study': work_study.has_done_work_study,
        'student_info': work_study.student_info,
        'can_arrive_before_first_meeting': work_study.can_arrive_before_first_meeting,
        'early_arrival': work_study.early_arrival,
        'can_stay_until_sunday_afternoon': work_study.can_stay_until_sunday_afternoon,
        'other_travel_info': work_study.other_travel_info,
        'job_preferences': ','.join(work_study.job_preferences),
        'other_jobs': work_study.other_jobs,
        'has_car': work_study.has_car,
        'relevant_job_experience': work_study.relevant_job_experience,
        'other_skills': work_study.other_skills,
        'other_info': work_study.other_info,
    }


def housing_to_dict(entry: RegistrationEntry) -> dict[str, object]:
    if not hasattr(entry, 'housing'):
        return {}

    housing: Housing = entry.housing

    return {
        'room_type': housing.room_type,
        'roommate_request': housing.roommate_request,
        'share_suite_request': housing.share_suite_request,
        'room_near_person_request': housing.room_near_person_request,
        'normal_bed_time': housing.normal_bed_time,
        'arrival_day': housing.arrival_day,
        'departure_day': housing.departure_day,
        'wants_housing_subsidy': housing.wants_housing_subsidy,
        'wants_canadian_currency_exchange_discount': (
            housing.wants_canadian_currency_exchange_discount
        ),
        'additional_housing_info': housing.additional_housing_info,
        'dietary_needs': ','.join(housing.dietary_needs),
        'other_dietary_needs': housing.other_dietary_needs,
        'banquet_food_choice': housing.banquet_food_choice,
        'is_bringing_guest_to_banquet': housing.is_bringing_guest_to_banquet,
        'banquet_guest_name': housing.banquet_guest_name,
        'banquet_guest_food_choice': housing.banquet_guest_food_choice,
    }


def extras_to_dict(entry: RegistrationEntry) -> dict[str, object]:
    if not hasattr(entry, 'tshirts'):
        return {}

    return {
        'tshirt1': entry.tshirts.tshirt1,
        'tshirt2': entry.tshirts.tshirt2,
        'donation': entry.tshirts.donation,
    }


def charges_to_dict(entry: RegistrationEntry) -> dict[str, float]:
    charges_summary = get_charges_summary(entry)
    return {
        **{charge['csv_label']: charge['amount'] for charge in charges_summary['charges']},
        'Work Study Scholarship': charges_summary['work_study_scholarship_amount'],
        'Housing Subsidy?': charges_summary['apply_housing_subsidy'],
        'Canadian Discount?': charges_summary['apply_canadian_discount'],
        'Subtotal': charges_summary['subtotal'],
        'Total': charges_summary['total'],
    }


# IMPORTANT: Update this list when you update the CSV dicts.
CSV_HEADERS = [
    'sequence_id',

    'USER INFO',
    'email',
    'first_name',
    'last_name',
    'nickname',
    'address_line_1',
    'address_line_2',
    'address_city',
    'address_state',
    'address_postal_code',
    'address_country',
    'conclave_phone',
    'phone1',
    'phone2',
    'age',
    'gender',
    'pronouns',
    'include_in_whos_coming_to_conclave_list',
    'attended_conclave_before',
    'buddy_willingness',
    'wants_display_space',
    'num_display_space_days',
    'liability_release',
    'covid_policy',
    'photo_release_auth',
    'other_info',

    'program',
    'is_late',
    'stripe_payment_method_id',

    'INSTRUMENTS',
    'instruments_bringing',
    'beginner_needs_instrument',
    'beginner_instrument_bringing',

    'CLASSES',
    'comments',
    *list(itertools.chain.from_iterable(
        (f'period{period}_choice{choice}', f'period{period}_choice{choice}_instrument')
        for choice in range(1, 4)
        for period in Period
    )),
    'flex_choice1',
    'flex_choice1_instrument',
    'flex_choice2',
    'flex_choice2_instrument',
    'flex_choice3',
    'flex_choice3_instrument',

    'ADVANCED PROJECTS',
    'participation',
    'project_proposal',

    'WORK-STUDY',
    'applying_for_work_study',
    'phone_number',
    'can_receive_texts_at_phone_number',
    'has_been_to_conclave',
    'has_done_work_study',
    'student_info',
    'can_arrive_before_first_meeting',
    'early_arrival',
    'can_stay_until_sunday_afternoon',
    'other_travel_info',
    'job_preferences',
    'other_jobs',
    'has_car',
    'relevant_job_experience',
    'other_skills',
    'other_info',

    'HOUSING',
    'room_type',
    'roommate_request',
    'share_suite_request',
    'room_near_person_request',
    'normal_bed_time',
    'arrival_day',
    'departure_day',
    'wants_housing_subsidy',
    'wants_canadian_currency_exchange_discount',
    'additional_housing_info',
    'dietary_needs',
    'other_dietary_needs',
    'banquet_food_choice',
    'is_bringing_guest_to_banquet',
    'banquet_guest_name',
    'banquet_guest_food_choice',

    'EXTRAS',
    'tshirt1',
    'tshirt2',
    'donation',

    'CHARGES',
    *get_args(ChargeCSVLabel),
    'Work Study Scholarship',
    'Housing Subsidy?',
    'Canadian Discount?',
    'Subtotal',
    'Total',
    'charges',
]

# -----------------------------------------------------------------------------


class DownloadFirstClassChoicesCSVView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
        return make_class_first_choices_csv(
            get_object_or_404(ConclaveRegistrationConfig, pk=self.kwargs['conclave_config_pk'])
        )

    def test_func(self) -> bool:
        return is_conclave_team(self.request.user)


def make_class_first_choices_csv(conclave_config: ConclaveRegistrationConfig) -> HttpResponse:
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="conclave_{conclave_config.year}_class_first_choices.csv"')

    classes = list(conclave_config.classes.all())
    first_choices_per_class = {str(class_): [] for class_ in classes}

    for entry in conclave_config.registration_entries.order_by('pk'):
        if not entry.is_finalized or not hasattr(entry, 'regular_class_choices'):
            continue

        choices = entry.regular_class_choices

        if choices.period1_choice1:
            first_choices_per_class[str(choices.period1_choice1)].append(entry.user)
        if choices.period2_choice1:
            first_choices_per_class[str(choices.period2_choice1)].append(entry.user)
        if choices.period3_choice1:
            first_choices_per_class[str(choices.period3_choice1)].append(entry.user)
        if choices.period4_choice1:
            first_choices_per_class[str(choices.period4_choice1)].append(entry.user)

        if choices.flex_choice1:
            first_choices_per_class[str(choices.flex_choice1)].append(entry.user)

    writer = csv.DictWriter(response, fieldnames=['Class', 'Who Picked as First Choice'])
    writer.writeheader()
    for class_name, first_choices in first_choices_per_class.items():
        writer.writerow({
            'Class': class_name,
            'Who Picked as First Choice': '\n'.join(
                map(lambda user: f'{user.first_name} {user.last_name} ({user.username})',
                    first_choices)
            )
        })

    return response
