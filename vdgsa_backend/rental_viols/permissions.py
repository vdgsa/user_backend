from typing import Union

from django.contrib.auth.models import AnonymousUser

from vdgsa_backend.accounts.models import User


def is_rental_manager(user: Union[User, AnonymousUser]) -> bool:
    return user.has_perm('accounts.rental_manager')
