from __future__ import annotations

from typing import List

from django import template
from django.utils import timezone

from ..models import (
    BEGINNER_PROGRAMS, Clef, ConclaveRegistrationConfig, DietaryNeeds, HousingRoomType,
    InstrumentChoices, InstrumentPurpose, Program, RegistrationPhase, RelativeInstrumentLevel
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
        raise


def url_path_is_conclave_registration(url_path: str) -> bool:
    return (
        url_path.startswith('/conclave/register/')
        or url_path.startswith('/conclave') and url_path.endswith('register/')
    )


def url_path_is_conclave_admin(url_path: str) -> bool:
    return url_path.startswith('/conclave/admin')


def format_registration_phase(registration_phase: str) -> str:
    return RegistrationPhase(registration_phase).label


PERIOD_STRS = {
    1: '1st',
    2: '2nd',
    3: '3rd',
    4: '4th',
}


def format_period_long(period: int) -> str:
    return f'{PERIOD_STRS[period]} Period'


def format_relative_level(relative_level: str) -> str:
    return RelativeInstrumentLevel(relative_level).label


def format_instrument_size(instrument_size: str) -> str:
    return InstrumentChoices(instrument_size).label


def format_instrument_purpose(purpose: str) -> str:
    return InstrumentPurpose(purpose).label


def format_clef_list(clef: list[str]) -> str:
    return ', '.join((Clef(clef).label for clef in clef))


def format_program(program: str) -> str:
    return Program(program).label


def format_room_type(room_type: str) -> str:
    return HousingRoomType(room_type).label


def format_dietary_needs(dietary_needs: List[str]) -> str:
    return ', '.join((
        DietaryNeeds(need).label for need in dietary_needs
    ))


def is_beginner_program(program: str) -> bool:
    return program in BEGINNER_PROGRAMS


register.filter('format_registration_phase', format_registration_phase)
register.filter('format_period_long', format_period_long)
register.filter('format_relative_level', format_relative_level)
register.filter('format_instrument_size', format_instrument_size)
register.filter('format_instrument_purpose', format_instrument_purpose)
register.filter('format_clef_list', format_clef_list)
register.filter('format_program', format_program)
register.filter('format_room_type', format_room_type)
register.filter('format_dietary_needs', format_dietary_needs)
register.filter('url_path_is_conclave_registration', url_path_is_conclave_registration)
register.filter('url_path_is_conclave_admin', url_path_is_conclave_admin)
register.filter('is_beginner_program', is_beginner_program)
