from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

from vdgsa_backend.rental_viols.models import (
    Bow, Case, RentalEvent, RentalHistory, RentalState, Viol, WaitingList
)

register = template.Library()


@register.filter
def to_class_name(value):
    return value.__class__.__name__


@register.inclusion_tag("history_table.html")
def history_table(history):
    return {
        "history": history.all().order_by('-created_at'),

    }


@register.inclusion_tag("instrument_detail.html")
def instrument_detail(rentalItemInstrument, request, perms):
    return {
        "item": rentalItemInstrument,
        "request": request,
        "perms": perms,

    }


def currency(dollars):
    dollars = round(float(dollars), 2)
    return "$%s%s" % (intcomma(int(dollars)), ("%0.2f" % dollars)[-3:])


def dollars(dollars):
    dollars = round(float(dollars), 2)
    return "$%s" % intcomma(int(dollars))


register.filter('currency', currency)
register.filter('dollars', dollars)
