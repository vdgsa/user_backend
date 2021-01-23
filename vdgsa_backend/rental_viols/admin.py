from django.contrib import admin

# Register your models here.
from django.contrib import admin

from vdgsa_backend.rental_viols.models import RentalHistory, Renter, Bow, Case, Viol, Manager, Image, WaitingList


class RentalHistoryAdmin(admin.ModelAdmin):  # type: ignore
    pass
# list_display = ['renter_num']

# def get_form(self, request, obj=None, **kwargs):
#     form = super(RentalHistoryAdmin, self).get_form(request, obj, **kwargs)
#     form.base_fields['renter_num'].label_from_instance = lambda obj: "{} {}".format(
#         obj.firstname, obj.lastname)
#     return form


class RenterAdmin(admin.ModelAdmin):  # type: ignore
    pass


class BowAdmin(admin.ModelAdmin):  # type: ignore
    pass


class CaseAdmin(admin.ModelAdmin):  # type: ignore
    pass


class ViolAdmin(admin.ModelAdmin):  # type: ignore
    pass


class ManagerAdmin(admin.ModelAdmin):  # type: ignore
    pass


class WaitingListAdmin(admin.ModelAdmin):  # type: ignore
    pass


class ImageAdmin(admin.ModelAdmin):  # type: ignore
    pass


admin.site.register(RentalHistory, RentalHistoryAdmin)
admin.site.register(Renter, RenterAdmin)

admin.site.register(Bow, BowAdmin)
admin.site.register(Case, CaseAdmin)
admin.site.register(Viol, ViolAdmin)

admin.site.register(Manager, ManagerAdmin)

admin.site.register(WaitingList, WaitingListAdmin)
admin.site.register(Image, ImageAdmin)
