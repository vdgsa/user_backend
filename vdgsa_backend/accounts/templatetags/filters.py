import pytz
from django import template
from django.utils import timezone

from vdgsa_backend.accounts.models import User

register = template.Library()


def show_name(user: User) -> str:
    if user.first_name:
        return f'{user.first_name} {user.last_name}'

    return user.username


def format_datetime(datetime_: timezone.datetime, timezone_str: str = 'America/New_York') -> str:
    return timezone.localtime(
        datetime_, pytz.timezone(timezone_str)
    ).strftime('%b %d, %Y, %I:%M %p %Z')


def format_date(datetime_: timezone.datetime, timezone_str: str = 'America/New_York') -> str:
    return timezone.localtime(
        datetime_, pytz.timezone(timezone_str)
    ).strftime('%b %d, %Y')


register.filter('show_name', show_name)
register.filter('format_datetime', format_datetime)
register.filter('format_date', format_date)
