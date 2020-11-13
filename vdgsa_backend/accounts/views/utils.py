from django.forms.forms import BaseForm
from django.http.response import HttpResponse
from django.template.loader import render_to_string


def get_ajax_form_response(form: BaseForm, status: int) -> HttpResponse:
    """
    Renders the given form using a minimal template and returns
    an HTTP response with the specified status and with the rendered
    content in the request body as text.

    The returned content is suitable for being placed inside
    an HTML <form> element.
    """
    return HttpResponse(
        render_to_string('utils/form_body.tmpl', {'form': form}),
        status=status
    )
