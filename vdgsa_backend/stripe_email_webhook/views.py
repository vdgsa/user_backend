from __future__ import annotations

import json
from typing import Any, Dict, Final, List

import stripe  # type: ignore
from django.core.mail import send_mail
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt

LINE_ITEM_NAMES_TO_OFFICER_EMAILS: Final[Dict[str, List[str]]] = {
    'advertising': ['advertising@vdgsa.org'],
    'Rental Viol': ['rentalviol@vdgsa.org'],
    'Sheet Music': ['arenken@sandwich.net'],
    'Books and Merchandise': ['arenken@sandwich.net'],
    "Young Players' Weekend": ['pafunes@me.com'],
    "Professional Development Weekend": ['janelhershey@gmail.com'],
}


# See https://stripe.com/docs/webhooks/build#example-code
@csrf_exempt
def stripe_officer_email_view(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    """
    Send emails to the right officers (treasurer, rental viol manager)
    upon receiving payments from stripe.
    """
    try:
        request_data = json.loads(request.body)
        event = stripe.Event.construct_from(
            request_data, stripe.api_key
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        return HttpResponse(str(e), status=400)

    if event.type == 'checkout.session.completed':
        line_items = stripe.checkout.Session.list_line_items(
            event.data.object.id, limit=100
        )

        customer_email = event.data.object.customer_email
        for item in line_items.data:
            product = stripe.Product.retrieve(item.price.product)
            recipients = ['treasurer@vdgsa.org']
            if product.name in LINE_ITEM_NAMES_TO_OFFICER_EMAILS:
                recipients += LINE_ITEM_NAMES_TO_OFFICER_EMAILS[product.name]

            send_mail(
                subject=f'{customer_email} has made a {product.name} payment',
                from_email='webmaster@vdgsa.org',
                recipient_list=recipients,
                message=f'{customer_email} has made a '
                        f'{item.price.unit_amount / 100:.2f}{item.price.currency} '
                        f'payment of type "{product.name}".\n\n'
                        f'Description: {item.description}'
            )

        return HttpResponse('Emails sent')

    return HttpResponse(f'No action taken for "{event.type}" event')
