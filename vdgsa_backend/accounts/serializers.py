from rest_framework import serializers

from .models import MembershipSubscription, MembershipSubscriptionHistory, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'owned_subscription',
            'subscription_is_family_member_for',
        ]
        read_only_fields = ['username', 'owned_subscription', 'subscription_is_family_member_for']
        depth = 1


class NestedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
        ]


class MembershipSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipSubscription
        fields = ['id', 'owner', 'family_members', 'valid_until', 'membership_type']
        read_only_fields = fields

    owner = NestedUserSerializer(read_only=True)
    family_members = NestedUserSerializer(many=True)


class MembershipSubscriptionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipSubscriptionHistory
        fields = ['id', 'owner', 'family_members', 'valid_from', 'valid_until', 'membership_type']
        read_only_fields = fields

    owner = NestedUserSerializer(read_only=True)
    family_members = NestedUserSerializer(many=True)
