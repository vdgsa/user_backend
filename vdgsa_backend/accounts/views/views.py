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
    MembershipSubscription,
    MembershipSubscriptionHistory,
    PendingMembershipSubscriptionPurchase,
    User
)
from ..serializers import (
    MembershipSubscriptionHistorySerializer,
    MembershipSubscriptionSerializer,
    UserSerializer
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


# class ListUserViewSet(
#     RequireAuthentication,
#     mixins.ListModelMixin,
#     GenericViewSet
# ):
#     queryset = User.objects.all().order_by('username')
#     serializer_class = UserSerializer
#     permission_classes = [IsMembershipSecretary]


class IsMembershipSecretaryOrCurrentUser(permissions.BasePermission):
    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        return (cast(User, request.user).has_perm('accounts.membership_secretary')
                or view.kwargs['username'] == request.user.username)


# class RetrieveUpdateUserViewSet(
#     RequireAuthentication,
#     mixins.RetrieveModelMixin,
#     GenericViewSet
# ):
#     lookup_field = 'username'
#     lookup_value_regex = '.+'
#     queryset = User.objects.all()
#     serializer_class = UserSerializer
#     permission_classes = [IsMembershipSecretaryOrCurrentUser]


def _check_is_requested_user_or_membership_secretary(
    request: Request,
    requested_user: User
) -> None:
    request_sender = request.user
    if (requested_user != request_sender
            and not request_sender.has_perm('accounts.membership_secretary')):
        raise PermissionDenied


def _plus_one_calendar_year(start_at: timezone.datetime) -> timezone.datetime:
    return start_at.replace(year=start_at.year + 1)


# class StripeWebhookView(APIView):
#     # See https://stripe.com/docs/webhooks/build#example-code
#     def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
#         try:
#             event = stripe.Event.construct_from(
#                 request.data, stripe.api_key
#             )
#         except ValueError as e:
#             return Response(status=status.HTTP_400_BAD_REQUEST)
#         except stripe.error.SignatureVerificationError as e:
#             return Response(status=status.HTTP_400_BAD_REQUEST)

#         if event.type == 'payment_intent.succeeded':
#             # TODO: check "payment_type" in metadata
#             payment_intent = event.data.object
#             with transaction.atomic():
#                 pending_purchase = get_object_or_404(
#                     PendingMembershipSubscriptionPurchase.objects.select_for_update(),
#                     stripe_payment_intent_id=payment_intent.id
#                 )
#                 create_or_renew_subscription(pending_purchase.user)
#                 pending_purchase.is_completed = True
#                 pending_purchase.save()
#                 return Response()

#         return Response(status=status.HTTP_400_BAD_REQUEST)


# class MembershipSubscriptionView(RequireAuthentication, APIView):
#     schema = CustomSchema(
#         register_serializers={
#             'MembershipSubscription': MembershipSubscriptionSerializer
#         },
#         operation_data={
#             'GET': {
#                 'operationId': 'getMembershipSubscription',
#                 'responses': {
#                     '200': {
#                         'content': {
#                             'application/json': {
#                                 'schema': {
#                                     '$ref': '#/components/schemas/MembershipSubscription'
#                                 }
#                             }
#                         }
#                     },
#                 }
#             },
#             'POST': {
#                 'operationId': 'purchaseMembershipSubscription',
#                 'requestBody': {
#                     'content': {
#                         'application/json': {
#                             'schema': {
#                                 'properties': {
#                                     'membership_type': {
#                                         'type': 'string',
#                                         'enum': [
#                                             MembershipSubscription.MembershipType.regular.value,
#                                             MembershipSubscription.MembershipType.student.value,
#                                         ]
#                                     },
#                                     'donation': {
#                                         'type': 'integer',
#                                     }
#                                 },
#                                 'required': ['membership_type']
#                             }
#                         }
#                     }
#                 },
#                 'responses': {
#                     '202': {
#                         'content': {
#                             'application/json': {
#                                 'schema': {
#                                     'description': 'A stripe session checkout ID.',
#                                     'type': 'string'
#                                 }
#                             }
#                         }
#                     }
#                 }
#             }
#         }
#     )

#     def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
#         """
#         Returns the membership subscription associated
#         with the specified user (owner or family member).

#         The requester must either be the same user as the one specified
#         or have "membership_secretary" permission.
#         """
#         user = get_object_or_404(User, username=kwargs['username'])
#         _check_is_requested_user_or_membership_secretary(request, user)

#         if hasattr(user, 'owned_subscription'):
#             subscription = user.owned_subscription
#         elif user.subscription_is_family_member_for is not None:
#             subscription = user.subscription_is_family_member_for
#         else:
#             return Response(None)

#         return Response(MembershipSubscriptionSerializer(subscription).data)

#     @transaction.atomic
#     def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
#         """
#         Purchases a subscription for the specified user or renews
#         their existing subscription.

#         The requester must either be the same user as the one specified
#         or have "membership_secretary" permission.

#         If the requester does not have the "membership_secretary" permission,
#         or if the membership secretary is renewing their own membership,
#         a stripe checkout session is created and returned with 202 status.
#         Otherwise, the requested user's subscription is updated immediately
#         (no payment is initiated).

#         If a new subscription was created,
#         the subscription data is returned with 201 status.
#         If an existing subscription was renewed, the updated subscription
#         data is returned with 200 status.

#         If the requested user is a lifetime member, no action is taken
#         and 400 status is returned.
#         """
#         user = get_object_or_404(User.objects.select_for_update(), username=kwargs['username'])
#         _check_is_requested_user_or_membership_secretary(request, user)

#         membership_type = request.data.get('membership_type', None)
#         if membership_type is None:
#             return Response(
#                 'Missing required request body key "membership_type"',
#                 status.HTTP_400_BAD_REQUEST
#             )

#         line_items = []
#         total = 0

#         if membership_type == MembershipSubscription.MembershipType.lifetime:
#             return Response(
#                 'This API endpoint cannot be used for granting lifetime memberships',
#                 status.HTTP_400_BAD_REQUEST
#             )

#         # If the request sender is not the specified user, they must be the membership secretary.
#         if request.user != user:
#             return Response(
#                 MembershipSubscriptionSerializer(create_or_renew_subscription(user)).data
#             )

#         if membership_type == MembershipSubscription.MembershipType.student:
#             student_rate = 35 * 100  # FIXME: get actual number
#             # total += student_rate
#             line_items.append({
#                 'price_data': {
#                     'currency': 'usd',
#                     'product_data': {
#                         'name': '1-year Student Membership'
#                     },
#                     'unit_amount': student_rate
#                 },
#                 'quantity': 1,
#             })
#         elif membership_type == MembershipSubscription.MembershipType.regular:
#             regular_rate = 40 * 100  # FIXME: get actual number
#             # total += regular_rate
#             line_items.append({
#                 'price_data': {
#                     'currency': 'usd',
#                     'product_data': {
#                         'name': '1-year Membership'
#                     },
#                     'unit_amount': regular_rate
#                 },
#                 'quantity': 1,
#             })
#         else:
#             return Response(
#                 f'Invalid membership type: {membership_type}',
#                 status.HTTP_400_BAD_REQUEST
#             )

#         try:
#             donation = int(request.data.get('donation', 0))
#         except ValueError:
#             return Response('"donation" must be a number', status.HTTP_400_BAD_REQUEST)

#         if donation < 0:
#             return Response('"donation" may not be negative', status.HTTP_400_BAD_REQUEST)

#         if donation:
#             # total += donation
#             line_items.append({
#                 'price_data': {
#                     'currency': 'usd',
#                     'product_data': {
#                         'name': 'Donation'
#                     },
#                     'unit_amount': donation * 100
#                 },
#                 'quantity': 1,
#             })

#         session = stripe.checkout.Session.create(
#             payment_method_types=['card'],
#             line_items=line_items,
#             mode='payment',
#             customer_email=user.username,
#             success_url='https://webmaster85689.wixsite.com/vdgsa-test',
#             cancel_url='https://webmaster85689.wixsite.com/vdgsa-test',
#             metadata={'transaction_type': 'membership'}
#         )

#         PendingMembershipSubscriptionPurchase.objects.create(
#             user=user,
#             stripe_payment_intent_id=session.payment_intent,
#         )

#         return Response(session.id)

#     @transaction.atomic
#     def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
#         """
#         Sets the family members of the requested user's subscription to
#         the users with the given usernames. If any of the usernames
#         don't exist, then a User object will be created.

#         (FUTURE) Newly added family members will receive an username
#         notification.
#         """
#         user = get_object_or_404(User.objects.select_for_update(), username=kwargs['username'])
#         _check_is_requested_user_or_membership_secretary(request, user)

#         if 'family_members' in request.data:
#             family_members = []
#             for username in request.data['family_members']:
#                 try:
#                     family_members.append(User.objects.get(username=username))
#                 except ObjectDoesNotExist:
#                     return Response(
#                         f'Requested family memebr {username} does not exist.'
#                         'Please have them create and account and then try your request again.',
#                         400
#                     )

#             user.owned_subscription.family_members.set(family_members)

#         return Response(
#             MembershipSubscriptionSerializer(user.owned_subscription).data)


# @transaction.atomic
# def create_or_renew_subscription(user: User) -> MembershipSubscription:
#     """
#     Extends the given user's membership subscription by 1 year. If the
#     user does not own a membership subscription, one is created.

#     Returns the new or updated MembershipSubscription object.
#     """
#     if not hasattr(user, 'owned_subscription'):
#         # Purchase new subscription
#         now = timezone.now()
#         valid_until = _plus_one_calendar_year(now)

#         subscription = MembershipSubscription.objects.create(
#             owner=user, valid_until=valid_until,
#             membership_type=MembershipSubscription.MembershipType.regular
#         )
#         history_entry = MembershipSubscriptionHistory.objects.create(
#             owner=user, valid_from=now, valid_until=valid_until,
#             membership_type=subscription.membership_type
#         )

#         return subscription
#     else:
#         if (user.owned_subscription.membership_type
#                 == MembershipSubscription.MembershipType.lifetime):
#             return user.owned_subscription

#         # Only lifetime members should have valid_until be None.
#         assert user.owned_subscription.valid_until is not None
#         # Extend existing subscription by 1 year
#         valid_from = user.owned_subscription.valid_until
#         valid_until = _plus_one_calendar_year(user.owned_subscription.valid_until)
#         user.owned_subscription.valid_until = valid_until
#         user.owned_subscription.save()

#         history_entry = MembershipSubscriptionHistory.objects.create(
#             owner=user, valid_from=valid_from, valid_until=valid_until,
#             membership_type=user.owned_subscription.membership_type
#         )
#         history_entry.family_members.set(list(user.owned_subscription.family_members.all()))
#         return user.owned_subscription


# class MembershipSubscriptionHistoryView(RequireAuthentication, APIView):
#     schema = None  # type: ignore

#     def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
#         """
#         Returns a list of MembershipSubscriptionHistory objects
#         for the user with the given username.

#         The requester must either be the same user as the one specified
#         or have "membership_secretary" permission.
#         """
#         user = get_object_or_404(User, username=kwargs['username'])
#         _check_is_requested_user_or_membership_secretary(request, user)

#         history = list(
#             sorted(
#                 itertools.chain(
#                     user.owned_subscription_history.all().order_by('-pk'),
#                     user.subscription_history_as_family_member.all().order_by('-pk')
#                 ),
#                 key=lambda entry: entry.pk,
#                 reverse=True
#             )
#         )
#         return Response(
#             MembershipSubscriptionHistorySerializer(history, many=True).data
#         )
