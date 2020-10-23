from django.http.request import HttpRequest

from vdgsa_backend.accounts.models import User


def is_requested_user_or_membership_secretary(requested_user: User, request: HttpRequest) -> bool:
    """
    Returns True if the authenticated user (request.user) is the same
    user as requested user, or if the authenticated user is the
    membership secretary.
    """
    return (
        request.user.has_perm('accounts.membership_secretary')
        or request.user == requested_user
    )
