from __future__ import annotations

from typing import Any, Dict, Literal, Optional, TypedDict

from django.forms.forms import BaseForm
from django.http.response import JsonResponse
from django.template.loader import render_to_string


class AjaxFormResponse(JsonResponse):
    def __init__(self, data: AjaxFormResponseData, *args: Any, **kwargs: Any) -> None:
        super().__init__(data, *args, **kwargs)


AjaxFormResponseStatus = Literal['success', 'form_validation_error']


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
    if form is None:
        rendered_form = None
    else:
        if form_context is None:
            form_context = {'form': form}
        rendered_form = render_to_string(form_template, form_context)

    return AjaxFormResponse(
        {
            'status': status,
            'rendered_form': rendered_form,
            'extra_data': extra_data,
        },
        status=200,
    )
