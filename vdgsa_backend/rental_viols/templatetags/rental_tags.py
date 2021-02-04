from vdgsa_backend.rental_viols.models import (
    Bow, Case, RentalEvent, RentalHistory, Viol, WaitingList
)
from django import template

register = template.Library()


@register.inclusion_tag("history_table.html")
def history_table(history):
    return {
        "history": history,

    }


@register.inclusion_tag("instrument_detail.html")
def instrument_detail(rentalItemInstrument):
    return {
        "item": rentalItemInstrument,

    }
