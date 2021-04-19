from __future__ import annotations

from typing import Any

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import widgets
from django.urls.base import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from vdgsa_backend.conclave_registration.models import (
    Class, ConclaveRegistrationConfig, Level, get_classes_by_period
)
from vdgsa_backend.conclave_registration.views.permissions import is_conclave_team


class ConclaveRegistrationConfigForm(forms.ModelForm):
    class Meta:
        model = ConclaveRegistrationConfig
        fields = [
            'year',
            'phase',
            'faculty_registration_password',
        ]

        labels = {
            'phase': 'Registration Phase',
        }

        widgets = {
            'phase': widgets.RadioSelect,
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


class _PassThroughField(forms.Field):
    pass


class ConclaveClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = [
            'name',
            'period',
            'level',
            'instructor',
            'description',
        ]

        widgets = {
            'description': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
        }

    # We don't want the field to process the "level" data in any way,
    # just pass it through to the underlying postgres array field.
    level = _PassThroughField(widget=widgets.CheckboxSelectMultiple(choices=Level.choices))

    def __init__(self, conclave_config_pk: int | None = None, **kwargs: Any):
        self.conclave_config_pk = conclave_config_pk
        super().__init__(**kwargs)
        if 'level' not in self.initial and self.instance is not None:
            self.initial['level'] = self.instance.level

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
