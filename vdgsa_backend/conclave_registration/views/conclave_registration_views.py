from __future__ import annotations

import itertools
from abc import abstractmethod
from datetime import datetime
from itertools import chain
from typing import Any, Dict, Final, Iterable, List, Type, cast

import stripe  # type: ignore
from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.mail import send_mail
from django.db.models.base import Model
from django.forms import widgets
from django.forms.fields import BooleanField, IntegerField
from django.forms.utils import ErrorDict
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls.base import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin

from vdgsa_backend.accounts.models import User
from vdgsa_backend.accounts.views.utils import get_ajax_form_response
from vdgsa_backend.conclave_registration.models import (
    BEGINNER_PROGRAMS, NO_CLASS_PROGRAMS, NOT_ATTENDING_BANQUET_SENTINEL,
    AdditionalRegistrationInfo, AdvancedProjectsInfo, AdvancedProjectsParticipationOptions,
    BeginnerInstrumentInfo, Class, Clef, ConclaveRegistrationConfig, DietaryNeeds, Housing,
    HousingRoomType, InstrumentBringing, InstrumentPurpose, PaymentInfo, Period, Program,
    RegistrationEntry, RegistrationPhase, RegularProgramClassChoices, SelfRatingInfo, TShirts,
    WorkStudyApplication, WorkStudyJob, YesNo, YesNoMaybe, get_classes_by_period
)
from vdgsa_backend.conclave_registration.summary_and_charges import (
    get_charges_summary, get_registration_summary
)
from vdgsa_backend.conclave_registration.templatetags.conclave_tags import (
    PERIOD_STRS, format_period_long, get_current_conclave
)
from vdgsa_backend.templatetags.filters import show_name, show_name_and_email

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
                'conclave_config': self.conclave_config,
                'membership_valid_through_conclave': self.membership_valid_through_conclave,
            }
        )

    @property
    def membership_valid_through_conclave(self) -> bool:
        # Avoid throwing an exception before departure_dates have been set
        if not self.conclave_config.departure_dates:
            last_day = timezone.now().replace(
                year=self.conclave_config.year,
                month=9,
                day=1,
            )
        else:
            last_day = datetime.combine(
                self.conclave_config.departure_dates[-1].replace(year=self.conclave_config.year),
                timezone.now().time(),
                timezone.now().tzinfo
            )
        return self.request.user.subscription_is_valid_until(last_day)


def get_first_step_url_name(registration_entry: RegistrationEntry) -> str:
    if registration_entry.program in NO_CLASS_PROGRAMS:
        return 'conclave-basic-info'

    if registration_entry.program in BEGINNER_PROGRAMS:
        return 'conclave-instruments-bringing'

    return 'conclave-self-rating'


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
        if not form.is_valid():  # type: ignore
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


class AdditionalInfoForm(_RegistrationStepFormBase, forms.ModelForm):
    class Meta:
        model = AdditionalRegistrationInfo
        fields = [
            'nickname',
            'phone',
            'age',
            'gender',
            'pronouns',
            'include_in_whos_coming_to_conclave_list',
            'attended_conclave_before',
            'buddy_willingness',
            # 'willing_to_help_with_small_jobs',
            'wants_display_space',
            'num_display_space_days',
            'liability_release',
            'covid_policy',
            'photo_release_auth',
            'other_info',
        ]

        widgets = {
            'other_info': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
        }

        labels = {
            'nickname': '',
            'phone': '',
            'include_in_whos_coming_to_conclave_list': '',
            'attended_conclave_before': '',
            'buddy_willingness': '',
            'wants_display_space': '',
            'num_display_space_days': '',
            'photo_release_auth': '',
            'other_info': '',
        }

    do_not_send_text_updates = BooleanField(required=False, label='I would like to opt-out of text reminders')
    include_in_whos_coming_to_conclave_list = YesNoRadioField(label='')
    attended_conclave_before = YesNoRadioField(
        label='', no_label='No, this is my first Conclave!')
    buddy_willingness = YesNoMaybeRadioField(label='', required=False)
    can_drive_loaners = YesNoMaybeRadioField(label='', required=False)
    liability_release = BooleanField(required=True, label='I agree')
    covid_policy = BooleanField(required=True, label='I agree')
    photo_release_auth = YesNoRadioField(
        yes_label='I allow',
        no_label="I don't allow",
        label='',
    )
    wants_display_space = YesNoRadioField(label='')

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        # self.fields['liability_release'].required = True


class AdditionalInfoView(_RegistrationStepViewBase):
    template_name = 'registration/additional_info.html'
    form_class = AdditionalInfoForm

    @property
    def next_step_url_name(self) -> str:  # type: ignore
        if self.registration_entry.program in NO_CLASS_PROGRAMS:
            return 'conclave-housing'

        return 'conclave-work-study'

    def get_step_instance(self) -> AdditionalRegistrationInfo | None:
        if hasattr(self.registration_entry, 'additional_info'):
            return self.registration_entry.additional_info

        return None


# A dummy field that won't modify the values passed through it to/from
# whatever widget we specify.
class _PassThroughField(forms.Field):
    pass


class WorkStudyForm(_RegistrationStepFormBase, forms.ModelForm):
    class Meta:
        model = WorkStudyApplication
        fields = [
            'wants_work_study',
            'phone_number',
            'can_receive_texts_at_phone_number',
            'has_been_to_conclave',
            'has_done_work_study',
            'student_info',
            'can_arrive_before_first_meeting',
            'early_arrival',
            'can_stay_until_sunday_afternoon',
            'other_travel_info',
            'job_preferences',
            'other_jobs',
            'has_car',
            'relevant_job_experience',
            'other_skills',
            'other_info',
        ]

        widgets = {
            'student_info': widgets.Textarea(attrs={'rows': 3, 'cols': None}),
            'early_arrival': widgets.RadioSelect(),
            'other_jobs': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
            'relevant_job_experience': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
            'other_skills': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
            'other_info': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
            'has_been_to_conclave': widgets.RadioSelect(),
            'has_done_work_study': widgets.RadioSelect(),
            'can_arrive_before_first_meeting': widgets.RadioSelect(),
            'other_travel_info': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
        }

        labels = dict(zip(fields, itertools.repeat('')))

    wants_work_study = YesNoRadioField(label='')

    can_receive_texts_at_phone_number = YesNoRadioField(label='')

    can_stay_until_sunday_afternoon = YesNoRadioField(label='')

    job_preferences = _PassThroughField(
        widget=widgets.CheckboxSelectMultiple(choices=WorkStudyJob.choices),
        label=''
    )
    has_car = YesNoMaybeRadioField(label='')

    def full_clean(self) -> None:
        # If the user doesn't want to apply for work study, don't perform
        # any other validation.
        if self.data.get('wants_work_study', '') == YesNo.no:
            self.cleaned_data = {'wants_work_study': YesNo.no}
            self._errors = ErrorDict()
            # _post_clean() sets attributes on the model instance.
            self._post_clean()  # type: ignore
        else:
            super().full_clean()


class WorkStudyApplicationView(_RegistrationStepViewBase):
    template_name = 'registration/work_study.html'
    form_class = WorkStudyForm
    next_step_url_name = 'conclave-housing'

    def get_step_instance(self) -> WorkStudyApplication | None:
        if hasattr(self.registration_entry, 'work_study'):
            return self.registration_entry.work_study

        return None



class SelfRatingInfoForm(_RegistrationStepFormBase, forms.ModelForm):
    class Meta:
        model = SelfRatingInfo
        fields = [
            'level',
        ]

        labels = {
            'level': 'My overall level is:',
        }


class SelfRatingInfoInfoView(_RegistrationStepViewBase):
    template_name = 'registration/self_rating.html'
    form_class = SelfRatingInfoForm

    @property
    def next_step_url_name(self) -> str:  # type: ignore
        return 'conclave-instruments-bringing'

    def get_step_instance(self) -> SelfRatingInfo | None:
        if hasattr(self.registration_entry, 'self_rating'):
            return self.registration_entry.self_rating

        return None


class InstrumentBringingForm(_RegistrationStepFormBase, forms.ModelForm):
    class Meta:
        model = InstrumentBringing
        fields = [
            'size',
            'name_if_other',
            'purpose',
            'relative_level',
            'clefs',
            'comments',
        ]

        labels = {
            'purpose': 'Are you bringing this instrument for yourself, '
                       'willing to lend it, or needing to borrow it?',
            'relative_level': 'I play this instrument:',
            'comments': 'Comments (e.g., "I can lend this instrument during 1st period only")',
            'name_if_other': 'Please specify instrument size/type'
        }

        widgets = {
            'comments': widgets.Textarea(attrs={'rows': 3, 'cols': None}),
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


class BeginnerInstrumentsForm(_RegistrationStepFormBase, forms.ModelForm):
    class Meta:
        model = BeginnerInstrumentInfo
        fields = [
            'needs_instrument',
            'instrument_bringing',
        ]

        labels = {
            'instrument_bringing': ''
        }

    needs_instrument = YesNoRadioField(
        yes_label='Yes, I need help getting an instrument',
        no_label='No, I will be bringing an instrument',
        label='',
    )


class InstrumentsBringingView(_RegistrationStepViewBase):
    @property
    def template_name(self) -> str:  # type: ignore
        if self.registration_entry.program in BEGINNER_PROGRAMS:
            return 'registration/instruments/beginner_instruments.html'

        return 'registration/instruments/instruments_bringing.html'

    @property
    def form_class(self) -> Type[_RegistrationStepFormBase]:  # type: ignore
        if self.registration_entry.program in BEGINNER_PROGRAMS:
            return BeginnerInstrumentsForm

        return InstrumentBringingForm

    next_step_url_name = 'conclave-class-selection'

    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
        if self.registration_entry.program in BEGINNER_PROGRAMS:
            return super().get(*args, **kwargs)

        return self.render_page(self.form_class(self.registration_entry))

    def post(self, *args: Any, **kwargs: Any) -> HttpResponse:
        if self.registration_entry.program in BEGINNER_PROGRAMS:
            return super().post(*args, **kwargs)

        form = self.form_class(self.registration_entry, self.request.POST)
        if not form.is_valid():  # type: ignore
            return get_ajax_form_response(
                'form_validation_error',
                form,  # type: ignore
                form_template='registration/instruments/add_instrument_form_body.tmpl'
            )

        instrument = form.save()
        return get_ajax_form_response(
            'success',
            None,
            form_context={'instrument': instrument},
            form_template='registration/instruments/instrument.tmpl'
        )

    def get_render_context(  # type: ignore
        self, form: _RegistrationStepFormBase
    ) -> dict[str, object]:
        context = super().get_render_context(form)
        context['instruments'] = self.registration_entry.instruments_bringing.all()
        return context

    def get_step_instance(self) -> BeginnerInstrumentInfo | None:
        if (self.registration_entry.program in BEGINNER_PROGRAMS
                and hasattr(self.registration_entry, 'beginner_instruments')):
            return self.registration_entry.beginner_instruments

        return None


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


def flex_choice_class_label(class_: Class) -> str:
    return f'{PERIOD_STRS[class_.period]} Per: ' + str(class_)


class RegularProgramClassSelectionForm(_RegistrationStepFormBase, forms.ModelForm):
    instance: RegularProgramClassChoices

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
        ) + [
            'comments',
            'flex_choice1',
            'flex_choice1_instrument',
            'flex_choice2',
            'flex_choice2_instrument',
            'flex_choice3',
            'flex_choice3_instrument',
        ]

        widgets = {
            'comments': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
        }

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        classes_by_period = get_classes_by_period(
            self.registration_entry.conclave_config_id,
            program=self.registration_entry.program
        )

        for period, field_names in _CLASS_CHOICE_FIELD_NAMES_BY_PERIOD.items():
            for field_name in field_names:
                self.fields[field_name].queryset = classes_by_period[period]
                self.fields[field_name].empty_label = 'No class'

        for field_name in chain.from_iterable(_INSTRUMENT_FIELD_NAMES_BY_PERIOD.values()):
            self.fields[field_name].queryset = InstrumentBringing.objects.filter(
                registration_entry=self.registration_entry
            )
            self.fields[field_name].empty_label = 'Any I listed'

        if self.registration_entry.uses_flexible_class_selection:
            self.flexible_class_selection_init()

    def flexible_class_selection_init(self) -> None:
        class_options_queryset = Class.objects.filter(
            conclave_config=self.registration_entry.conclave_config
        ).exclude(period=Period.fourth)

        self.fields['flex_choice1'].queryset = class_options_queryset
        self.fields['flex_choice1'].label_from_instance = flex_choice_class_label
        self.fields['flex_choice1_instrument'].queryset = InstrumentBringing.objects.filter(
            registration_entry=self.registration_entry
        )
        self.fields['flex_choice1_instrument'].empty_label = 'Any I listed'

        self.fields['flex_choice2'].queryset = class_options_queryset
        self.fields['flex_choice2'].label_from_instance = flex_choice_class_label
        self.fields['flex_choice2_instrument'].queryset = InstrumentBringing.objects.filter(
            registration_entry=self.registration_entry
        )
        self.fields['flex_choice2_instrument'].empty_label = 'Any I listed'

        self.fields['flex_choice3'].queryset = class_options_queryset
        self.fields['flex_choice3'].label_from_instance = flex_choice_class_label
        self.fields['flex_choice3_instrument'].queryset = InstrumentBringing.objects.filter(
            registration_entry=self.registration_entry
        )
        self.fields['flex_choice3_instrument'].empty_label = 'Any I listed'

        if (self.registration_entry.uses_flexible_class_selection
                and self.registration_entry.program == Program.part_time):
            self.fields['flex_choice1'].required = True
            self.fields['flex_choice2'].required = True
            self.fields['flex_choice3'].required = True

    def full_clean(self) -> None:
        super().full_clean()
        # Running the validation logic below will cause an exception to
        # be thrown if "self.cleaned_data" is not available. Validation
        # gets triggered by our non-field-error display code near the top
        # of the template, and self.cleaned_data
        # is typically not available when rendering for a GET request
        # This check will prevent us from running our extra validation
        # if all we're doing is rendering for a GET request.
        if not hasattr(self, 'cleaned_data'):
            return

        if self.registration_entry.program == Program.regular:
            if self.instance.num_non_freebie_classes < 2:
                self.add_error(
                    None,
                    'Regular Curriculum (full-time) attendees must select at least '
                    '2 non-freebie courses to attend. If you want to take only one '
                    'class, you should register as part-time. '
                    "If you don't want to take any classes, you should register "
                    'as a non-playing attendee.'
                )

        self._validate_period_preferences(Period.first)
        self._validate_period_preferences(Period.second)
        self._validate_period_preferences(Period.third)
        self._validate_period_preferences(Period.fourth)

        self._validate_extra_class_preferences()

    def _validate_period_preferences(self, period: Period) -> None:
        choices = [
            choice['class'] for choice in self.instance.by_period[period]
            if choice['class'] is not None
        ]

        if len(choices) == 0:
            return

        # Allow < 3 choices for freebies and beginners
        if (len(choices) != 3 and period != Period.fourth
                and self.registration_entry.program != Program.beginners):
            self.add_error(
                None,
                f'{format_period_long(period)}: You must select a 1st, 2nd, and 3rd choice. '
                'If you do not want to take a class during this period, please '
                'set all three choices to "No class."'
            )

        if len(set(choices)) != len(choices):
            self.add_error(
                None,
                f'{format_period_long(period)}: You must select different classes for '
                'your 1st, 2nd, and 3rd choices.'
            )

    def _validate_extra_class_preferences(self) -> None:
        if not self.registration_entry.uses_flexible_class_selection:
            return

        # All three choices must be selected.
        extra_class_choices = [
            self.instance.flex_choice1,
            self.instance.flex_choice2,
            self.instance.flex_choice3
        ]

        # Note: In part-time class selection, the flex choice fields
        # are marked as required, so if we get to this point for part-time
        # registration, num_choices should always be 3.
        num_choices = sum(1 for choice in extra_class_choices if choice is not None)
        if num_choices == 0:
            return

        if num_choices != len(extra_class_choices):
            self.add_error(
                None,
                'Add-on class: You must select a 1st, 2nd, and 3rd choice. '
                'If you do not want to take an extra class, please '
                'set all three choices to "No class."'
            )

        if len(set(extra_class_choices)) != len(extra_class_choices):
            self.add_error(
                None,
                f'You must select different classes for '
                'your 1st, 2nd, and 3rd choices.'
            )


class RegularProgramClassSelectionView(_RegistrationStepViewBase):
    template_name = 'registration/regular_class_selection.html'
    form_class = RegularProgramClassSelectionForm

    def get_next_step_url(self) -> str:
        if self.registration_entry.program == Program.seasoned_players:
            url_name = 'conclave-advanced-projects'
        else:
            url_name = 'conclave-basic-info'

        return reverse(
            url_name,
            kwargs={'conclave_reg_pk': self.registration_entry.pk}
        )

    def get_step_instance(self) -> RegularProgramClassChoices | None:
        if hasattr(self.registration_entry, 'regular_class_choices'):
            return self.registration_entry.regular_class_choices

        return None

    def get_render_context(  # type: ignore
        self, form: _RegistrationStepFormBase
    ) -> dict[str, object]:
        context = super().get_render_context(form)
        classes_offered = get_classes_by_period(
            self.registration_entry.conclave_config_id,
            program=self.registration_entry.program
        )
        if not self.registration_entry.uses_flexible_class_selection:
            if not self._show_first_period:
                classes_offered.pop(Period.first)
            if not self._show_second_period:
                classes_offered.pop(Period.second)
            if not self._show_third_period:
                classes_offered.pop(Period.third)
            if not self._show_fourth_period:
                classes_offered.pop(Period.fourth)

        context.update({
            'classes_by_period': classes_offered,

            'show_first_period': self._show_first_period,
            'show_second_period': self._show_second_period,
            'show_third_period': self._show_third_period,
            'show_fourth_period': self._show_fourth_period,
        })
        return context

    @property
    def _show_first_period(self) -> bool:
        if self.registration_entry.program == Program.beginners:
            return self._period_has_beginner_add_on_classes(Period.first)

        return self.registration_entry.program in [Program.regular, Program.consort_coop]

    @property
    def _show_second_period(self) -> bool:
        if self.registration_entry.program == Program.beginners:
            return self._period_has_beginner_add_on_classes(Period.second)

        return self.registration_entry.program in [Program.regular, Program.consort_coop]

    @property
    def _show_third_period(self) -> bool:
        if self.registration_entry.program == Program.beginners:
            return self._period_has_beginner_add_on_classes(Period.third)

        return self.registration_entry.program in [Program.regular]

    @property
    def _show_fourth_period(self) -> bool:
        """
        Fourth period contains only freebie classes.
        """
        return self.registration_entry.program in [
            Program.regular,
            Program.beginners,
            Program.seasoned_players,
        ]

    def _period_has_beginner_add_on_classes(self, period: Period) -> bool:
        return self.registration_entry.conclave_config.classes.filter(
            period=period,
            offer_to_beginners=True
        ).exists()


class AdvancedProjectsForm(_RegistrationStepFormBase, forms.ModelForm):
    class Meta:
        fields = [
            'participation',
            'project_proposal',
        ]
        model = AdvancedProjectsInfo

        labels = {
            'participation': '',
            'project_proposal': '',
        }
        widgets = {
            'participation': widgets.RadioSelect(),
            'project_proposal': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
        }

    def full_clean(self) -> None:
        super().full_clean()

        # Running the validation logic below will cause an exception to
        # be thrown if "self.cleaned_data" is not available. Validation
        # gets triggered by our non-field-error display code near the top
        # of the template, and self.cleaned_data
        # is typically not available when rendering for a GET request
        # This check will prevent us from running our extra validation
        # if all we're doing is rendering for a GET request.
        if not hasattr(self, 'cleaned_data'):
            return

        if self.registration_entry.program != Program.seasoned_players:
            return

        if (self.instance.participation == YesNo.yes
                and not self.instance.project_proposal):
            self.add_error(None, 'Please describe your proposed project.')


class AdvancedProjectsView(_RegistrationStepViewBase):
    template_name = 'registration/advanced_projects.html'
    form_class = AdvancedProjectsForm
    next_step_url_name = 'conclave-basic-info'

    def get_step_instance(self) -> AdvancedProjectsInfo | None:
        if hasattr(self.registration_entry, 'advanced_projects'):
            return self.registration_entry.advanced_projects

        return None


class HousingForm(_RegistrationStepFormBase, forms.ModelForm):
    class Meta:
        fields = [
            'room_type',
            'roommate_request',
            'room_near_person_request',
            'normal_bed_time',
            'arrival_day',
            'departure_day',
            'wants_housing_subsidy',
            'wants_2023_supplemental_discount',
            'wants_canadian_currency_exchange_discount',
            'additional_housing_info',
            'dietary_needs',
            'other_dietary_needs',
            'banquet_food_choice',
            'is_bringing_guest_to_banquet',
            'banquet_guest_name',
            'banquet_guest_food_choice',
        ]
        model = Housing

        labels = {
            'room_type': '',
            'roommate_request': '',
            'room_near_person_request': '',
            'normal_bed_time': '',
            'arrival_day': '',
            'departure_day': '',
            'additional_housing_info': '',
            'dietary_needs': '',
            'other_dietary_needs': '',
            'banquet_food_choice': '',
            'is_bringing_guest_to_banquet': '',
            'banquet_guest_name': '',
            'banquet_guest_food_choice': '',
        }

        widgets = {
            'room_type': widgets.RadioSelect(),
            'roommate_request': widgets.TextInput(),
            'room_near_person_request': widgets.TextInput(),
            'normal_bed_time': widgets.RadioSelect(),
            'additional_housing_info': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
            'dietary_needs': widgets.CheckboxSelectMultiple(choices=DietaryNeeds.choices),
            'other_dietary_needs': widgets.Textarea(attrs={'rows': 5, 'cols': None}),
            'banquet_guest_name': widgets.TextInput(),
        }

    is_bringing_guest_to_banquet = YesNoRadioField(label='', required=True)

    # We don't want the field to process the "dietary_needs" data in any way,
    # just pass it through to the underlying postgres array field.
    dietary_needs = _PassThroughField(
        widget=widgets.CheckboxSelectMultiple(choices=DietaryNeeds.choices),
        label='',
        required=False
    )

    def __init__(self, registration_entry: RegistrationEntry, *args: Any, **kwargs: Any):
        super().__init__(registration_entry, *args, **kwargs)
        if 'dietary_needs' not in self.initial and self.instance is not None:
            self.initial['dietary_needs'] = self.instance.dietary_needs

        early_arrival_dates: List[str] = (
            self.registration_entry.conclave_config.early_arrival_date_options.splitlines())
        arrival_dates: List[str] = (
            self.registration_entry.conclave_config.arrival_date_options.splitlines())
        departure_dates: List[str] = (
            self.registration_entry.conclave_config.departure_date_options.splitlines())

        all_arrival_dates = early_arrival_dates + arrival_dates
        self.fields['arrival_day'].widget = widgets.Select(
            choices=list(zip(all_arrival_dates, all_arrival_dates)))
        # Select the first regular arrival date by default.
        self.fields['arrival_day'].initial = arrival_dates[0] if arrival_dates else ''

        self.fields['departure_day'].widget = widgets.Select(
            choices=list(zip(departure_dates, departure_dates)))
        self.fields['departure_day'].initial = departure_dates[-1] if departure_dates else ''

        banquet_options = (
            self.registration_entry.conclave_config.banquet_food_options.splitlines())
        self.fields['banquet_food_choice'].widget = widgets.RadioSelect(
            choices=(
                list(zip(banquet_options, banquet_options))
                + [(NOT_ATTENDING_BANQUET_SENTINEL, 'Not Attending')]
            )
        )
        self.fields['banquet_guest_food_choice'].widget = widgets.RadioSelect(
            choices=list(zip(banquet_options, banquet_options))
        )

    def full_clean(self) -> None:
        super().full_clean()

        # Running the validation logic below will cause an exception to
        # be thrown if "self.cleaned_data" is not available. Validation
        # gets triggered by our non-field-error display code near the top
        # of the template, and self.cleaned_data
        # is typically not available when rendering for a GET request
        # This check will prevent us from running our extra validation
        # if all we're doing is rendering for a GET request.
        if not hasattr(self, 'cleaned_data'):
            return

        if (self.instance.room_type != HousingRoomType.off_campus
                and not self.instance.normal_bed_time):
            self.add_error(None, 'Please specify your preferred normal bedtime.')

        # Added for 2023 only (one bed per room)
        if (self.registration_entry.conclave_config.year == 2023
                and self.instance.room_type == HousingRoomType.double
                and not self.instance.roommate_request):
            self.add_error(None, 'Please specify your preferred roommate.')

        if self.instance.room_type == HousingRoomType.off_campus:
            self.instance.wants_housing_subsidy = False
            self.instance.wants_2023_supplemental_discount = False

        if self.instance.is_bringing_guest_to_banquet == YesNo.yes:
            if not (self.instance.banquet_guest_food_choice and self.instance.banquet_guest_name):
                self.add_error(
                    None,
                    'Banquet guest info: You indicated that you are '
                    'bringing a guest to the banquet. '
                    'Please provide their name and food choice.'
                )


class HousingView(_RegistrationStepViewBase):
    template_name = 'registration/housing.html'
    form_class = HousingForm
    next_step_url_name = 'conclave-tshirts'

    def get_step_instance(self) -> Housing | None:
        if hasattr(self.registration_entry, 'housing'):
            return self.registration_entry.housing

        return None


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

    def get_step_instance(self) -> TShirts | None:
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
            raise ValidationError('Invalid card number: numbers only (no spaces)')


class PaymentForm(_RegistrationStepFormBase, forms.ModelForm):
    class Meta:
        model = PaymentInfo
        fields: List[str] = []

    name_on_card = forms.CharField()
    card_number = forms.CharField(validators=[_credit_card_number_validator])
    expiration_month = forms.ChoiceField(choices=list(zip(_MONTHS, _MONTHS)))
    expiration_year = forms.ChoiceField(choices=list(zip(_YEARS, _YEARS)))
    cvc = forms.CharField()


class PaymentView(_RegistrationStepViewBase):
    template_name = 'registration/payment/payment.html'
    form_class = PaymentForm
    next_step_url_name = 'conclave-done'

    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
        return self.render_page(PaymentForm(self.registration_entry))

    def post(self, *args: Any, **kwargs: Any) -> HttpResponse:
        form = self.get_form()
        if not form.is_valid():  # type: ignore
            return self.render_page(form)

        payment_info = form.save(commit=False)

        if self._get_missing_sections():
            return self.render_page(form)

        try:
            card_number = ''.join(form.cleaned_data['card_number'].split())
            payment_method = stripe.PaymentMethod.create(
                type='card',
                card={
                    'number': card_number,  # type: ignore
                    'exp_month': form.cleaned_data['expiration_month'],  # type: ignore
                    'exp_year': form.cleaned_data['expiration_year'],  # type: ignore
                    'cvc': form.cleaned_data['cvc'],  # type: ignore
                },
                billing_details={
                    'name': form.cleaned_data['name_on_card']  # type: ignore
                }
            )

            user = self.registration_entry.user
            year = self.registration_entry.conclave_config.year
            new_customer = stripe.Customer.create(
                description=f"Conclave {year} registration",
                email=user.email,
                name=show_name(user),
                phone=user.phone1,
                address={
                    'city': user.address_city,
                    'country': user.address_country,
                    'line1': user.address_line_1,
                    'line2': user.address_line_2,
                    'postal_code': user.address_postal_code,
                    'state': user.address_state,
                },
            )

            stripe.PaymentMethod.attach(payment_method.id, customer=new_customer.id)
        except stripe.error.CardError as e:
            return self.render_page(form, {'stripe_error': e.user_message})

        payment_info.stripe_payment_method_id = payment_method.id
        payment_info.save()
        send_confirmation_email(self.registration_entry)
        send_instrument_loan_emails(self.registration_entry)

        return HttpResponseRedirect(self.get_next_step_url())

    def get_step_instance(self) -> PaymentInfo | None:
        if hasattr(self.registration_entry, 'payment_info'):
            return self.registration_entry.payment_info

        return None

    def get_render_context(self, form: _RegistrationStepFormBase | None) -> dict[str, object]:
        context = super().get_render_context(form)
        context['missing_sections'] = self._get_missing_sections()
        context['class_selection_required'] = self.registration_entry.class_selection_is_required
        context['registration_summary'] = get_registration_summary(self.registration_entry)
        context['charges_summary'] = get_charges_summary(self.registration_entry)
        if settings.DEBUG:
            context['confirmation_email_debug'] = (
                _render_confirmation_email(self.registration_entry))
        return context

    def _get_missing_sections(self) -> list[str]:
        missing_sections = []

        if (self.registration_entry.self_rating_is_required
                and not hasattr(self.registration_entry, 'self_rating')):
            missing_sections.append('Self-Rating')

        if self.registration_entry.class_selection_is_required:
            if self.registration_entry.program in BEGINNER_PROGRAMS:
                if not hasattr(self.registration_entry, 'beginner_instruments'):
                    missing_sections.append('Instruments')
            elif self.registration_entry.instruments_bringing.count() == 0:
                missing_sections.append('Instruments')

            if not hasattr(self.registration_entry, 'regular_class_choices'):
                missing_sections.append('Classes')

        if (self.registration_entry.program == Program.seasoned_players
                and not hasattr(self.registration_entry, 'advanced_projects')):
            missing_sections.append('Advanced Projects')

        if not hasattr(self.registration_entry, 'additional_info'):
            missing_sections.append('Additional Info')

        if self.registration_entry.class_selection_is_required:
            if not hasattr(self.registration_entry, 'work_study'):
                missing_sections.append('Work-Study')

        if not hasattr(self.registration_entry, 'housing'):
            missing_sections.append('Housing')

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


class CurrentUserRegistrationSummaryView(LoginRequiredMixin, View):
    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
        registration_entry = get_object_or_404(
            RegistrationEntry.objects.filter(
                conclave_config_id=(
                    self.kwargs['conclave_config_pk']
                ),
                user=self.request.user,
            )
        )
        return render(
            self.request,
            'registration/payment/summary.tmpl',
            context={
                'registration_summary': get_registration_summary(registration_entry),
                'charges_summary': get_charges_summary(registration_entry)
            }
        )


def send_confirmation_email(registration_entry: RegistrationEntry) -> None:
    send_mail(
        subject=f'VdGSA Conclave {registration_entry.conclave_config.year} '
                f'- Thank you for registering, {show_name(registration_entry.user)}!',
        from_email=None,
        recipient_list=[
            registration_entry.user.username,
            'conclave.manager@vdgsa.org',
            'conclave.manager@gmail.com',
            'treasurer@vdgsa.org',
        ],
        message=_render_confirmation_email(registration_entry)
    )


def _render_confirmation_email(registration_entry: RegistrationEntry) -> str:
    message = render_to_string(
        'registration/confirmation_email.tmpl',
        {
            'registration_entry': registration_entry,
            'conclave_config': registration_entry.conclave_config,
            'class_selection_required': registration_entry.class_selection_is_required,
            'registration_summary': get_registration_summary(registration_entry),
            'charges_summary': get_charges_summary(registration_entry),
        }
    )

    # Remove blank lines and strip leading and trailing whitespace.
    result = ''
    for line in message.splitlines():
        line = line.strip()
        if line == '<br>':
            result += '\n'
        elif line:
            result += line
            result += '\n'  # Add back a newline since we stripped whitespace

    return result


def send_instrument_loan_emails(registration_entry: RegistrationEntry) -> None:
    _send_instrument_loan_email_impl(
        registration_entry.user,
        registration_entry.instruments_bringing.filter(purpose=InstrumentPurpose.willing_to_loan),
        subject=f'Conclave {registration_entry.conclave_config.year} Instrument Loan Offer',
        purpose_text='is offering to loan the instrument(s) below\n'
    )

    _send_instrument_loan_email_impl(
        registration_entry.user,
        registration_entry.instruments_bringing.filter(purpose=InstrumentPurpose.wants_to_borrow),
        subject=f'Conclave {registration_entry.conclave_config.year} Instrument Borrow Request',
        purpose_text='wants to borrow the instrument(s) below\n'
    )

    if (hasattr(registration_entry, 'beginner_instruments')
            and registration_entry.beginner_instruments.needs_instrument == YesNo.yes):
        send_mail(
            f'Conclave {registration_entry.conclave_config.year} '
            'Beginner Instrument Borrow Request',
            from_email=None,
            recipient_list=['rentalviol@vdgsa.org'],
            message=f'{show_name_and_email(registration_entry.user)} wants to borrow an instument '
                    'for the beginner program.'
        )


def _send_instrument_loan_email_impl(
    user: User, instruments: Iterable[InstrumentBringing], *, subject: str, purpose_text: str
):
    if instruments:
        message = f'{show_name_and_email(user)} ' + purpose_text
        for i, instrument in enumerate(instruments):
            message += f'{i}. {instrument}\n'
            message += instrument.comments
        send_mail(
            subject,
            from_email=None,
            recipient_list=['rentalviol@vdgsa.org'],
            message=message
        )
