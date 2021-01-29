from typing import Any, Optional

import pytz
from django import template
from django.utils import timezone

from vdgsa_backend.accounts.models import User

register = template.Library()


def show_name(user: User) -> str:
    if user.first_name:
        return f'{user.first_name} {user.last_name}'

    return user.username


def show_name_and_email(user: User) -> str:
    if user.first_name:
        return f'{user.first_name} {user.last_name} ({user.username})'

    return user.username


@register.simple_tag
def format_datetime(*args: Any, **kwargs: Any) -> str:
    return format_datetime_impl(*args, **kwargs)


def format_datetime_impl(
    datetime_: Optional[timezone.datetime],
    timezone_str: str = 'America/New_York',
    *,
    none_ok: bool = False
) -> str:
    if datetime_ is None:
        if none_ok:
            return ''
        else:
            raise ValueError(
                'datetime_ argument was None. '
                'Pass none_ok=True if you want to allow None values for datetime_.'
            )

    return timezone.localtime(
        datetime_, pytz.timezone(timezone_str)
    ).strftime('%b %d, %Y, %I:%M %p %Z')


@register.simple_tag
def format_date(*args: Any, **kwargs: Any) -> str:
    return format_date_impl(*args, **kwargs)


def format_date_impl(
    datetime_: Optional[timezone.datetime],
    timezone_str: str = 'America/New_York',
    *,
    none_ok: bool = False
) -> str:
    if datetime_ is None:
        if none_ok:
            return ''
        else:
            raise ValueError(
                'datetime_ argument was None. '
                'Pass none_ok=True if you want to allow None values for datetime_.'
            )

    return timezone.localtime(
        datetime_, pytz.timezone(timezone_str)
    ).strftime('%b %d, %Y')


register.filter('show_name', show_name)
register.filter('show_name_and_email', show_name_and_email)
