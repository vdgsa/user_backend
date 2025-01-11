from typing import Any, Optional, Union

import pytz
from django import template
from django.forms import BoundField
from django.forms.boundfield import BoundWidget
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
    print(obj)
    return obj


def show_name(user: User) -> str:
    if user.first_name:
        return f'{user.first_name} {user.last_name}'

    return user.username


def show_name_and_email(user: User) -> str:
    if user.first_name:
        return f'{user.first_name} {user.last_name} ({user.username})'

    return user.username


def teacher_affiliation(user: User) -> str:
    affiliations = []
    if user.is_teacher:
        affiliations.append("Lessons in Person")

    if user.is_remote_teacher: 
        affiliations.append("Remote Lessons")

    return affiliations

def commercial_affiliation(user: User) -> str:
    affiliations = []
    if user.is_instrument_maker:
        affiliations.append("Instrument Maker")

    if user.is_bow_maker:
        affiliations.append("Bow Maker")

    if user.is_repairer:
        affiliations.append("Repairer")

    if user.is_publisher:
        affiliations.append("Publisher")

    if len(user.other_commercial) > 0:
        affiliations.append(user.other_commercial)

    return affiliations

def all_affiliation(user: User) -> str:
    return commercial_affiliation(user) + teacher_affiliation(user) 

def add_classes(field: Union[BoundField, BoundWidget], classes: str) -> SafeText:
    """
    Adds "classes" (a space-separated string of classes) to "field".
    Example usage: {{form.some_field | add_classes:"form-control"}}
    """
    if isinstance(field, BoundField):
        return field.as_widget(attrs={'class': field.css_classes(classes)})

    class_str = field.data['attrs'].get('class', '')
    class_str += classes
    field.data['attrs']['class'] = class_str
    return field.tag()


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
register.filter('teacher_affiliation', teacher_affiliation)
register.filter('commercial_affiliation', commercial_affiliation)
register.filter('all_affiliation', all_affiliation)

