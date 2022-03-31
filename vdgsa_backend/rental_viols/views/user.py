import datetime
from functools import cached_property
from typing import Any, Dict, Iterable, Literal

from django import forms
from django.apps import apps
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.storage import FileSystemStorage
from django.db import connection
from django.db.models import Count, F, IntegerField, Max, Q
from django.db.models.functions import Cast
from django.forms.widgets import DateTimeBaseInput, HiddenInput
from django.http import Http404, JsonResponse, response
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls.base import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import urlencode
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.generic.list import ListView

from vdgsa_backend.accounts.models import User
from vdgsa_backend.rental_viols.managers.InstrumentManager import AccessoryManager, ViolManager
from vdgsa_backend.rental_viols.managers.RentalItemBaseManager import (
    RentalEvent, RentalItemBaseManager, RentalState
)
from vdgsa_backend.rental_viols.models import (
    Bow, Case, Image, ItemType, RentalContract, RentalHistory, RentalProgram, Viol, ViolSize,
    WaitingList
)
from vdgsa_backend.rental_viols.permissions import is_rental_manager
from vdgsa_backend.rental_viols.views.utils import (
    NotesOnlyHistoryForm, RentalEditBase, RentalViewBase, ReserveViolModelForm, _createUserStamp
)


class MoveRentalUserReference(RentalEditBase, View):
    template_name = 'users/move.html'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        context['user'] = User.objects.get(pk=self.kwargs['pk'])
        return render(
            self.request,
            'users/move.html', context
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any):
        oldUserId = self.kwargs['pk']
        newUserId = self.request.POST.get('user_id')
        if (newUserId and oldUserId):
            cursor = connection.cursor()
            cursor.execute('UPDATE rental_viols_rentalhistory SET renter_num_id = %(newUserId)s \
                                WHERE renter_num_id = %(oldUserId)s; \
                            UPDATE rental_viols_waitinglist SET renter_num_id = %(newUserId)s \
                                WHERE renter_num_id = %(oldUserId)s; \
                            UPDATE rental_viols_viol SET renter_id = %(newUserId)s \
                                WHERE renter_id = %(oldUserId)s; \
                            UPDATE rental_viols_viol SET storer_id = %(newUserId)s \
                                WHERE storer_id = %(oldUserId)s; \
                            UPDATE rental_viols_bow SET storer_id = %(newUserId)s \
                                WHERE storer_id = %(oldUserId)s; \
                            UPDATE rental_viols_case SET storer_id = %(newUserId)s \
                                WHERE storer_id = %(oldUserId)s; ', {'newUserId': newUserId,
                                                                     'oldUserId': oldUserId})

        return redirect(reverse('renter-info', args=[newUserId]))


class ViewUserInfo(RentalViewBase, DetailView):
    model = User
    template_name = 'renters/userDetail.html'

    def get_context_data(self, **kwargs):

        context = super(ViewUserInfo, self).get_context_data(**kwargs)
        context['history'] = (RentalHistory.objects.all().filter(
                              Q(event=RentalEvent.rented)
                              | Q(event=RentalEvent.renewed)
                              | Q(event=RentalEvent.returned)).filter(
                                  renter_num=self.kwargs['pk'])).annotate(
                                      rental_end_date=Max('rental_end'))
        # .annotate(rental_end_date=Max('rental_end')
        return context


class UserSearchViewAjax(RentalViewBase, View):
    """Filter list of users """
    @csrf_exempt
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        search_str = request.GET.get("q")
        context = {}
        if search_str:
            users = User.objects.filter(Q(first_name__icontains=search_str)
                                        | Q(last_name__icontains=search_str))
        else:
            users = User.objects.all()

        context["users"] = users
        html = render_to_string(
            template_name="users/user-results-partial.html", context={"users": users}
        )
        data_dict = {"html_from_view": html}
        return JsonResponse(data=data_dict, safe=False)
