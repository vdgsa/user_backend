from __future__ import annotations

from django import template

from ..models import Clef, InstrumentChoices, RegistrationPhase, TuitionOption

register = template.Library()


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


def format_level_list(levels: list[str]) -> str:
    return '/'.join(levels)


def format_instrument_size(instrument_size: str) -> str:
    return InstrumentChoices(instrument_size).label


def format_clef_list(clef: list[str]) -> str:
    return ', '.join((Clef(clef).label for clef in clef))


def format_tuition_option(tuition_option: str) -> str:
    return TuitionOption(tuition_option).label


register.filter('format_registration_phase', format_registration_phase)
register.filter('format_period_long', format_period_long)
register.filter('format_level_list', format_level_list)
register.filter('format_instrument_size', format_instrument_size)
register.filter('format_clef_list', format_clef_list)
register.filter('format_tuition_option', format_tuition_option)
