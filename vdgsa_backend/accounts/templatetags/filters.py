from django import template
from django.forms import BoundField
from django.forms.widgets import CheckboxInput

from vdgsa_backend.accounts.models import User

register = template.Library()


def show_name(user: User) -> str:
    if user.first_name:
        return f'{user.first_name} {user.last_name}'

    return user.username


register.filter('show_name', show_name)
