import datetime
from functools import cached_property
from typing import Any, Dict, Iterable, Literal

from django import forms
from django.apps import apps
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.storage import FileSystemStorage
from django.db.models import Count, F, Max, Q
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


class ListWaitingView(RentalViewBase, ListView):
    def get_queryset(self, *args: Any, **kwargs: Any):
        queryset = WaitingList.objects.all()
        return queryset

    template_name = 'wait/waitinglist.html'


class WaitingDetailView(RentalViewBase, DetailView):
    model = WaitingList
    template_name = 'wait/detail.html'


class UpdateWaitingView(RentalEditBase, SuccessMessageMixin, UpdateView):
    model = WaitingList
    template_name = 'wait/update.html'
    form_class = ReserveViolModelForm
    success_message = "Waiter was updated successfully"

    def get_context_data(self, **kwargs):
        context = super(UpdateWaitingView, self).get_context_data(**kwargs)
        context['entry_num'] = self.kwargs['pk']
        return context

    def get_success_url(self, **kwargs) -> str:
        return reverse('wait-detail', args=[self.object.pk])
