from __future__ import annotations

from django import template
from django.utils import timezone

from ..models import (
    BEGINNER_PROGRAMS, Clef, ConclaveRegistrationConfig, InstrumentChoices, Program,
    RegistrationPhase, TuitionOption
)

register = template.Library()


@register.simple_tag
def get_current_conclave() -> ConclaveRegistrationConfig | None:
    try:
        query = ConclaveRegistrationConfig.objects.filter(
            year=timezone.now().year,
            phase__in=[RegistrationPhase.open, RegistrationPhase.late]
        )
        if query.exists():
            return query.get()

        return None
    except Exception as e:
        import traceback
        traceback.print_exc()


def url_path_is_conclave_registration(url_path: str) -> bool:
    return (
        url_path.startswith('/conclave/register/')
        or url_path.startswith('/conclave') and url_path.endswith('register/')
    )


def url_path_is_conclave_admin(url_path: str) -> bool:
    return url_path.startswith('/conclave/admin')


def format_registration_phase(registration_phase: str) -> str:
    return RegistrationPhase(registration_phase).label


_PERIOD_STRS = {
    1: '1st',
    2: '2nd',
    3: '3rd',
    4: '4th',
}


def format_period_long(period: int) -> str:
    return f'{_PERIOD_STRS[period]} Period'


def format_instrument_size(instrument_size: str) -> str:
    return InstrumentChoices(instrument_size).label


def format_clef_list(clef: list[str]) -> str:
    return ', '.join((Clef(clef).label for clef in clef))


def format_tuition_option(tuition_option: str) -> str:
    return TuitionOption(tuition_option).label


def format_program(program: str) -> str:
    return Program(program).label


def is_beginner_program(program: str) -> bool:
    return program in BEGINNER_PROGRAMS


register.filter('format_registration_phase', format_registration_phase)
register.filter('format_period_long', format_period_long)
register.filter('format_instrument_size', format_instrument_size)
register.filter('format_clef_list', format_clef_list)
register.filter('format_tuition_option', format_tuition_option)
register.filter('format_program', format_program)
register.filter('url_path_is_conclave_registration', url_path_is_conclave_registration)
register.filter('url_path_is_conclave_admin', url_path_is_conclave_admin)
register.filter('is_beginner_program', is_beginner_program)
