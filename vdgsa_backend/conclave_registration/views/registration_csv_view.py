from __future__ import annotations

import csv
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View

from vdgsa_backend.conclave_registration.models import (
    ADVANCED_PROGRAMS, BEGINNER_PROGRAMS, NO_CLASS_PROGRAMS, BasicRegistrationInfo,
    BeginnerInstrumentInfo, Class, Clef, ConclaveRegistrationConfig, InstrumentBringing,
    PaymentInfo, Period, Program, RegistrationEntry, RegistrationPhase, RegularProgramClassChoices,
    TShirts, WorkStudyApplication, WorkStudyJob, YesNo, YesNoMaybe, get_classes_by_period
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
    headers = [
        'email',
        'first_name',
        'last_name',
        'address_line_1',
        'address_line_2',
        'address_city',
        'address_state',
        'address_postal_code',
        'address_country',
        'phone1',
        'phone2',
        'program',
        'is_late',
        'tuition_charge',
        'late_fee',
        'tshirts_charge',
        'total_charges',
        'total_minus_work_study',
        'stripe_payment_method_id',
        'INSTRUMENTS',
        'beginner_needs_instrument',
        'beginner_instrument_bringing',
        'instruments_bringing',
        'CLASSES',
        'comments',
        'period1_choice1',
        'period1_choice1_instrument',
        'period1_choice2',
        'period1_choice2_instrument',
        'period1_choice3',
        'period1_choice3_instrument',
        'period2_choice1',
        'period2_choice1_instrument',
        'period2_choice2',
        'period2_choice2_instrument',
        'period2_choice3',
        'period2_choice3_instrument',
        'period3_choice1',
        'period3_choice1_instrument',
        'period3_choice2',
        'period3_choice2_instrument',
        'period3_choice3',
        'period3_choice3_instrument',
        'period4_choice1',
        'period4_choice1_instrument',
        'period4_choice2',
        'period4_choice2_instrument',
        'period4_choice3',
        'period4_choice3_instrument',
        'ADDITIONAL INFO',
        'attended_nonclave',
        'buddy_willingness',
        'wants_display_space',
        'archival_video_release',
        'photo_release_auth',
        'other_info',
        'WORK-STUDY',
        'nickname_and_pronouns',
        'phone_number',
        'can_receive_texts_at_phone_number',
        'home_timezone',
        'other_timezone',
        'has_been_to_conclave',
        'has_done_work_study',
        'student_info',
        'job_preferences',
        'relevant_job_experience',
        'other_skills',
        'other_info',
        'EXTRAS',
        'tshirt1',
        'tshirt2',
        'donation',
    ]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="conclave_{conclave_config.year}_registration.csv"')

    writer = csv.DictWriter(response, fieldnames=headers)
    writer.writeheader()

    entries = RegistrationEntry.objects.filter(
        conclave_config=conclave_config).order_by('payment_info__pk')
    for entry in entries:
        if not hasattr(entry, 'payment_info') or entry.payment_info.stripe_payment_method_id == '':
            continue

        writer.writerow({
            'email': entry.user.username,
            'first_name': entry.user.first_name,
            'last_name': entry.user.last_name,
            'address_line_1': entry.user.address_line_1,
            'address_line_2': entry.user.address_line_2,
            'address_city': entry.user.address_city,
            'address_state': entry.user.address_state,
            'address_postal_code': entry.user.address_postal_code,
            'address_country': entry.user.address_country,
            'phone1': entry.user.phone1,
            'phone2': entry.user.phone2,

            'program': entry.program,
            'is_late': entry.is_late,
            'tuition_charge': entry.tuition_charge,
            'late_fee': entry.late_fee,
            'tshirts_charge': entry.tshirts_charge,
            'total_charges': entry.total_charges,
            'total_minus_work_study': entry.total_minus_work_study,

            'stripe_payment_method_id': entry.payment_info.stripe_payment_method_id,

            'INSTRUMENTS': '',
            **instruments_to_dict(entry),

            'CLASSES': '',
            'comments': entry.regular_class_choices.comments if hasattr(entry, 'regular_class_choices') else '',
            'period1_choice1': entry.regular_class_choices.period1_choice1 if hasattr(entry, 'regular_class_choices') else '',
            'period1_choice1_instrument': entry.regular_class_choices.period1_choice1_instrument if hasattr(entry, 'regular_class_choices') else '',
            'period1_choice2': entry.regular_class_choices.period1_choice2 if hasattr(entry, 'regular_class_choices') else '',
            'period1_choice2_instrument': entry.regular_class_choices.period1_choice2_instrument if hasattr(entry, 'regular_class_choices') else '',
            'period1_choice3': entry.regular_class_choices.period1_choice3 if hasattr(entry, 'regular_class_choices') else '',
            'period1_choice3_instrument': entry.regular_class_choices.period1_choice3_instrument if hasattr(entry, 'regular_class_choices') else '',
            'period2_choice1': entry.regular_class_choices.period2_choice1 if hasattr(entry, 'regular_class_choices') else '',
            'period2_choice1_instrument': entry.regular_class_choices.period2_choice1_instrument if hasattr(entry, 'regular_class_choices') else '',
            'period2_choice2': entry.regular_class_choices.period2_choice2 if hasattr(entry, 'regular_class_choices') else '',
            'period2_choice2_instrument': entry.regular_class_choices.period2_choice2_instrument if hasattr(entry, 'regular_class_choices') else '',
            'period2_choice3': entry.regular_class_choices.period2_choice3 if hasattr(entry, 'regular_class_choices') else '',
            'period2_choice3_instrument': entry.regular_class_choices.period2_choice3_instrument if hasattr(entry, 'regular_class_choices') else '',
            'period3_choice1': entry.regular_class_choices.period3_choice1 if hasattr(entry, 'regular_class_choices') else '',
            'period3_choice1_instrument': entry.regular_class_choices.period3_choice1_instrument if hasattr(entry, 'regular_class_choices') else '',
            'period3_choice2': entry.regular_class_choices.period3_choice2 if hasattr(entry, 'regular_class_choices') else '',
            'period3_choice2_instrument': entry.regular_class_choices.period3_choice2_instrument if hasattr(entry, 'regular_class_choices') else '',
            'period3_choice3': entry.regular_class_choices.period3_choice3 if hasattr(entry, 'regular_class_choices') else '',
            'period3_choice3_instrument': entry.regular_class_choices.period3_choice3_instrument if hasattr(entry, 'regular_class_choices') else '',
            'period4_choice1': entry.regular_class_choices.period4_choice1 if hasattr(entry, 'regular_class_choices') else '',
            'period4_choice1_instrument': entry.regular_class_choices.period4_choice1_instrument if hasattr(entry, 'regular_class_choices') else '',
            'period4_choice2': entry.regular_class_choices.period4_choice2 if hasattr(entry, 'regular_class_choices') else '',
            'period4_choice2_instrument': entry.regular_class_choices.period4_choice2_instrument if hasattr(entry, 'regular_class_choices') else '',
            'period4_choice3': entry.regular_class_choices.period4_choice3 if hasattr(entry, 'regular_class_choices') else '',
            'period4_choice3_instrument': entry.regular_class_choices.period4_choice3_instrument if hasattr(entry, 'regular_class_choices') else '',

            'ADDITIONAL INFO': '',
            'attended_nonclave': entry.basic_info.attended_nonclave,
            'buddy_willingness': entry.basic_info.buddy_willingness,
            'wants_display_space': entry.basic_info.wants_display_space,
            'archival_video_release': entry.basic_info.archival_video_release,
            'photo_release_auth': entry.basic_info.photo_release_auth,
            'other_info': entry.basic_info.other_info,

            'WORK-STUDY': '',
            'nickname_and_pronouns': entry.work_study.nickname_and_pronouns if hasattr(entry, 'work_study') else '',
            'phone_number': entry.work_study.phone_number if hasattr(entry, 'work_study') else '',
            'can_receive_texts_at_phone_number': entry.work_study.can_receive_texts_at_phone_number if hasattr(entry, 'work_study') else '',
            'home_timezone': entry.work_study.home_timezone if hasattr(entry, 'work_study') else '',
            'other_timezone': entry.work_study.other_timezone if hasattr(entry, 'work_study') else '',
            'has_been_to_conclave': entry.work_study.has_been_to_conclave if hasattr(entry, 'work_study') else '',
            'has_done_work_study': entry.work_study.has_done_work_study if hasattr(entry, 'work_study') else '',
            'student_info': entry.work_study.student_info if hasattr(entry, 'work_study') else '',
            'job_preferences': entry.work_study.job_preferences if hasattr(entry, 'work_study') else '',
            'relevant_job_experience': entry.work_study.relevant_job_experience if hasattr(entry, 'work_study') else '',
            'other_skills': entry.work_study.other_skills if hasattr(entry, 'work_study') else '',
            'other_info': entry.work_study.other_info if hasattr(entry, 'work_study') else '',

            'EXTRAS': '',
            'tshirt1': entry.tshirts.tshirt1 if hasattr(entry, 'tshirts') else '',
            'tshirt2': entry.tshirts.tshirt2 if hasattr(entry, 'tshirts') else '',
            'donation': entry.tshirts.donation if hasattr(entry, 'tshirts') else '',
        })

    return response


def instruments_to_dict(entry: RegistrationEntry):
    instruments_str = ''
    for instr in entry.instruments_bringing.all():
        instruments_str += str(instr) + f' | {instr.level} | {",".join(instr.clefs)}'

    return {
        'beginner_needs_instrument': (entry.beginner_instruments.needs_instrument
                                      if entry.program in BEGINNER_PROGRAMS else ''),
        'beginner_instrument_bringing': (entry.beginner_instruments.instrument_bringing
                                         if entry.program in BEGINNER_PROGRAMS else ''),

        'instruments_bringing': instruments_str,
    }
