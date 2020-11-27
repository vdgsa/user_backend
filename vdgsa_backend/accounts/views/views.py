import itertools
from functools import wraps
from typing import Any, Callable, Dict, List, TypeVar, Union, cast

import stripe  # type: ignore
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework import mixins, permissions, status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from vdgsa_backend.api_schema.schema import CustomSchema

from ..models import (
    MembershipSubscription, MembershipSubscriptionHistory, MembershipType,
    PendingMembershipSubscriptionPurchase, User
)
from ..serializers import (
    MembershipSubscriptionHistorySerializer, MembershipSubscriptionSerializer, UserSerializer
)

# See https://github.com/python/mypy/issues/3157
_DecoratedFunc = TypeVar('_DecoratedFunc', bound=Callable[..., Any])


def convert_django_validation_error(func: _DecoratedFunc) -> _DecoratedFunc:
    """
    If the decorated function raises django.core.exceptions.ValidationError,
    catches the error and raises rest_framework.exceptions.ValidationError
    with the same content.
    """
    @wraps(func)
    def decorated_func(*args, **kwargs):  # type: ignore  ## Wait for PEP 612
        try:
            return func(*args, **kwargs)
        except DjangoValidationError as e:
            detail: Union[str, List[Any], Dict[str, Any]] = ''
            if hasattr(e, 'message_dict'):
                detail = e.message_dict
            elif hasattr(e, 'message'):
                detail = e.message
            elif hasattr(e, 'messages'):
                detail = e.messages

            raise DRFValidationError(detail)

    return cast(_DecoratedFunc, decorated_func)


class IsAuthenticatedAndActive(permissions.IsAuthenticated):
    """
    Permissions class that checks that the user is authenticated
    and that the user is active (specified by User.is_active).
    """
    def has_permission(self, request: Request, view: View) -> bool:
        is_authenticated = super().has_permission(request, view)
        if not is_authenticated:
            return False

        return cast(User, request.user).is_active

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        is_authenticated = super().has_object_permission(request, view, obj)
        if not is_authenticated:
            return False

        return cast(User, request.user).is_active


class RequireAuthentication:
    """
    A mixin class that prepends IsAuthenticatedAndActive to the list
    of permissions classes for the host class.
    """
    def get_permissions(self) -> List[permissions.BasePermission]:
        return [IsAuthenticatedAndActive()] + super().get_permissions()  # type: ignore


class CurrentUserView(RequireAuthentication, APIView):
    schema = CustomSchema(
        register_serializers={
            'User': UserSerializer
        },
        operation_data={
            'GET': {
                'operationId': 'getCurrentUser',
                'responses': {
                    '200': {
                        'description': 'Returns the current authenticated User',
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/User'
                                }
                            }
                        }
                    },
                    '401': {
                        'description': 'The requester is not authenticated.'
                    }
                }
            }
        }
    )

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return Response(UserSerializer(request.user).data)


class IsMembershipSecretary(permissions.BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        return cast(User, request.user).has_perm('accounts.membership_secretary')


class IsMembershipSecretaryOrCurrentUser(permissions.BasePermission):
    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        return (cast(User, request.user).has_perm('accounts.membership_secretary')
                or view.kwargs['username'] == request.user.username)
