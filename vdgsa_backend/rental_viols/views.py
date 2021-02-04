from functools import cached_property
from typing import Any, Literal

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from django.urls.base import reverse
from django.utils.http import urlencode
from django.utils import timezone
from django.views.generic.base import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.generic.list import ListView

from vdgsa_backend.accounts.models import User
from vdgsa_backend.rental_viols.managers.InstrumentManager import AccessoryManager, ViolManager
from vdgsa_backend.rental_viols.managers.RentalActionsManager import RentalActionsManager
from vdgsa_backend.rental_viols.models import (
    Bow, Case, RentalEvent, RentalHistory, Viol, WaitingList
)
from vdgsa_backend.rental_viols.permissions import is_rental_manager


class RentalViewBase(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self) -> bool:
        return is_rental_manager(self.request.user)

    def reverse(*args, **kwargs):
        get = kwargs.pop('get', {})
        url = reverse(*args, **kwargs)
        if get:
            url += '?' + urlencode(get)
        return url


# Actions
# Attach to viol | Detach from viol - Bow, Case
# Retire | Un-retire - Bow, Case, Viol
# Rent out | Reserve | Renew rental | Return from rental | Make available (un-retire?) - Viol
# Add to waiting list | Cancel waiting list


class AttachToViolView(RentalViewBase, View):
    template_name = 'viols/attatchToViol.html'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        if self.request.method == 'GET' and 'viol_num' in self.request.GET:
            context['viol'] = Viol.objects.get(pk=viol_num)
            # Get List of available bows and cases
        else:
            if 'case_num' in self.request.GET:
                case_num = self.request.GET['case_num']
                if case_num is not None and case_num != '':
                    context['case'] = Case.objects.get(pk=case_num)
            if 'bow_num' in self.request.GET:
                bow_num = self.request.GET['bow_num']
                if bow_num is not None and bow_num != '':
                    context['bow'] = Bow.objects.get(pk=bow_num)

            # Get List of bachelor viols
            context['viols'] = Viol.objects.get_available

        return render(
            self.request,
            'viols/attatchToViol.html', context
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any):
        if self.request.POST.get('viol_num'):
            viol = Viol.objects.get(pk=self.request.POST['viol_num'])
            if self.request.POST.get('bow_num'):
                bow = Bow.objects.get(pk=self.request.POST['bow_num'])
                viol.bows.add(bow)
                history = RentalHistoryForm(
                    {"event": RentalEvent.attached, "viol_num": viol.viol_num, "bow_num": bow.bow_num})
                history.save()
                messages.add_message(self.request, messages.SUCCESS, 'Bow attached!')

            if self.request.POST.get('case_num'):
                case = Case.objects.get(pk=self.request.POST['case_num'])
                viol.cases.add(case)
                history = RentalHistoryForm(
                    {"event": RentalEvent.attached, "viol_num": viol.viol_num, "case_num": case.case_num})
                history.save()
                messages.add_message(self.request, messages.SUCCESS, 'Case attached!')

        return render(request, 'viols/attatchToViol.html')


class DetachFromViolView(RentalViewBase, View):
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        if self.request.GET.get('viol_num'):
            viol = Viol.objects.get(pk=self.request.GET['viol_num'])
            if self.request.GET.get('bow_num'):
                bow = Bow.objects.get(pk=self.request.GET['bow_num'])
                bow.viol_num = None
                bow.save()
                history = RentalHistoryForm(
                    {"event": RentalEvent.detached, "viol_num": viol.viol_num, "bow_num": bow.bow_num})
                history.save()
                messages.add_message(self.request, messages.SUCCESS, 'Bow attached!')

            if self.request.GET.get('case_num'):
                case = Case.objects.get(pk=self.request.GET['case_num'])
                case.viol_num = None
                case.save()
                history = RentalHistoryForm(
                    {"event": RentalEvent.detached, "viol_num": viol.viol_num, "case_num": case.case_num})
                history.save()
                messages.add_message(self.request, messages.SUCCESS, 'Case attached!')

        return render(request, 'viols/attatchToViol.html')


class RentalHomeView(RentalViewBase, TemplateView):
    template_name = 'home.html'

# Rental Actions = Rent Out | Reserve (waitingList) | Return | Renew


class RentOutView(RentalViewBase, View):
    """get to select Renter Post to submit"""

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        if self.request.GET.get('viol_num'):
            context['viol'] = Viol.objects.get(pk=viol_num)
            context['users'] = Viol.objects.get(pk=viol_num)

        return render(request, 'rental/rentOut.html')

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any):
        if self.request.POST.get('viol_num'):
            viol = Viol.objects.get(pk=self.request.POST['viol_num'])

        return render(request, 'rental/rentOut.html')


# LIST VIEWS


class ViolsMultiListView(RentalViewBase, ListView):
    template_name = 'viols/list.html'

    def get_queryset(self, *args: Any, **kwargs: Any):
        filter = self.request.GET.get('filter', 'available')
        if filter == 'available':
            queryset = Viol.objects.get_available()
        elif filter == 'rented':
            queryset = Viol.objects.get_rented()
        else:
            queryset = Viol.objects.all()
        return queryset


class ListBowsView(RentalViewBase, ListView):
    model = Bow
    template_name = 'bows/list_bows.html'


class ListCasesView(RentalViewBase, ListView):
    model = Case
    template_name = 'cases/list.html'


class ListRentersView(RentalViewBase, ListView):

    def get_queryset(self, *args: Any, **kwargs: Any):
        filter = self.request.GET.get('filter', 'available')
        if filter == 'available':
            queryset = RentalHistory.objects.all()
        elif filter == 'rented':
            queryset = RentalHistory.objects.all()
        else:
            queryset = RentalHistory.objects.all()
        return queryset

    template_name = 'renters/list.html'


class ListWaitingView(RentalViewBase, ListView):
    def get_queryset(self, *args: Any, **kwargs: Any):
        return WaitingList.objects.all()

    template_name = 'waitinglist.html'

# CRUD


class RentalHistoryForm(forms.ModelForm):
    class Meta:
        model = RentalHistory
        fields = [
            'entry_num',
            'viol_num',
            'bow_num',
            'case_num',
            'renter_num',
            'event',
            'notes',
            'rental_start',
            'rental_end',
            'contract_scan',
        ]


class BowForm(forms.ModelForm):
    class Meta:
        model = Bow
        fields = [
            'vdgsa_number',
            'maker',
            'size',
            'state',
            'value',
            'provenance',
            'description',
            'accession_date',
            'notes',
            'storer',
            'program',
        ]


class AddBowView(RentalViewBase, SuccessMessageMixin, CreateView):
    model = Bow
    form_class = BowForm
    success_message = "%(size)s bow was created successfully"
    template_name = 'bows/add_bow.html'


class UpdateBowView(RentalViewBase, SuccessMessageMixin, UpdateView):
    model = Bow
    form_class = BowForm
    template_name = 'bows/update.html'
    success_message = "%(size)s bow was created successfully"

    def get_success_url(self, **kwargs) -> str:
        print(self.object.bow_num)
        return reverse('list-bows')


class BowDetailView(RentalViewBase, DetailView):
    model = Bow
    template_name = 'bows/bow_detail.html'


class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = [
            'vdgsa_number',
            'maker',
            'size',
            'state',
            'value',
            'provenance',
            'description',
            'accession_date',
            'notes',
            'storer',
            'program',
        ]


class AddCaseView(RentalViewBase, SuccessMessageMixin, CreateView):
    model = Case
    form_class = CaseForm
    success_message = "%(size)s case was created successfully"
    template_name = 'cases/add.html'


class UpdateCaseView(RentalViewBase, SuccessMessageMixin, UpdateView):
    model = Case
    form_class = CaseForm
    template_name = 'cases/update.html'

    success_url = 'cases/'
    success_message = "%(size)s case was updated successfully"

    def get_success_url(self, **kwargs) -> str:
        print(self.object.case_num)
        return reverse('list-cases')


class CaseDetailView(RentalViewBase, DetailView):
    model = Case
    template_name = 'cases/detail.html'


class ViolForm(forms.ModelForm):
    class Meta:
        model = Viol
        fields = [
            'vdgsa_number',
            'maker',
            'size',
            'strings',
            'state',
            'value',
            'provenance',
            'description',
            'accession_date',
            'notes',
            'storer',
            'program',
            'renter',
        ]


class AddViolView(RentalViewBase, SuccessMessageMixin, CreateView):
    model = Viol
    form_class = ViolForm
    template_name = 'viols/add.html'
    success_message = "%(size)s viol was created successfully"


class UpdateViolView(RentalViewBase, SuccessMessageMixin, UpdateView):
    model = Viol
    form_class = ViolForm
    template_name = 'viols/update.html'
    success_message = "%(size)s viol was updated successfully"

    def get_success_url(self, **kwargs) -> str:
        print(self.object.viol_num)
        return reverse('list-viols')


class ViolDetailView(RentalViewBase, DetailView):
    model = Viol
    template_name = 'viols/detail.html'

    def get_context_data(self, **kwargs):
        context = super(ViolDetailView, self).get_context_data(**kwargs)
        print('context', context)
        context['now'] = timezone.now()
        return context
