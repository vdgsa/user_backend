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

    def getCountries() -> List[Dict[str, object]]:
        # Get the iterable collection of country objects and convert it to a list
        countries_list = list(pycountry.countries)

        # Sort the list of country objects by their 'name' attribute
        sorted_countries = sorted(countries_list, key=lambda country: country.name)
        return sorted_countries
    
        

    
    def getSubdivisions(country_code: str) -> List[Dict[str, object]]:
        # Get all subdivisions for the United States ('US')
        subdivisions = pycountry.subdivisions.get(country_code=country_code)

        if(not subdivisions):
            return []
        
        # Filter the list to include only those with a type of 'State'
        subdivisions = [sub for sub in subdivisions ]

        # Sort the list of state objects by name
        sorted_subdivisions = sorted(subdivisions, key=lambda state: state.name)
        return sorted_subdivisions
    
