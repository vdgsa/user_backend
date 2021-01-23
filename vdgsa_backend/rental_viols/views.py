from vdgsa_backend.rental_viols.permissions import is_rental_manager
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import ModelForm
from django.shortcuts import render
from django.views.generic.edit import CreateView

from vdgsa_backend.rental_viols.models import Bow


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


class AddBowView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Bow
    form_class = BowForm

    template_name = 'add_bow.html'

    def test_func(self) -> bool:
        return is_rental_manager(self.request.user)
