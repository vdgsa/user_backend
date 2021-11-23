import datetime
from functools import cached_property
from typing import Any, Dict, Iterable, Literal

from django import forms
from django.apps import apps
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.storage import FileSystemStorage
from django.db.models import Count, F, Max, OuterRef, Q, Subquery
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
    NotesOnlyHistoryForm, RentalViewBase, ReserveViolModelForm, _createUserStamp
)


class ListBowsView(RentalViewBase, ListView):
    model = Bow
    filterSessionName = 'bow_filter'
    template_name = 'bows/list_bows.html'
    filter = None

    def getFilter(self, **kwargs):
        filter = {}
        if self.request.GET.get('state') is None:
            filter = self.request.session.get(self.filterSessionName, None)
            if filter is None:
                filter = {'state': 'all'}
        else:
            filter = {'state': self.request.GET.get('state') or 'all'}
        return filter

    def get_context_data(self, **kwargs):
        context = super(ListBowsView, self).get_context_data(**kwargs)
        context['filter'] = self.getFilter()
        return context

    def get_queryset(self, *args: Any, **kwargs: Any):
        filter = self.getFilter()
        self.request.session[self.filterSessionName] = filter

        if filter['state'] == 'available':
            queryset = Bow.objects.get_available()
        elif filter['state'] == 'retired':
            queryset = Bow.objects.get_retired()
        elif filter['state'] == 'rented':
            queryset = Bow.objects.get_rented()
        else:
            queryset = Bow.objects.get_all()

        # for bow in queryset:
            # print(bow.__dict__)

        return queryset


# CRUD
class BowForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BowForm, self).__init__(*args, **kwargs)
        self.fields['vdgsa_number'].widget = HiddenInput()

    class Meta:
        model = Bow
        fields = [
            'vdgsa_number',
            'maker',
            'size',
            'value',
            'provenance',
            'description',
            'accession_date',
            'notes',
            'storer',
            'program',
        ]
        labels = {'storer': 'Custodian', 'vdgsa_number': '', }
        widgets = {
            'accession_date': forms.DateInput(format=('%Y-%m-%d'),
                                              attrs={'class': 'form-control',
                                                     'placeholder': 'Select a date',
                                                     'type': 'date'}),
        }


class AddBowView(RentalViewBase, SuccessMessageMixin, CreateView):
    model = Bow
    form_class = BowForm
    initial = {
        'vdgsa_number': Bow.objects.get_next_accessory_vdgsa_num,
        'accession_date': datetime.date.today}
    success_message = "%(size)s bow was created successfully"
    template_name = 'bows/add_bow.html'


class UpdateBowView(RentalViewBase, SuccessMessageMixin, UpdateView):
    model = Bow
    form_class = BowForm
    template_name = 'bows/update.html'
    success_message = "%(size)s bow was created successfully"

    def get_success_url(self, **kwargs) -> str:
        return reverse('list-bows')


class BowDetailView(RentalViewBase, DetailView):
    model = Bow
    template_name = 'bows/bow_detail.html'

    def get_context_data(self, **kwargs):
        context = super(BowDetailView, self).get_context_data(**kwargs)
        context['images'] = Image.objects.get_images('bow', context['bow'].pk)
        return context


class AvailableBowView(RentalViewBase, FormView):
    """Make Available"""
    template_name = 'viols/available.html'
    form_class = NotesOnlyHistoryForm
    model = RentalHistory

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        form = NotesOnlyHistoryForm(initial={'item': self.kwargs['pk']})
        context = self.get_context_data(**kwargs)
        context['form'] = form

        context['viol'] = Bow.objects.get(pk=self.kwargs['pk'])
        # context['form'] = RentalHistoryForm(
        #     {"event": RentalEvent.retired, "pk": viol.pk,
        #         "case_num": viol.cases.first().case_num if viol.cases.exists() else None,
        #         "bow_num": viol.bows.first().bow_num if viol.bows.exists() else None})

        return render(request, 'viols/available.html', context)

    def form_valid(self, form):
        bow = Bow.objects.get(pk=self.request.POST['pk'])
        bow.status = RentalState.available
        bow.save()
        history = RentalHistory.objects.create(
            bow_num=bow,
            event=RentalState.available,
            notes=form.cleaned_data['notes'])
        history.save()

        messages.add_message(self.request, messages.SUCCESS, 'Bow Made Available!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('bow-detail', args=[self.request.POST.get('pk')])


class RetireBowView(RentalViewBase, FormView):
    """Retire Bow"""
    template_name = './retireMulti.html'
    form_class = NotesOnlyHistoryForm
    model = RentalHistory

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        form = NotesOnlyHistoryForm(initial={'item': self.kwargs['pk']})
        context = self.get_context_data(**kwargs)
        context['item'] = Bow.objects.get(pk=self.kwargs['pk'])
        context['form'] = form
        return render(request, self.template_name, context)

    def form_valid(self, form):
        item = Bow.objects.get(pk=self.kwargs['pk'])
        item.status = RentalState.retired
        item.save()
        history = RentalHistory.objects.create(
            bow_num=item,
            event=RentalEvent.retired,
            notes=form.cleaned_data['notes'])
        history.save()

        messages.add_message(self.request, messages.SUCCESS, 'Bow Retired!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('bow-detail', args=[self.kwargs['pk']])
