from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render


def stripe_checkout_view(request: HttpRequest, stripe_session_id: str) -> HttpResponse:
    return render(
        request,
        'stripe_checkout/checkout.html',
        context={'stripe_session_id': stripe_session_id}
    )


def stripe_cancel_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'stripe_checkout/cancel.html')
