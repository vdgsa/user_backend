from __future__ import annotations

from django.contrib.auth.models import AnonymousUser
from django.http.request import HttpRequest

from vdgsa_backend.accounts.models import User


def is_conclave_team(user: User | AnonymousUser) -> bool:
    return user.has_perm('conclave_registration.conclave_team')


def is_requested_user_or_membership_secretary(requested_user: User, request: HttpRequest) -> bool:
    """
    Returns True if the authenticated user (request.user) is the same
    user as requested user, or if the authenticated user has
    conclave team permission.
    """
    return (
        is_conclave_team(request.user)
        or request.user == requested_user
    )
