"""
Contains an API endpoint that returns basic info about the currently
authenticated user.
"""

from django.contrib.auth.models import AnonymousUser
from django.http.request import HttpRequest
from django.http.response import HttpResponse, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View


class CurrentUserView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        if isinstance(request.user, AnonymousUser):
            return HttpResponse(status=401)

        user = request.user
        subscription = user.subscription

        if subscription is None:
            subscription_data = None
        else:
            subscription_data = {
                'id': subscription.id,
                'owner': {
                    'id': subscription.owner.id,
                    'username': subscription.owner.username,
                },
                'family_members': [
                    {
                        'id': family_member.id,
                        'username': family_member.username,
                    }
                    for family_member in subscription.family_members.all()
                ],
                'valid_until': subscription.valid_until,
                'membership_type': subscription.membership_type,
            }

        return JsonResponse({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'subscription': subscription_data,
            'subscription_is_current': user.subscription_is_current,
            'last_modified': user.last_modified,
        })
