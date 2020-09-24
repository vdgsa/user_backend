import itertools
from functools import wraps
from typing import Any, Callable, Dict, List, Union

from django.contrib.auth import password_validation
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework import mixins, permissions, response, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from .models import MembershipSubscription, MembershipSubscriptionHistory, User
from .serializers import (
    MembershipSubscriptionHistorySerializer,
    MembershipSubscriptionSerializer,
    UserSerializer
)


def convert_django_validation_error(func: Callable[..., Any]) -> Callable[..., Any]:
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

    return decorated_func


class IsAuthenticatedAndActive(permissions.IsAuthenticated):
    """
    Permissions class that checks that the user is authenticated
    and that the user is active (specified by User.is_active).
    """
    def has_permission(self, request: Request, view: View) -> bool:
        is_authenticated = super().has_permission(request, view)
        if not is_authenticated:
            return False

        return request.user.is_active

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        is_authenticated = super().has_object_permission(request, view, obj)
        if not is_authenticated:
            return False

        return request.user.is_active


class RequireAuthentication:
    """
    A mixin class that prepends IsAuthenticatedAndActive to the list
    of permissions classes for the host class.
    """
    def get_permissions(self) -> List[permissions.BasePermission]:
        return [IsAuthenticatedAndActive()] + super().get_permissions()  # type: ignore


class CurrentUserView(RequireAuthentication, APIView):
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return Response(UserSerializer(request.user).data)


class UserViewSetPermission(permissions.BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        return request.user.has_perm('accounts.membership_secretary')

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        return (request.user.has_perm('accounts.membership_secretary')
                or request.kwargs['pk'] == request.user.pk)


class UserViewSet(
    RequireAuthentication,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet
):
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer
    permission_classes = [UserViewSetPermission]


class UserRegistrationView(APIView):
    @convert_django_validation_error
    @transaction.atomic
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        username = request.data['username']
        password = request.data['password']
        password_validation.validate_password(password)
        try:
            user = User.objects.create_user(username, password)
            user.full_clean()
            token = Token.objects.create(user=user)
            return Response({'token': token.key}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response('A user with this username address already exists')


def _check_is_requested_user_or_membership_secretary(request: Request, user: User) -> None:
    if user != request.user and not user.has_perm('accounts.membership_secretary'):
        raise PermissionDenied


def _plus_one_calendar_year(start_at: timezone.datetime) -> timezone.datetime:
    return start_at.replace(year=start_at.year + 1)


class StripeWebhookView(APIView):
    # See https://stripe.com/docs/webhooks/build#example-code
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        # try:
        #     event = stripe.Event.construct_from(
        #         request.data, stripe.api_key
        #     )
        # except ValueError as e:
        #     return Response(status=status.HTTP_400_BAD_REQUEST)

        # if event.type == 'payment_intent.succeeded':
        #     payment_intent = event.data.object
        #     return Response()

        # return Response(status=status.HTTP_400_BAD_REQUEST)


# /api/users/:username/membership_subscription/
class MembershipSubscriptionView(RequireAuthentication, APIView):
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Returns the membership subscription associated
        with the specified user (owner or family member).

        The requester must either be the same user as the one specified
        or have "membership_secretary" permission.
        """
        user = get_object_or_404(User, username=kwargs['username'])
        _check_is_requested_user_or_membership_secretary(request, user)

        if hasattr(user, 'owned_subscription'):
            subscription = user.owned_subscription
        elif user.subscription_is_family_member_for is not None:
            subscription = user.subscription_is_family_member_for
        else:
            return Response(None)

        return Response(MembershipSubscriptionSerializer(subscription).data)

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Purchases a subscription for the specified user or renews
        their existing subscription.

        The requester must either be the same user as the one specified
        or have "membership_secretary" permission.

        If the requester does not have the "membership_secretary" permission,
        or if the membership secretary is renewing their own membership,
        a stripe checkout session is created and returned with 202 status.

        Otherwise, the requested user's subscription is updated immediately
        (no payment is initiated). If a new subscription was created,
        the subscription data is returned with 201 status.
        If an existing subscription was renewed, the updated subscription
        data is returned with 200 status.

        If the requested user is a lifetime member, no action is taken
        and 400 status is returned.
        """
        user = get_object_or_404(User.objects.select_for_update(), username=kwargs['username'])
        _check_is_requested_user_or_membership_secretary(request, user)

        # If the requester is not the requested user, they must be the membership secretary.
        if request.user != user:
            return Response(
                MembershipSubscriptionSerializer(_create_or_renew_subscription(user)).data
            )

        # TODO: Create stripe session and return it.
        return Response('stripe payment not implemented yet.', status=400)

    @transaction.atomic
    def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Sets the family members of the requested user's subscription to
        the users with the given usernames. If any of the usernames
        don't exist, then a User object will be created.

        (FUTURE) Newly added family members will receive an username
        notification.
        """
        user = get_object_or_404(User.objects.select_for_update(), username=kwargs['username'])
        _check_is_requested_user_or_membership_secretary(request, user)

        if 'family_members' in request.data:
            family_members = []
            for username in request.data['family_members']:
                try:
                    family_members.append(User.objects.get(username=username))
                except ObjectDoesNotExist:
                    return Response(
                        f'Requested family memebr {username} does not exist.'
                        'Please have them create and account and then try your request again.',
                        400
                    )

            user.owned_subscription.family_members.set(family_members)

        return Response(
            MembershipSubscriptionSerializer(user.owned_subscription).data)


@transaction.atomic
def _create_or_renew_subscription(user: User) -> MembershipSubscription:
    """
    Extends the given user's membership subscription by 1 year. If the
    user does not own a membership subscription, one is created.

    Returns the new or updated MembershipSubscription object.
    """
    if not hasattr(user, 'owned_subscription'):
        # Purchase new subscription
        now = timezone.now()
        valid_until = _plus_one_calendar_year(now)

        subscription = MembershipSubscription.objects.create(
            owner=user, valid_until=valid_until,
            membership_type=MembershipSubscription.MembershipType.regular
        )
        history_entry = MembershipSubscriptionHistory.objects.create(
            owner=user, valid_from=now, valid_until=valid_until,
            membership_type=subscription.membership_type
        )

        return subscription
    else:
        if (user.owned_subscription.membership_type
                == MembershipSubscription.MembershipType.lifetime):
            return user.owned_subscription

        # Only lifetime members should have valid_until be None.
        assert user.owned_subscription.valid_until is not None
        # Extend existing subscription by 1 year
        valid_from = user.owned_subscription.valid_until
        valid_until = _plus_one_calendar_year(user.owned_subscription.valid_until)
        user.owned_subscription.valid_until = valid_until
        user.owned_subscription.save()

        history_entry = MembershipSubscriptionHistory.objects.create(
            owner=user, valid_from=valid_from, valid_until=valid_until,
            membership_type=user.owned_subscription.membership_type
        )
        history_entry.family_members.set(list(user.owned_subscription.family_members.all()))
        return user.owned_subscription


# /api/users/:username/membership_history/
class MembershipSubscriptionHistoryView(RequireAuthentication, APIView):
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Returns a list of MembershipSubscriptionHistory objects
        for the user with the given username.

        The requester must either be the same user as the one specified
        or have "membership_secretary" permission.
        """
        user = get_object_or_404(User, username=kwargs['username'])
        _check_is_requested_user_or_membership_secretary(request, user)

        history = list(
            sorted(
                itertools.chain(
                    user.owned_subscription_history.all().order_by('-pk'),
                    user.subscription_history_as_family_member.all().order_by('-pk')
                ),
                key=lambda entry: entry.pk,
                reverse=True
            )
        )
        return Response(
            MembershipSubscriptionHistorySerializer(history, many=True).data
        )
