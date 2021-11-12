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
from vdgsa_backend.rental_viols.views.utils import ( 
    RentalViewBase, NotesOnlyHistoryForm, ReserveViolModelForm, _createUserStamp
)
from vdgsa_backend.rental_viols.managers.InstrumentManager import AccessoryManager, ViolManager
from vdgsa_backend.rental_viols.managers.RentalItemBaseManager import (
    RentalEvent, RentalItemBaseManager, RentalState
)
from vdgsa_backend.rental_viols.models import (
    Bow, Case, Image, ItemType, RentalContract, RentalHistory, RentalProgram, Viol, ViolSize,
    WaitingList
)
from vdgsa_backend.rental_viols.permissions import is_rental_manager


class ListCasesView(RentalViewBase, ListView):
    model = Case
    filterSessionName = 'case_filter'
    template_name = 'cases/list.html'
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
        context = super(ListCasesView, self).get_context_data(**kwargs)
        context['filter'] = self.getFilter()
        return context

    def get_queryset(self, *args: Any, **kwargs: Any):
        filter = self.getFilter()
        self.request.session[self.filterSessionName] = filter

        if filter['state'] == 'available':
            queryset = Case.objects.get_available()
        elif filter['state'] == 'retired':
            queryset = Case.objects.get_retired()
        elif filter['state'] == 'rented':
            queryset = Case.objects.get_rented()
        else:
            queryset = Case.objects.get_all()

        return queryset


class CaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CaseForm, self).__init__(*args, **kwargs)
        self.fields['vdgsa_number'].widget = HiddenInput()

    class Meta:
        model = Case
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


class AddCaseView(RentalViewBase, SuccessMessageMixin, CreateView):
    model = Case
    form_class = CaseForm
    initial = {
        'vdgsa_number': Case.objects.get_next_accessory_vdgsa_num,
        'accession_date': datetime.date.today}
    success_message = "%(size)s case was created successfully"
    template_name = 'cases/add.html'


class UpdateCaseView(RentalViewBase, SuccessMessageMixin, UpdateView):
    model = Case
    form_class = CaseForm
    template_name = 'cases/update.html'

    success_url = 'cases/'
    success_message = "%(size)s case was updated successfully"

    def get_success_url(self, **kwargs) -> str:
        return reverse('list-cases')


class CaseDetailView(RentalViewBase, DetailView):
    model = Case
    template_name = 'cases/detail.html'

    def get_context_data(self, **kwargs):
        context = super(CaseDetailView, self).get_context_data(**kwargs)
        context['images'] = Image.objects.get_images('case', context['case'].pk)
        return context


class AvailableCaseView(RentalViewBase, FormView):
    """Make Available"""
    template_name = 'viols/available.html'
    form_class = NotesOnlyHistoryForm
    model = RentalHistory

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        form = NotesOnlyHistoryForm(initial={'item': self.kwargs['pk']})
        context = self.get_context_data(**kwargs)
        context['form'] = form

        context['viol'] = Case.objects.get(pk=self.kwargs['pk'])
        return render(request, 'viols/available.html', context)

    def form_valid(self, form):
        case = Case.objects.get(pk=self.request.POST['pk'])
        case.status = RentalState.available
        case.save()
        history = RentalHistory.objects.create(
            case_num=case,
            event=RentalState.available,
            notes=form.cleaned_data['notes'])
        history.save()

        messages.add_message(self.request, messages.SUCCESS, 'Case Made Available!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('case-detail', args=[self.request.POST.get('pk')])


class RetireCaseView(RentalViewBase, FormView):
    """Retire Case"""
    template_name = './retireMulti.html'
    form_class = NotesOnlyHistoryForm
    model = RentalHistory

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        form = NotesOnlyHistoryForm(initial={'item': self.kwargs['pk']})
        context = self.get_context_data(**kwargs)
        context['item'] = Case.objects.get(pk=self.kwargs['pk'])
        context['form'] = form
        return render(request, self.template_name, context)

    def form_valid(self, form):
        item = Case.objects.get(pk=self.kwargs['pk'])
        item.status = RentalState.retired
        item.save()
        history = RentalHistory.objects.create(
            case_num=item,
            event=RentalEvent.retired,
            notes=form.cleaned_data['notes'])
        history.save()

        messages.add_message(self.request, messages.SUCCESS, 'Case Retired!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('case-detail', args=[self.kwargs['pk']])
