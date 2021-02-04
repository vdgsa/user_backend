from typing import Any, Literal
from functools import cached_property
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import ModelForm
from django.shortcuts import render

from django.utils.http import urlencode

from django.shortcuts import redirect
from django.urls.base import reverse

from django.views.generic.base import View
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.base import TemplateView

from vdgsa_backend.accounts.models import User

from vdgsa_backend.rental_viols.models import Bow, Case, Viol
from vdgsa_backend.rental_viols.managers.InstrumentManager import InstrumentManager
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


class RentalHomeView(RentalViewBase, TemplateView):
    template_name = 'home.html'


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


class BowForm(ModelForm):
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


class AddBowView(RentalViewBase, CreateView):
    model = Bow
    form_class = BowForm

    template_name = 'bows/add_bow.html'


class UpdateBowView(RentalViewBase, UpdateView):
    model = Bow
    form_class = BowForm
    template_name = 'bows/update.html'

    def get_success_url(self, **kwargs) -> str:
        print(self.object.bow_num)
        return reverse('list-bows')


class ListBowsView(RentalViewBase, ListView):
    model = Bow
    template_name = 'bows/list_bows.html'


class BowDetailView(RentalViewBase, DetailView):
    model = Bow
    template_name = 'bows/bow_detail.html'


class CaseForm(ModelForm):
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


class AddCaseView(RentalViewBase, CreateView):
    model = Case
    form_class = CaseForm

    template_name = 'cases/add.html'


class UpdateCaseView(RentalViewBase, UpdateView):
    model = Case
    form_class = CaseForm
    template_name = 'cases/update.html'

    def get_success_url(self, **kwargs) -> str:
        print(self.object.case_num)
        return reverse('list-cases')


class ListCasesView(RentalViewBase, ListView):
    model = Case
    template_name = 'cases/list.html'


class CaseDetailView(RentalViewBase, DetailView):
    model = Case
    template_name = 'cases/detail.html'


class ViolForm(ModelForm):
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


class AddViolView(RentalViewBase, CreateView):
    model = Viol
    form_class = ViolForm
    template_name = 'viols/add.html'


class UpdateViolView(RentalViewBase, UpdateView):
    model = Viol
    form_class = ViolForm
    template_name = 'viols/update.html'

    def get_success_url(self, **kwargs) -> str:
        print(self.object.viol_num)
        return reverse('list-viols')


class ViolDetailView(RentalViewBase, DetailView):
    model = Viol
    template_name = 'viols/detail.html'


class ListRentersView(RentalViewBase, ListView):
    model = Viol
    template_name = 'renters/list.html'


class ListWaitingView(RentalViewBase, ListView):
    model = Viol
    template_name = 'waitinglist.html'
