from __future__ import annotations

from typing import Any, Dict, Literal, Optional, TypedDict

from django import forms
from django.apps import apps
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.storage import FileSystemStorage
from django.db.models import Count, F, IntegerField, Max, Q
from django.db.models.functions import Cast
from django.forms.forms import BaseForm
from django.forms.widgets import DateTimeBaseInput, HiddenInput
from django.http import Http404, JsonResponse, response
from django.http.request import HttpRequest
from django.http.response import (
    HttpResponse, HttpResponseNotFound, HttpResponseRedirect, JsonResponse
)
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
from vdgsa_backend.rental_viols.permissions import is_rental_manager, is_rental_viewer


def _createUserStamp(user):
    return ('\n\n\nRental Contact info:\n' + user.first_name + ' ' + user.last_name + '\n'
            + user.username + '\n'
            + user.address_line_1 + '\n'
            + user.address_city + ' '
            + user.address_state + ' '
            + user.address_postal_code + ' '
            + user.address_country + '\n'
            + user.phone1 + '\n')


class RentalViewBase(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self) -> bool:
        return is_rental_viewer(self.request.user) or is_rental_manager(self.request.user)

    def reverse(*args, **kwargs):
        get = kwargs.pop('get', {})
        url = reverse(*args, **kwargs)
        if get:
            url += '?' + urlencode(get)
        return url


class RentalEditBase(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self) -> bool:
        return is_rental_manager(self.request.user)

    def reverse(*args, **kwargs):
        get = kwargs.pop('get', {})
        url = reverse(*args, **kwargs)
        if get:
            url += '?' + urlencode(get)
        return url


class NotesOnlyHistoryForm(forms.ModelForm):
    item = forms.HiddenInput()

    class Meta:
        model = RentalHistory
        fields = ('notes',)
        labels = {'item': 'xxx', 'notes': 'Notes'}


class ReserveViolModelForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ReserveViolModelForm, self).__init__(*args, **kwargs)
        self.fields['viol_num'].queryset = Viol.objects.get_all().annotate(vdgsa_int=Cast(
            'vdgsa_number', IntegerField())).order_by('size', 'vdgsa_int')
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['address_line_1'].required = True

    class Meta:
        model = WaitingList
        fields = [
            'entry_num',
            'viol_num',
            'date_req',
            'size',
            'first_name',
            'last_name',
            'email',
            'address_line_1',
            'address_city',
            'address_state',
            'address_postal_code',
            'phone1',
            'notes',
        ]
        labels = {'phone1': 'Contact Phone', 'address_line_1': 'Mailing Address',
                  'date_req': 'Date added', 'first_name': 'First Name', 'last_name': 'Last Name'}


class AjaxFormResponse(JsonResponse):
    def __init__(self, data: AjaxFormResponseData, *args: Any, **kwargs: Any) -> None:
        super().__init__(data, *args, **kwargs)


AjaxFormResponseStatus = Literal['success', 'form_validation_error', 'other_error']


class AjaxFormResponseData(TypedDict):
    status: AjaxFormResponseStatus
    rendered_form: Optional[str]
    extra_data: Dict[str, object]


def get_ajax_form_response(
    status: AjaxFormResponseStatus,
    form: Optional[BaseForm],
    *,
    form_context: Optional[Dict[str, object]] = None,
    form_template: str = 'utils/form_body.tmpl',
    extra_data: Dict[str, object] = {},
) -> AjaxFormResponse:
    context: dict[str, object] = {'form': form}
    if form_context is not None:
        context.update(form_context)

    return AjaxFormResponse(
        {
            'status': status,
            'rendered_form': render_to_string(form_template, context),
            'extra_data': extra_data,
        },
        status=200,
    )
