# Register your models here.
from django.contrib import admin

from vdgsa_backend.rental_viols.models import (
    Bow, Case, Image, RentalContract, RentalHistory, Viol, WaitingList
)


class RentalHistoryAdmin(admin.ModelAdmin):  # type: ignore
    pass
# list_display = ['renter_num']

# def get_form(self, request, obj=None, **kwargs):
#     form = super(RentalHistoryAdmin, self).get_form(request, obj, **kwargs)
#     form.base_fields['renter_num'].label_from_instance = lambda obj: "{} {}".format(
#         obj.firstname, obj.lastname)
#     return form


class BowAdmin(admin.ModelAdmin):  # type: ignore
    pass


class CaseAdmin(admin.ModelAdmin):  # type: ignore
    pass


class ViolAdmin(admin.ModelAdmin):  # type: ignore
    list_filter = ['size', 'state', 'program']
    search_fields = ['maker']


class WaitingListAdmin(admin.ModelAdmin):  # type: ignore
    pass


class ImageAdmin(admin.ModelAdmin):  # type: ignore
    pass


class RentalContractAdmin(admin.ModelAdmin):  # type: ignore
    pass


class RentalHistoryAdmin(admin.ModelAdmin):  # type: ignore
    pass


admin.site.register(RentalHistory, RentalHistoryAdmin)

admin.site.register(Bow, BowAdmin)
admin.site.register(Case, CaseAdmin)
admin.site.register(Viol, ViolAdmin)

admin.site.register(WaitingList, WaitingListAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(RentalContract, RentalContractAdmin)
