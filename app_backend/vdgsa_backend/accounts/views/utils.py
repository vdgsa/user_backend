from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict
import pycountry
from django.forms.forms import BaseForm
from django.http.response import JsonResponse
from django.template.loader import render_to_string


class AjaxFormResponse(JsonResponse):
    def __init__(self, data: AjaxFormResponseData, *args: Any, **kwargs: Any) -> None:
        super().__init__(data, *args, **kwargs)


AjaxFormResponseStatus = Literal['success', 'form_validation_error', 'other_error']


class AjaxFormResponseData(TypedDict):
    status: AjaxFormResponseStatus
    rendered_form: Optional[str]
    extra_data: Dict[str, object]


def get_ajax_form_response(
    status: AjaxFormResponseStatus,
    form: Optional[BaseForm],
    *,
    form_context: Optional[Dict[str, object]] = None,
    form_template: str = 'utils/form_body.tmpl',
    extra_data: Dict[str, object] = {},
) -> AjaxFormResponse:
    context: dict[str, object] = {'form': form}
    if form_context is not None:
        context.update(form_context)

    return AjaxFormResponse(
        {
            'status': status,
            'rendered_form': render_to_string(form_template, context),
            'extra_data': extra_data,
        },
        status=200,
    )


class LocationAddress():

    COUNTRY_SUBDIVISION_WHITELIST = ['United States', 'Canada', 'Mexico', 'Japan',
                                     'Brazil', 'Australia', 'New Zealand', 'China', 'Italy', 'Malaysia', 'South Korea', 'Venezuela']

    # US: US (Alpha-2), USA (Alpha-3)
    # Canada: CA, CAN
    # Mexico: MX, MEX
    # Japan: JP, JPN
    # Brazil: BR, BRA
    # Australia: AU, AUS
    # New Zealand: NZ, NZL
    # China: CN, CHN
    # Italy: IT, ITA
    # Malaysia: MY, MYS
    # South Korea: KR, KOR
    # Venezuela: VE, VEN

    def get_countries(filter_to_users: bool = False) -> List[Dict[str, object]]:
        if filter_to_users:
            try:
                # import here to avoid circular imports at module import time
                from vdgsa_backend.accounts.models import User
                codes_qs = (
                    User.objects
                    .order_by("address_country")
                    .values_list("address_country", flat=True)
                    .exclude(address_country__isnull=True)
                    .exclude(address_country="")
                    .distinct("address_country")
                )
                countries_list = [c.strip() for c in list(codes_qs) if c and c.strip()]
            except Exception:
                countries_list = []

            matched = []
            for countryName in countries_list:
                country = None
                # Try name match first
                country = pycountry.countries.get(name=countryName)
                if not country:
                    # Try alpha_2 match first
                    country = pycountry.countries.get(alpha_2=countryName.upper())

                if country and country not in matched:
                    matched.append(country)

            sorted_countries = sorted(matched, key=lambda country: country.name)
            return sorted_countries

        sorted_countries = sorted(list(pycountry.countries), key=lambda country: country.name)
        return sorted_countries

    def is_country( country_name: str) -> bool:
        return country_name in (c.name for c in LocationAddress.get_countries())

    def get_subdivisions(country_name: str, filter_to_users: bool = False) -> List[Dict[str, object]]:
        # Get all subdivisions for the specified country code
        if country_name not in LocationAddress.COUNTRY_SUBDIVISION_WHITELIST:
            return

        country = pycountry.countries.lookup(country_name)
        subdivisions = [s for s in pycountry.subdivisions if s.country_code == country.alpha_2]
    
        if (not subdivisions):
            return []

        # Filter the list to include only those with a type of 'State'
        subdivisions = [sub for sub in subdivisions]

        # If requested, filter to only subdivisions that appear in User.address_state
        if filter_to_users:
            try:
                # import here to avoid circular imports at module import time
                from vdgsa_backend.accounts.models import User

                states_qs = (
                    User.objects
                    .exclude(address_state__isnull=True)
                    .exclude(address_state="")
                    .order_by("address_state")
                    .values_list("address_state", flat=True)
                    .distinct("address_state")
                )
                states = [s.strip() for s in list(states_qs) if s and s.strip()]
            except Exception:
                states = []

            matched = []
            for state_code in states:
                subdivision = None
                # Try matching by code (upper case)
                subdivision = pycountry.subdivisions.get(code=f"{country.alpha_2}-{state_code.upper()}")
                if not subdivision:
                    # Try just the state code
                    subdivision = pycountry.subdivisions.get(code=state_code.upper())
                if not subdivision:
                    # Try matching by name (case-insensitive)
                    name_matches = [s for s in subdivisions if getattr(s, "name", "").lower() == state_code.lower()]
                    if name_matches:
                        subdivision = name_matches[0]

                if subdivision and subdivision not in matched:
                    matched.append(subdivision)

            sorted_subdivisions = sorted(matched, key=lambda state: state.name)
            return sorted_subdivisions

        # Default: return all subdivisions sorted by name
        sorted_subdivisions = sorted(subdivisions, key=lambda state: state.name)
        return sorted_subdivisions
