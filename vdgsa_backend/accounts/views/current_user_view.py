from django.utils.translation import gettext_lazy as _
from rest_framework import permissions, serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from vdgsa_backend.api_schema.schema import CustomSchema

from ..models import MembershipSubscription, User


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


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'subscription',
            # 'owned_subscription',
            # 'subscription_is_family_member_for',
        ]
        read_only_fields = [
            'username',
            # 'owned_subscription',
            # 'subscription_is_family_member_for'
        ]
        depth = 1

    subscription = MembershipSubscriptionSerializer(read_only=True)


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

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

    def get(self, request: Request) -> Response:
        return Response(UserSerializer(request.user).data)
