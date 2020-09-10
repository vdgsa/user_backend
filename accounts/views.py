import itertools
from typing import Any
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from django.views import View

from rest_framework import viewsets, permissions, mixins, response
from rest_framework import request
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from .serializers import MembershipSubscriptionHistorySerializer, MembershipSubscriptionSerializer, UserSerializer
from .models import MembershipSubscription, MembershipSubscriptionHistory, User


class RequireAuthentication:
    """
    A mixin class that prepends permissions.IsAuthenticated to the list
    of permissions classes for the host class.
    """

    def get_permissions(self):
        return [permissions.IsAuthenticated()] + super().get_permissions()


class CurrentUserView(RequireAuthentication, APIView):
    def get(self, request, *args, **kwargs):
        return response.Response(UserSerializer(request.user).data)


class UserViewSetPermission(permissions.BasePermission):
    def has_permission(self, request: request.Request, view: View) -> bool:
        return request.user.has_perm('accounts.membership_secretary')

    def has_object_permission(self, request: request.Request, view: View, obj: Any) -> bool:
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


def _check_is_requested_user_or_membership_secretary(request: Request, user: User):
    if user != request.user and not user.has_perm('accounts.membership_secretary'):
        raise PermissionDenied


def _plus_one_calendar_year(start_at: timezone.datetime) -> timezone.datetime:
    return start_at.replace(year=start_at.year + 1)


# /api/users/:username/membership_subscription/
class MembershipSubscriptionView(RequireAuthentication, APIView):

    def get(self, request, *args, **kwargs):
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
            return response.Response(None)

        return response.Response(MembershipSubscriptionSerializer(subscription).data)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """
        Purchases a subscription for the specified user or renews
        their existing subscription.

        If the requester has the "membership_secretary" permission,
        then payment information is not required.

        FIXME: Handle lifetime members

        The requester must either be the same user as the one specified
        or have "membership_secretary" permission.
        """
        user = get_object_or_404(User.objects.select_for_update(), username=kwargs['username'])
        _check_is_requested_user_or_membership_secretary(request, user)

        if not hasattr(user, 'owned_subscription'):
            # Purchase new subscription
            now = timezone.now()
            valid_until = _plus_one_calendar_year(now)

            subscription = MembershipSubscription.objects.create(
                owner=user, valid_until=valid_until,
                membership_type=MembershipSubscription.MembershipType.regular
            )
            family_members = [
                User.objects.get_or_create(username=username)[0]
                for username in request.data.get('family_members', [])
            ]
            subscription.family_members.set(family_members)
            history_entry = MembershipSubscriptionHistory.objects.create(
                owner=user, valid_from=now, valid_until=valid_until,
                membership_type=subscription.membership_type
            )
            history_entry.family_members.set(family_members)
            return response.Response(MembershipSubscriptionSerializer(subscription).data)
        else:
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

            return response.Response(
                MembershipSubscriptionSerializer(user.owned_subscription).data)

    @transaction.atomic
    def put(self, request, *args, **kwargs):
        """
        Sets the family members of the requested user's subscription to
        the users with the given usernames. If any of the usernames
        don't exist, then a User object will be created.

        (FUTURE) Newly added family members will receive an email
        notification.
        """
        user = get_object_or_404(User.objects.select_for_update(), username=kwargs['username'])
        _check_is_requested_user_or_membership_secretary(request, user)

        if 'family_members' in request.data:
            user.owned_subscription.family_members.set([
                User.objects.get_or_create(username=username)[0]
                for username in request.data.get('family_members')
            ])
        return response.Response(
            MembershipSubscriptionSerializer(user.owned_subscription).data)


# /api/users/:username/membership_history/
class MembershipSubscriptionHistoryView(RequireAuthentication, APIView):
    def get(self, request, *args, **kwargs):
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
        return response.Response(
            MembershipSubscriptionHistorySerializer(history, many=True).data
        )
