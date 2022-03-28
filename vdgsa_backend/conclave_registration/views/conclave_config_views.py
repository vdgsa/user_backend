from __future__ import annotations

import csv
import tempfile
from typing import Any

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models.query import QuerySet
from django.forms import widgets
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls.base import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.views.generic.base import View

from vdgsa_backend.conclave_registration.models import (
    Class, ConclaveRegistrationConfig, Period, RegistrationEntry, get_classes_by_period
)
from vdgsa_backend.conclave_registration.views.permissions import is_conclave_team


class ConclaveRegistrationConfigForm(forms.ModelForm):
    class Meta:
        model = ConclaveRegistrationConfig
        fields = [
            'year',
            'phase',
            'faculty_registration_password',
            'liability_release_text',
            'archival_video_release_text',
            'photo_release_text',

            'first_period_time_label',
            'second_period_time_label',
            'third_period_time_label',
            'fourth_period_time_label',

            'housing_form_top_markdown',
            'housing_form_pre_arrival_markdown',
            'arrival_date_options',
            'departure_date_options',
            'banquet_food_options',

            'tshirt_image_url',

            'regular_tuition',
            'part_time_tuition',
            'consort_coop_tuition',
            'seasoned_players_tuition',
            'non_playing_attendee_fee',
            'beginners_extra_class_fee',
            'consort_coop_one_extra_class_fee',
            'consort_coop_two_extra_classes_fee',
            'seasoned_players_extra_class_fee',
            'single_room_cost',
            'double_room_cost',
            'banquet_guest_fee',
            'tshirt_price',
            'late_registration_fee',
            'work_study_scholarship_amount',
            'housing_subsidy_amount',
            'canadian_discount_percent',
        ]

        labels = {
            'phase': 'Registration Phase',
            'housing_form_top_markdown': (
                'Text to display at the top of the housing form. Rendered as markdown'),
            'housing_form_pre_arrival_markdown': (
                'Text to display before the arrival/departure section of the housing form. '
                'Rendered as markdown'),
            'arrival_date_options': (
                'A list of allowed conclave arrival dates, each separated by a newline'),
            'departure_date_options': (
                'A list of allowed conclave arrival dates, each separated by a newline.'),
            'banquet_food_options': (
                'A list of banquet food options, each separated by a newline. '
                'Note that "Not Attending" is automatically added as a choice.'
            ),
        }

        widgets = {
            'phase': widgets.RadioSelect,
            'liability_release_text': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
            'archival_video_release_text': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
            'photo_release_text': widgets.Textarea(attrs={'rows': 5, 'cols': None}),

            'housing_form_top_markdown': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
            'arrival_date_options': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
            'departure_date_options': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
            'banquet_food_options': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
            'housing_form_pre_arrival_markdown': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
        }


class ListConclaveRegistrationConfigView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = ConclaveRegistrationConfig
    ordering = '-year'

    template_name = 'registration_config/config_list.html'

    def test_func(self) -> bool | None:
        return is_conclave_team(self.request.user)


class CreateConclaveRegistrationConfigView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = ConclaveRegistrationConfig
    fields = ['year']

    template_name = 'registration_config/create_conclave.html'
    success_url = reverse_lazy('list-conclaves')

    def test_func(self) -> bool | None:
        return is_conclave_team(self.request.user)


class ConclaveRegistrationConfigView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = ConclaveRegistrationConfig
    template_name = 'registration_config/conclave_detail.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['classes_by_period'] = get_classes_by_period(self.kwargs[self.pk_url_kwarg])
        return context

    def test_func(self) -> bool | None:
        return is_conclave_team(self.request.user)


class EditConclaveRegistrationConfigView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ConclaveRegistrationConfig
    form_class = ConclaveRegistrationConfigForm
    template_name = 'registration_config/edit_conclave.html'

    def get_success_url(self) -> str:
        return reverse('conclave-detail', kwargs={'pk': self.kwargs[self.pk_url_kwarg]})

    def test_func(self) -> bool | None:
        return is_conclave_team(self.request.user)


class ListRegistrationEntriesView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'registration_config/list_registration_entries.html'

    @cached_property
    def conclave_config(self) -> ConclaveRegistrationConfig:
        return get_object_or_404(ConclaveRegistrationConfig, pk=self.kwargs['conclave_config_pk'])

    def get_queryset(self) -> QuerySet[RegistrationEntry]:
        return self.conclave_config.registration_entries.order_by('user__last_name')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['conclave_config'] = self.conclave_config
        return context

    def test_func(self) -> bool | None:
        return is_conclave_team(self.request.user)


class _PassThroughField(forms.Field):
    pass


class ConclaveClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = [
            'period',
            'name',
            'instructor',
            'level',
            'offer_to_beginners',
            'description',
            'notes',
        ]

        labels = {'offer_to_beginners': 'Offer as Beginners+ Add-On Option'}

        widgets = {
            'description': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
            'notes': widgets.Textarea(attrs={'rows': 3, 'cols': None}),
        }

    def __init__(self, conclave_config_pk: int | None = None, **kwargs: Any):
        self.conclave_config_pk = conclave_config_pk
        super().__init__(**kwargs)

    def save(self, *args: Any, **kwargs: Any) -> Any:
        class_ = super().save(commit=False)
        if not hasattr(class_, 'conclave_config'):
            assert self.conclave_config_pk is not None, \
                'conclave_config_pk is required when creating a Class'
            class_.conclave_config = ConclaveRegistrationConfig.objects.get(
                pk=self.conclave_config_pk
            )
        class_.save()
        return class_


class CreateConclaveClassView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Class
    form_class = ConclaveClassForm
    template_name = 'registration_config/create_class.html'

    pk_url_kwarg = 'conclave_config_pk'

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs['conclave_config_pk'] = self.kwargs[self.pk_url_kwarg]
        return kwargs

    def get_success_url(self) -> str:
        return reverse('conclave-detail', kwargs={'pk': self.kwargs[self.pk_url_kwarg]})

    def test_func(self) -> bool | None:
        return is_conclave_team(self.request.user)


class EditConclaveClassView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Class
    form_class = ConclaveClassForm
    template_name = 'registration_config/edit_class.html'

    def get_success_url(self) -> str:
        assert hasattr(self, 'object')
        return reverse(
            'conclave-detail',
            kwargs={'pk': self.object.conclave_config_id}  # type: ignore
        )

    def test_func(self) -> bool | None:
        return is_conclave_team(self.request.user)


class DeleteConclaveClassView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Class

    def get_success_url(self) -> str:
        assert hasattr(self, 'object')
        return reverse(
            'conclave-detail',
            kwargs={'pk': self.object.conclave_config_id}  # type: ignore
        )

    def test_func(self) -> bool | None:
        return is_conclave_team(self.request.user)


class ConclaveClassCSVView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'registration_config/class_csv_upload.html'

    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
        return render(self.request, self.template_name)

    def post(self, *args: Any, **kwargs: Any) -> HttpResponse:
        file_ = self.request.FILES['class_csv']
        with tempfile.NamedTemporaryFile('w+', newline='') as f:
            for chunk in file_.chunks():
                f.write(chunk.decode(encoding='utf-8', errors='surrogateescape'))

            f.seek(0)

            reader = csv.DictReader(f)
            with transaction.atomic():
                self.conclave_config.classes.all().delete()
                for row in reader:
                    Class.objects.create(
                        conclave_config=self.conclave_config,
                        name=row['Title'].strip(),
                        period=Period(int(row['Period'])),
                        defaults={
                            'level': row['Level'],
                            'instructor': row['Teacher'],
                            'description': row['Description'],
                            'notes': row['Notes'],
                        }
                    )

        return HttpResponseRedirect(
            reverse('conclave-detail', kwargs={'pk': self.conclave_config.pk})
        )

    @cached_property
    def conclave_config(self) -> ConclaveRegistrationConfig:
        return get_object_or_404(ConclaveRegistrationConfig, pk=self.kwargs['conclave_config_pk'])

    def test_func(self) -> bool | None:
        return is_conclave_team(self.request.user)
