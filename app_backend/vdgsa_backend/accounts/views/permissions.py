from typing import Union

from django.contrib.auth.models import AnonymousUser
from django.http.request import HttpRequest

from vdgsa_backend.accounts.models import User


def is_membership_secretary(user: Union[User, AnonymousUser]) -> bool:
    return user.has_perm('accounts.membership_secretary')


def is_requested_user_or_membership_secretary(requested_user: User, request: HttpRequest) -> bool:
    """
    Returns True if the authenticated user (request.user) is the same
    user as requested user, or if the authenticated user is the
    membership secretary.
    """
    return (
        is_membership_secretary(request.user)
        or request.user == requested_user
    )


def is_active_member(user: Union[User, AnonymousUser]) -> bool:
    return user.subscription_is_current
