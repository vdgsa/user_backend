from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import ModelForm
from django.shortcuts import render
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.base import TemplateView

from vdgsa_backend.rental_viols.models import Bow, Case, Viol
from vdgsa_backend.rental_viols.permissions import is_rental_manager


class RentalViewBase(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self) -> bool:
        return is_rental_manager(self.request.user)


class RentalHomeView(RentalViewBase, TemplateView):
    template_name = 'rentals.html'


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


class ListViolsView(RentalViewBase, ListView):
    model = Viol
    template_name = 'viols/list.html'


class ViolDetailView(RentalViewBase, DetailView):
    model = Viol
    template_name = 'viols/detail.html'


class ListRentersView(RentalViewBase, ListView):
    model = Viol
    template_name = 'renters/list.html'


class ListWaitingView(RentalViewBase, ListView):
    model = Viol
    template_name = 'waitinglist.html'
