from django import forms
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as origGroupAdmin
from django.contrib.auth.models import Group, User

from vdgsa_backend.accounts.models import MembershipSubscription, User


class UserAdmin(admin.ModelAdmin):  # type: ignore
    exclude = ['password', 'last_login']
    search_fields = ['first_name', 'last_name', 'username']


class MembershipSubscriptionAdmin(admin.ModelAdmin):  # type: ignore
    def has_add_permission(self, *args: object) -> bool:
        return False


class GroupAdminForm(forms.ModelForm):
    """
    ModelForm that adds an additional multiple select field for managing
    the users in the group.
    Source: https://stackoverflow.com/questions/34568311\
/show-group-members-in-django-admin
    """
    users = forms.ModelMultipleChoiceField(
        User.objects.all(),
        widget=admin.widgets.FilteredSelectMultiple('Users', False),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(GroupAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            initial_users = self.instance.user_set.values_list('pk', flat=True)
            self.initial['users'] = initial_users

    def save(self, *args, **kwargs):
        kwargs['commit'] = True
        return super(GroupAdminForm, self).save(*args, **kwargs)

    def save_m2m(self):
        self.instance.user_set.clear()
        self.instance.user_set.add(*self.cleaned_data['users'])


class GroupAdmin(origGroupAdmin):
    """
    Customized GroupAdmin class that uses the customized form to allow
    management of users within a group.
    """
    form = GroupAdminForm


admin.site.register(User, UserAdmin)
admin.site.register(MembershipSubscription, MembershipSubscriptionAdmin)
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)
