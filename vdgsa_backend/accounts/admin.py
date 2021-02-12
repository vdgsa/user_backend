from django.contrib import admin

from vdgsa_backend.accounts.models import MembershipSubscription, User


class UserAdmin(admin.ModelAdmin):  # type: ignore
    exclude = ['password', 'last_login']


class MembershipSubscriptionAdmin(admin.ModelAdmin):  # type: ignore
    def has_add_permission(self, *args: object) -> bool:
        return False


admin.site.register(User, UserAdmin)
admin.site.register(MembershipSubscription, MembershipSubscriptionAdmin)
