from vdgsa_backend.rental_viols.models import (
    Bow, Case, RentalEvent, RentalState, RentalHistory, Viol, WaitingList
)
from django import template

from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()


@register.inclusion_tag("history_table.html")
def history_table(history):
    return {
        "history": history.all().order_by('-created_at'),

    }


@register.inclusion_tag("instrument_detail.html")
def instrument_detail(rentalItemInstrument):
    return {
        "item": rentalItemInstrument,

    }


def currency(dollars):
    dollars = round(float(dollars), 2)
    return "$%s%s" % (intcomma(int(dollars)), ("%0.2f" % dollars)[-3:])


register.filter('currency', currency)
