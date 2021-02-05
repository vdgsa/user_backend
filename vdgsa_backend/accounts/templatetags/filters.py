from typing import Any, Optional

import pytz
from django import template
from django.forms import BoundField
from django.http.request import HttpRequest
from django.urls.base import reverse
from django.utils import timezone
from django.utils.safestring import SafeText

from vdgsa_backend.accounts.models import User

register = template.Library()


def introspect(obj: object) -> object:
    """
    Used for debugging. Prints the type and attributes of "obj".
    """
    print(type(obj))
    print(dir(obj))
    return obj


def show_name(user: User) -> str:
    if user.first_name:
        return f'{user.first_name} {user.last_name}'

    return user.username


def show_name_and_email(user: User) -> str:
    if user.first_name:
        return f'{user.first_name} {user.last_name} ({user.username})'

    return user.username


def add_classes(field: BoundField, classes: str) -> SafeText:
    """
    Adds "classes" (a space-separated string of classes) to "field".
    Example usage: {{form.some_field | add_classes:"form-control"}}
    """
    return field.as_widget(attrs={'class': field.css_classes(classes)})  # type: ignore


def current_page_is_my_account_page(request: HttpRequest) -> bool:
    return request.path == reverse('user-profile', kwargs={'pk': request.user.pk})


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
register.filter('introspect', introspect)
register.filter('add_classes', add_classes)
register.filter('current_page_is_my_account_page', current_page_is_my_account_page)
