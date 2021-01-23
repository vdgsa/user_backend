from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import ModelForm
from django.shortcuts import render
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView

from vdgsa_backend.rental_viols.models import Bow
from vdgsa_backend.rental_viols.permissions import is_rental_manager


class RentalViewBase(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self) -> bool:
        return is_rental_manager(self.request.user)


class BowForm(ModelForm):
    class Meta:
        model = Bow
        fields = [
            'vdgsa_number',
            'size',
            'value',
            'provenance',
            'description',
            'accession_date',
            'notes',
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
