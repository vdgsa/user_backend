from __future__ import annotations

import itertools
from abc import abstractmethod
from itertools import chain
from typing import Any, Dict, Final, Type, cast

import stripe  # type: ignore
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models.base import Model
from django.forms import widgets
from django.forms.fields import ChoiceField
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls.base import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin

from vdgsa_backend.accounts.models import User
from vdgsa_backend.accounts.views.utils import get_ajax_form_response
from vdgsa_backend.conclave_registration.models import (
    ADVANCED_PROGRAMS, NO_CLASS_PROGRAMS, BasicRegistrationInfo, Class, Clef,
    ConclaveRegistrationConfig, InstrumentBringing, PaymentInfo, Period, Program, RegistrationEntry,
    RegistrationPhase, RegularProgramClassChoices, TShirts, WorkStudyApplication, WorkStudyJob,
    YesNo, YesNoMaybe, get_classes_by_period
)
from vdgsa_backend.conclave_registration.templatetags.conclave_tags import get_current_conclave

from .permissions import is_conclave_team


@login_required
def current_year_conclave_redirect_view(request: HttpRequest) -> HttpResponse:
    conclave_config = get_current_conclave()
    if conclave_config is None:
        return HttpResponse(404)

    return HttpResponseRedirect(
        reverse('conclave-reg-landing', kwargs={'conclave_config_pk': conclave_config.pk})
    )


class ChooseProgramForm(forms.Form):
    program = forms.TypedChoiceField(
        coerce=Program,
        choices=[('', '--- Select a Program ---')] + Program.choices,
        label='',
    )
    faculty_registration_password = forms.CharField(
        required=False, widget=widgets.PasswordInput, label='Password'
    )

    def __init__(self, conclave_config: ConclaveRegistrationConfig, *args: Any, **kwargs: Any):
        self.conclave_config = conclave_config
        super().__init__(*args, **kwargs)

    def clean(self) -> Dict[str, Any]:
        result = super().clean()
        if self.cleaned_data['program'] == Program.faculty_guest_other:
            password = self.cleaned_data.get('faculty_registration_password', '')
            if password != self.conclave_config.faculty_registration_password:
                raise ValidationError({'faculty_registration_password': 'Invalid password'})

        return result


class ConclaveRegistrationLandingPage(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'registration/landing_page.html'

    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
        registration_entry_query = RegistrationEntry.objects.filter(
            conclave_config=self.conclave_config, user=cast(User, self.request.user)
        )
        if registration_entry_query.exists():
            registration_entry = registration_entry_query.get()
            return HttpResponseRedirect(
                reverse(get_first_step_url_name(registration_entry),
                        kwargs={'conclave_reg_pk': registration_entry.pk})
            )

        return self._render_page(ChooseProgramForm(self.conclave_config))

    def post(self, *args: Any, **kwargs: Any) -> HttpResponse:
        if 'user_pk' in self.request.POST:
            requested_user = get_object_or_404(User, pk=self.request.POST['user_pk'])
            if requested_user != self.request.user and not is_conclave_team(self.request.user):
                raise PermissionDenied
        else:
            requested_user = cast(User, self.request.user)

        form = ChooseProgramForm(self.conclave_config, self.request.POST)
        if not form.is_valid():
            return self._render_page(form)

        registration_entry = RegistrationEntry.objects.create(
            conclave_config=self.conclave_config,
            user=requested_user,
            program=form.cleaned_data['program'],
            is_late=self.conclave_config.phase == RegistrationPhase.late
        )
        return HttpResponseRedirect(
            reverse(
                get_first_step_url_name(registration_entry),
                kwargs={'conclave_reg_pk': registration_entry.pk}
            )
        )

    def test_func(self) -> bool:
        if is_conclave_team(self.request.user):
            return True

        if self.request.method == 'GET':
            return self.conclave_config.phase != RegistrationPhase.unpublished

        return self.conclave_config.phase in [RegistrationPhase.open, RegistrationPhase.late]

    @cached_property
    def conclave_config(self) -> ConclaveRegistrationConfig:
        return get_object_or_404(ConclaveRegistrationConfig, pk=self.kwargs['conclave_config_pk'])

    def _render_page(self, form: ChooseProgramForm) -> HttpResponse:
        return render(
            self.request,
            self.template_name,
            {
                'choose_program_form': form,
                'conclave_config': self.conclave_config
            }
        )


def get_first_step_url_name(registration_entry: RegistrationEntry) -> str:
    if registration_entry.program in NO_CLASS_PROGRAMS:
        return 'conclave-basic-info'

    return 'conclave-instruments-bringing'


class _RegistrationStepFormBase:
    """
    Base class to provide some common initialization for our forms
    corresponding to registration steps (e.g., basic info, class selection).
    """
    def __init__(self, registration_entry: RegistrationEntry, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)  # type: ignore
        self.registration_entry = registration_entry

    def save(self, commit: bool = True) -> Any:
        obj = super().save(commit=False)  # type: ignore
        obj.registration_entry = self.registration_entry
        if commit:
            obj.save()

        return obj


class _RegistrationStepViewBase(LoginRequiredMixin, UserPassesTestMixin, SingleObjectMixin, View):
    model = RegistrationEntry
    pk_url_kwarg = 'conclave_reg_pk'
    template_name: str | None = None

    # The form class to use in the "get" and "post" implementations.
    # Derived classes must specify this.
    form_class: Type[_RegistrationStepFormBase] | None = None

    # The url name for the next step in the registration flow.
    # Derived classes can also override the "get_next_step_url" method
    # for customizable behavior (e.g., for when different registration
    # programs have different steps).
    next_step_url_name: str | None = None

    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
        assert self.form_class is not None, 'You must provide a value for "form_class"'
        return self.render_page(
            self.form_class(self.registration_entry, instance=self.get_step_instance())
        )

    def post(self, *args: Any, **kwargs: Any) -> HttpResponse:
        form = self.get_form()
        if not form.is_valid():
            return self.render_page(form)

        form.save()
        return HttpResponseRedirect(self.get_next_step_url())

    def get_form(self) -> _RegistrationStepFormBase:
        assert self.form_class is not None, 'You must provide a value for "form_class"'
        return self.form_class(
            self.registration_entry, self.request.POST, instance=self.get_step_instance())

    @abstractmethod
    def get_step_instance(self) -> Model | None:
        """
        Returns the object instance for this step for the current registration entry,
        or None if no object exists.
        """
        raise NotImplementedError

    @cached_property
    def registration_entry(self) -> RegistrationEntry:
        return cast(RegistrationEntry, self.get_object())

    def render_page(
        self,
        form: _RegistrationStepFormBase | None,
        extra_context: dict[str, object] | None = None,
    ) -> HttpResponse:
        context = self.get_render_context(form)
        if extra_context is not None:
            context.update(extra_context)

        assert self.template_name is not None, 'You must provide a value for "template_name"'
        return render(self.request, self.template_name, context)

    def get_render_context(self, form: _RegistrationStepFormBase | None) -> dict[str, object]:
        return {
            'form': form,
            'next_step_url': self.get_next_step_url(),
            'registration_entry': self.registration_entry,
        }

    def get_next_step_url(self) -> str:
        return reverse(
            self.next_step_url_name,
            kwargs={'conclave_reg_pk': self.registration_entry.pk}
        )

    def test_func(self) -> bool:
        if is_conclave_team(self.request.user):
            return True

        if self.request.user != self.registration_entry.user:
            return False

        if self.request.method == 'GET':
            return self.registration_entry.conclave_config.phase != RegistrationPhase.unpublished

        return (
            self.registration_entry.conclave_config.phase
            in [RegistrationPhase.open, RegistrationPhase.late]
        )


# class BooleanRadioField(forms.BooleanField):
#     def __init__(
#         self,
#         true_label: str = 'Yes',
#         false_label: str = 'No',
#         **kwargs: Any
#     ) -> None:
#         kwargs['widget'] = forms.RadioSelect(choices=((True, true_label), (False, false_label)))
#         super().__init__(**kwargs)


class YesNoRadioField(forms.ChoiceField):
    def __init__(
        self,
        yes_label: str = YesNo.yes.label,
        no_label: str = YesNo.no.label,
        widget: widgets.Widget | Type[widgets.Widget] | None = forms.RadioSelect,
        **kwargs: Any
    ) -> None:
        kwargs['choices'] = ((YesNo.yes, yes_label), (YesNo.no, no_label))
        super().__init__(widget=widget, **kwargs)


class YesNoMaybeRadioField(forms.ChoiceField):
    def __init__(
        self,
        widget: widgets.Widget | Type[widgets.Widget] | None = forms.RadioSelect,
        **kwargs: Any
    ) -> None:
        kwargs['choices'] = YesNoMaybe.choices
        super().__init__(widget=widget, **kwargs)


class BasicInfoForm(_RegistrationStepFormBase, forms.ModelForm):
    class Meta:
        model = BasicRegistrationInfo
        fields = [
            'is_first_time_attendee',
            'buddy_willingness',
            # 'willing_to_help_with_small_jobs',
            'wants_display_space',
            'photo_release_auth',
            # 'liability_release',
            'other_info',
        ]

        widgets = {
            'other_info': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
        }

        labels = {
            'is_first_time_attendee': '',
            'buddy_willingness': '',
            'wants_display_space': '',
            'photo_release_auth': '',
            'other_info': '',
        }

    is_first_time_attendee = YesNoRadioField(label='')
    buddy_willingness = YesNoMaybeRadioField(label='', required=False)
    photo_release_auth = YesNoRadioField(
        yes_label='I agree',
        no_label="I don't agree",
        label='',
    )
    wants_display_space = YesNoRadioField(label='')

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        # self.fields['liability_release'].required = True


class BasicInfoView(_RegistrationStepViewBase):
    template_name = 'registration/basic_info.html'
    form_class = BasicInfoForm

    @property
    def next_step_url_name(self) -> str:  # type: ignore
        if self.registration_entry.program in NO_CLASS_PROGRAMS:
            return 'conclave-tshirts'

        return 'conclave-work-study'

    def get_step_instance(self) -> BasicRegistrationInfo | None:
        if hasattr(self.registration_entry, 'basic_info'):
            return self.registration_entry.basic_info

        return None


# A dummy field that won't modify the values passed through it to/from
# whatever widget we specify.
class _PassThroughField(forms.Field):
    pass


class WorkStudyForm(_RegistrationStepFormBase, forms.ModelForm):
    class Meta:
        model = WorkStudyApplication
        fields = [
            'nickname_and_pronouns',
            'phone_number',
            'can_receive_texts_at_phone_number',
            'home_timezone',
            'other_timezone',
            'has_been_to_conclave',
            'has_done_work_study',
            'student_info',
            'job_preferences',
            'relevant_job_experience',
            'other_skills',
            'other_info',
        ]

        widgets = {
            'student_info': widgets.Textarea(attrs={'rows': 3, 'cols': None}),
            'relevant_job_experience': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
            'other_skills': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
            'other_info': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
        }

        labels = dict(zip(fields, itertools.repeat('')))

    can_receive_texts_at_phone_number = YesNoRadioField(label='')

    has_been_to_conclave = YesNoRadioField(label='')
    has_done_work_study = YesNoRadioField(label='')

    home_timezone = ChoiceField(
        choices=(
            ('EDT', 'EDT (Eastern Daylight Time) UTC/GMT -4 hours -- '
                    'this is CONCLAVE OFFICIAL TIME'),
            ('CDT', 'CDT (Central)'),
            ('MDT', 'MDT (Mountain)'),
            ('PDT', 'PDT (Pacific Daylight Time) UTC/GMT -7 hours -- this is where Koren, '
                    'the work-study coordinator, lives!'),
            ('other', 'Other'),
        ),
        widget=widgets.RadioSelect
    )

    job_preferences = _PassThroughField(
        widget=widgets.CheckboxSelectMultiple(choices=WorkStudyJob.choices),
        label=''
    )


class WorkStudyApplicationView(_RegistrationStepViewBase):
    template_name = 'registration/work_study.html'
    form_class = WorkStudyForm
    next_step_url_name = 'conclave-tshirts'

    def get_step_instance(self) -> WorkStudyApplication | None:
        if hasattr(self.registration_entry, 'work_study'):
            return self.registration_entry.work_study

        return None


class InstrumentBringingForm(_RegistrationStepFormBase, forms.ModelForm):
    class Meta:
        model = InstrumentBringing
        fields = [
            'size',
            'name_if_other',
            'level',
            'clefs',
        ]

        labels = {
            'level': 'My level on this instrument',
        }

    # We don't want the field to process the "clefs" data in any way,
    # just pass it through to the underlying postgres array field.
    clefs = _PassThroughField(
        widget=widgets.CheckboxSelectMultiple(choices=Clef.choices),
        label='Clefs I read on this instrument'
    )

    def __init__(self, registration_entry: RegistrationEntry, *args: Any, **kwargs: Any):
        super().__init__(registration_entry, *args, **kwargs)
        if 'clefs' not in self.initial and self.instance is not None:
            self.initial['clefs'] = self.instance.clefs


class InstrumentsBringingView(_RegistrationStepViewBase):
    template_name = 'registration/instruments/instruments_bringing.html'
    form_class = InstrumentBringingForm
    next_step_url_name = 'conclave-class-selection'

    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
        return self.render_page(InstrumentBringingForm(self.registration_entry))

    def post(self, *args: Any, **kwargs: Any) -> HttpResponse:
        form = InstrumentBringingForm(self.registration_entry, self.request.POST)
        if not form.is_valid():
            return get_ajax_form_response(
                'form_validation_error',
                form,
                form_template='registration/instruments/add_instrument_form_body.tmpl'
            )

        instrument = form.save()
        return get_ajax_form_response(
            'success',
            None,
            form_context={'instrument': instrument},
            form_template='registration/instruments/instrument.tmpl'
        )

    def get_render_context(self, form: _RegistrationStepFormBase) -> dict[str, object]:
        context = super().get_render_context(form)
        context['instruments'] = self.registration_entry.instruments_bringing.all()
        return context


class DeleteInstrumentView(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, *args: Any, **kwargs: Any) -> HttpResponse:
        self.instrument.delete()
        return HttpResponse(status=204)

    @cached_property
    def instrument(self) -> InstrumentBringing:
        return get_object_or_404(InstrumentBringing, pk=self.kwargs['pk'])

    def test_func(self) -> bool:
        if is_conclave_team(self.request.user):
            return True

        if self.request.user != self.instrument.registration_entry.user:
            return False

        return (
            self.instrument.registration_entry.conclave_config.phase
            in [RegistrationPhase.open, RegistrationPhase.late]
        )


_CLASS_CHOICE_FIELD_NAMES_BY_PERIOD: Final = {
    Period.first: ['period1_choice1', 'period1_choice2', 'period1_choice3'],
    Period.second: ['period2_choice1', 'period2_choice2', 'period2_choice3'],
    Period.third: ['period3_choice1', 'period3_choice2', 'period3_choice3'],
    Period.fourth: ['period4_choice1', 'period4_choice2', 'period4_choice3'],
}

_INSTRUMENT_FIELD_NAMES_BY_PERIOD: Final = {
    Period.first: [
        'period1_choice1_instrument', 'period1_choice2_instrument', 'period1_choice3_instrument'],
    Period.second: [
        'period2_choice1_instrument', 'period2_choice2_instrument', 'period2_choice3_instrument'],
    Period.third: [
        'period3_choice1_instrument', 'period3_choice2_instrument', 'period3_choice3_instrument'],
    Period.fourth: [
        'period4_choice1_instrument', 'period4_choice2_instrument', 'period4_choice3_instrument'],
}


class RegularProgramClassSelectionForm(_RegistrationStepFormBase, forms.ModelForm):
    class Meta:
        model = RegularProgramClassChoices
        # Interleave the class choice and instrument choice field names
        # i.e., ['period1_choice1', 'period1_choice1_instrument',
        #        'period1_choice2', 'period1_choice2_instrument']
        fields = list(
            chain.from_iterable(
                zip(
                    chain.from_iterable(_CLASS_CHOICE_FIELD_NAMES_BY_PERIOD.values()),
                    chain.from_iterable(_INSTRUMENT_FIELD_NAMES_BY_PERIOD.values()),
                )
            )
        ) + ['comments']

        widgets = {
            'comments': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
        }

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        for period, field_names in _CLASS_CHOICE_FIELD_NAMES_BY_PERIOD.items():
            for field_name in field_names:
                self.fields[field_name].queryset = Class.objects.filter(
                    conclave_config=self.registration_entry.conclave_config,
                    period=period
                )
                self.fields[field_name].empty_label = 'No class'

        for field_name in chain.from_iterable(_INSTRUMENT_FIELD_NAMES_BY_PERIOD.values()):
            self.fields[field_name].queryset = InstrumentBringing.objects.filter(
                registration_entry=self.registration_entry
            )
            self.fields[field_name].empty_label = 'Any I listed'

    def full_clean(self) -> None:
        super().full_clean()

        # if self.instance.num_classes_selected < self.min_num_classes:
        #     raise ValidationError(
        #         'Please specify your class preferences '
        #         f'for at least {self.min_num_classes} period(s).'
        #     )

        if self.instance.num_classes_selected > self.max_num_classes:
            self.add_error(
                None,
                'Please specify your class preferences '
                f'for no more than {self.max_num_classes} period(s).'
            )

    # @property
    # def min_num_classes(self) -> int:
    #     return 0

    @property
    def max_num_classes(self) -> int:
        program = self.registration_entry.program
        if program == Program.beginners:
            return 1

        if program in ADVANCED_PROGRAMS:
            return 2

        return 4


class RegularProgramClassSelectionView(_RegistrationStepViewBase):
    template_name = 'registration/regular_class_selection.html'
    form_class = RegularProgramClassSelectionForm
    next_step_url_name = 'conclave-basic-info'

    def get_step_instance(self) -> RegularProgramClassChoices | None:
        if hasattr(self.registration_entry, 'regular_class_choices'):
            return self.registration_entry.regular_class_choices

        return None

    def get_render_context(self, form: _RegistrationStepFormBase) -> dict[str, object]:
        context = super().get_render_context(form)
        context['classes_by_period'] = get_classes_by_period(
            self.registration_entry.conclave_config_id)
        return context


class TShirtsForm(_RegistrationStepFormBase, forms.ModelForm):
    class Meta:
        fields = ['tshirt1', 'tshirt2', 'donation']
        model = TShirts

    donation = forms.IntegerField(required=False, min_value=0)

    def __init__(self, registration_entry: RegistrationEntry, *args: Any, **kwargs: Any):
        super().__init__(registration_entry, *args, **kwargs)
        self.fields['tshirt1'].label = 'T-Shirt 1'
        self.fields['tshirt2'].label = 'T-Shirt 2'

    def clean(self) -> Dict[str, Any]:
        data = super().clean()
        if data['donation'] is None:
            data['donation'] = 0
        return data


class TShirtsView(_RegistrationStepViewBase):
    template_name = 'registration/tshirts.html'
    form_class = TShirtsForm
    next_step_url_name = 'conclave-payment'

    def get_step_instance(self) -> RegularProgramClassChoices | None:
        if hasattr(self.registration_entry, 'tshirts'):
            return self.registration_entry.tshirts

        return None


def _generate_credit_card_years() -> list[str]:
    now_year = timezone.now().year
    return [str(now_year + i) for i in range(20)]


_MONTHS: Final = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
_YEARS: Final = _generate_credit_card_years()


def _credit_card_number_validator(card_number: str) -> None:
    for digit in card_number:
        if not digit.isdigit():
            raise ValidationError('Invalid card number')


class PaymentForm(_RegistrationStepFormBase, forms.ModelForm):
    class Meta:
        model = PaymentInfo
        fields = []

    name_on_card = forms.CharField()
    card_number = forms.CharField(
        min_length=16, max_length=16, validators=[_credit_card_number_validator]
    )
    expiration_month = forms.ChoiceField(choices=list(zip(_MONTHS, _MONTHS)))
    expiration_year = forms.ChoiceField(choices=list(zip(_YEARS, _YEARS)))
    cvc = forms.CharField(min_length=3, max_length=3)


class PaymentView(_RegistrationStepViewBase):
    template_name = 'registration/payment/payment.html'
    form_class = PaymentForm
    next_step_url_name = 'conclave-done'

    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
        return self.render_page(PaymentForm(self.registration_entry))

    def post(self, *args: Any, **kwargs: Any) -> HttpResponse:
        form = self.get_form()
        if not form.is_valid():
            return self.render_page(form)

        payment_info = form.save(commit=False)

        if self._get_missing_sections():
            return self.render_page(form)

        try:
            payment_method = stripe.PaymentMethod.create(
                type='card',
                card={
                    'number': form.cleaned_data['card_number'],
                    'exp_month': form.cleaned_data['expiration_month'],
                    'exp_year': form.cleaned_data['expiration_year'],
                    'cvc': form.cleaned_data['cvc'],
                },
                billing_details={
                    'name': form.cleaned_data['name_on_card']
                }
            )
        except stripe.error.CardError as e:
            return self.render_page(form, {'stripe_error': e.user_message})

        payment_info.stripe_payment_method_id = payment_method.id
        payment_info.save()

        return HttpResponseRedirect(self.get_next_step_url())

    def get_step_instance(self) -> PaymentInfo | None:
        if hasattr(self.registration_entry, 'payment_info'):
            return self.registration_entry.payment_info

        return None

    def get_render_context(self, form: _RegistrationStepFormBase | None) -> dict[str, object]:
        context = super().get_render_context(form)
        context['missing_sections'] = self._get_missing_sections()
        context['class_selection_required'] = self.registration_entry.class_selection_is_required
        return context

    def _get_missing_sections(self) -> list[str]:
        missing_sections = []

        if not hasattr(self.registration_entry, 'basic_info'):
            missing_sections.append('Additional Info')

        if (self.registration_entry.class_selection_is_required
                and not hasattr(self.registration_entry, 'regular_class_choices')):
            missing_sections.append('Classes')

        return missing_sections


class StartOverView(_RegistrationStepViewBase):
    template_name = 'registration/start_over.html'

    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
        return self.render_page(None)

    def post(self, *args: Any, **kwargs: Any) -> HttpResponse:
        redirect_url = self.get_next_step_url()
        self.registration_entry.delete()
        return HttpResponseRedirect(redirect_url)

    def get_next_step_url(self) -> str:
        return reverse(
            'conclave-reg-landing',
            kwargs={'conclave_config_pk': self.registration_entry.conclave_config.pk}
        )


class RegistrationDoneView(View):
    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
        return render(self.request, 'registration/done.html')
