import datetime
from typing import Any

from django import forms
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Max
from django.forms.widgets import HiddenInput
from django.http.request import HttpRequest
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls.base import reverse
from django.utils import timezone
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.generic.list import ListView

from vdgsa_backend.accounts.models import User
from vdgsa_backend.rental_viols.managers.RentalItemBaseManager import RentalEvent, RentalState
from vdgsa_backend.rental_viols.models import (
    Bow, Case, Image, RentalHistory, RentalProgram, Viol, ViolSize, WaitingList
)
from vdgsa_backend.rental_viols.views.utils import (
    NotesOnlyHistoryForm, RentalEditBase, RentalViewBase, ReserveViolModelForm
)


class ViolsMultiListView(RentalViewBase, ListView):
    template_name = 'viols/list.html'
    filterSessionName = 'viol_filter'
    filter = None

    def getFilter(self, **kwargs):
        filter = {}

        if self.request.GET.get('state') is None:
            filter = self.request.session.get(self.filterSessionName, None)
            if filter is None:
                filter = {'state': 'all', 'program': 'all', 'size': 'all', }
        else:
            filter = {'state': self.request.GET.get('state') or 'all',
                      'program': self.request.GET.get('program') or 'all',
                      'size': self.request.GET.get('size') or 'all', }
        return filter

    def get_context_data(self, **kwargs):
        context = super(ViolsMultiListView, self).get_context_data(**kwargs)
        context['filter'] = self.getFilter()
        context['ViolSize'] = ViolSize
        return context

    def get_queryset(self, *args: Any, **kwargs: Any):
        filter = self.getFilter()
        self.request.session[self.filterSessionName] = filter

        size = None if filter['size'] == 'all' else filter['size']
        if filter['state'] == 'available':
            queryset = Viol.objects.get_available(size)
        elif filter['state'] == 'retired':
            queryset = Viol.objects.get_retired(size)
        elif filter['state'] == 'rented':
            queryset = Viol.objects.get_rented(size)
        else:
            queryset = Viol.objects.get_all(size)

        if filter['program'] != 'all':
            queryset = queryset.filter(program=RentalProgram[filter['program']])

        return queryset.annotate(rental_end_date=Max('history__rental_end'))


class ViolForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ViolForm, self).__init__(*args, **kwargs)
        self.fields['vdgsa_number'].widget = HiddenInput()
        self.fields['strings'].required = True

    class Meta:
        model = Viol
        fields = [
            'vdgsa_number',
            'maker',
            'size',
            'strings',
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


class DetachFromViolView(RentalEditBase, View):
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        if self.request.GET.get('viol_num'):
            viol = Viol.objects.get(pk=self.request.GET['viol_num'])
            if self.request.GET.get('bow_num'):
                bow = Bow.objects.get(pk=self.request.GET['bow_num'])
                bow.viol_num = None
                bow.status = RentalState.detached
                bow.storer = viol.storer
                bow.save()
                history = RentalHistory.objects.create(
                    viol_num=viol,
                    event=RentalEvent.detached,
                    bow_num=bow)
                history.save()
                messages.add_message(self.request, messages.SUCCESS, 'Bow attached!')

            if self.request.GET.get('case_num'):
                case = Case.objects.get(pk=self.request.GET['case_num'])
                case.viol_num = None
                case.status = RentalState.detached
                case.storer = viol.storer
                case.save()
                history = RentalHistory.objects.create(
                    viol_num=viol,
                    event=RentalEvent.detached,
                    case_num=case)
                history.save()
                messages.add_message(self.request, messages.SUCCESS, 'Case detatched!')

        return redirect(reverse('viol-detail', args=[self.request.GET['viol_num']]))


class ChangeCustView(RentalEditBase, SuccessMessageMixin, View):

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any):
        if self.request.POST.get('user_id'):
            custodian = User.objects.get(pk=self.request.POST.get('user_id'))
        else:
            custodian = None

        if self.request.POST.get('viol_num'):
            viol = Viol.objects.get(pk=self.request.POST.get('viol_num'))
            viol.storer = custodian
            viol.save()
        if self.request.POST.get('bow_num'):
            bow = Bow.objects.get(pk=self.request.POST.get('bow_num'))
            bow.storer = custodian
            bow.save()
        if self.request.POST.get('case_num'):
            case = Case.objects.get(pk=self.request.POST.get('case_num'))
            case.storer = custodian
            case.save()

        return HttpResponseRedirect(self.request.POST.get('page'))


class ReserveViolView(RentalEditBase, FormView):
    template_name = 'renters/reserve.html'
    form_class = ReserveViolModelForm
    model = ReserveViolModelForm
    success_url = '/rentals/waiting/'

    def get_initial(self):
        initial = super().get_initial()
        initial['date_req'] = datetime.date.today
        if self.request.GET.get('viol_num'):
            viol = Viol.objects.get(pk=self.request.GET.get('viol_num'))
            initial['viol_num'] = viol
        # if self.request.GET.get('user_id'):
        #     renter = User.objects.get(pk=self.request.GET.get('user_id'))
        #     initial['renter_num'] = renter
        return initial

    # def get_context_data(self, **kwargs):
    #     data = super().get_context_data(**kwargs)
    #     return data

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        context = self.get_context_data(**kwargs)
        context['form'] = form

        if self.request.GET.get('viol_num'):
            context['viol'] = Viol.objects.get(pk=request.GET.get('viol_num'))
            context['users'] = User.objects.all()

        return self.render_to_response(context)

    def form_valid(self, form):
        waitinglist, created = WaitingList.objects.update_or_create(
            # renter_num=form.cleaned_data['renter_num'],
            viol_num=form.cleaned_data['viol_num'],
            date_req=form.cleaned_data['date_req'],
            size=form.cleaned_data['size'],
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            email=form.cleaned_data['email'],
            address_line_1=form.cleaned_data['address_line_1'],
            address_city=form.cleaned_data['address_city'],
            address_state=form.cleaned_data['address_state'],
            address_postal_code=form.cleaned_data['address_postal_code'],
            phone1=form.cleaned_data['phone1'])

        if form.cleaned_data['viol_num']:
            viol = Viol.objects.get(pk=form.cleaned_data['viol_num'].pk)
            history = RentalHistory.objects.create(viol_num=viol, event=RentalEvent.reserved)
            history.save()

        messages.add_message(self.request, messages.SUCCESS, 'Waiting List record created!')
        return super().form_valid(form)


class AddViolView(RentalEditBase, SuccessMessageMixin, CreateView):
    model = Viol
    form_class = ViolForm
    initial = {
        'vdgsa_number': Viol.objects.get_next_vdgsa_num,
        'accession_date': datetime.date.today}
    template_name = 'viols/add.html'
    success_message = "%(size)s viol was created successfully"


class UpdateViolView(RentalEditBase, SuccessMessageMixin, UpdateView):
    model = Viol
    form_class = ViolForm
    template_name = 'viols/update.html'
    success_message = "%(size)s viol was updated successfully"

    def get_success_url(self, **kwargs) -> str:
        return reverse('list-viols')


class ViolDetailView(RentalViewBase, DetailView):
    model = Viol
    template_name = 'viols/detail.html'

    def get_context_data(self, **kwargs):
        context = super(ViolDetailView, self).get_context_data(**kwargs)
        context['RentalEvent'] = RentalEvent
        context['RentalState'] = RentalState
        context['now'] = timezone.now()
        context['images'] = Image.objects.get_images('viol', context['viol'].pk)
        context['last_rental'] = (context['viol'].history.filter(event=RentalEvent.rented)
                                  .order_by('-created_at').first())
        return context


class AvailableViolView(RentalViewBase, FormView):
    """Make Available"""
    template_name = 'viols/available.html'
    form_class = NotesOnlyHistoryForm
    model = RentalHistory

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        form = NotesOnlyHistoryForm(initial={'item': self.kwargs['viol_num']})
        context = self.get_context_data(**kwargs)
        context['form'] = form

        context['viol'] = Viol.objects.get(pk=self.kwargs['viol_num'])
        # context['form'] = RentalHistoryForm(
        #     {"event": RentalEvent.retired, "viol_num": viol.viol_num,
        #         "case_num": viol.cases.first().case_num if viol.cases.exists() else None,
        #         "bow_num": viol.bows.first().bow_num if viol.bows.exists() else None})

        return render(request, 'viols/available.html', context)

    def form_valid(self, form):
        viol = Viol.objects.get(pk=self.request.POST['viol_num'])
        viol.status = RentalState.available
        viol.save()
        if viol.cases.exists():
            viol.cases.first().status = RentalState.available
            viol.cases.first().save()
        if viol.bows.exists():
            viol.bows.first().status = RentalState.available
            viol.bows.first().save()
        history = RentalHistory.objects.create(
            viol_num=viol,
            case_num=viol.cases.first() if viol.cases.exists() else None,
            bow_num=viol.bows.first() if viol.bows.exists() else None,
            event=RentalState.available,
            notes=form.cleaned_data['notes'])
        history.save()

        messages.add_message(self.request, messages.SUCCESS, 'Viol Made Available!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('viol-detail', args=[self.request.POST.get('viol_num')])


class RetireViolView(RentalEditBase, FormView):
    """Renew Rental Agreement"""
    template_name = './retireMulti.html'
    form_class = NotesOnlyHistoryForm
    model = RentalHistory

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        form = NotesOnlyHistoryForm(initial={'item': self.kwargs['viol_num']})
        context = self.get_context_data(**kwargs)
        context['viol'] = Viol.objects.get(pk=self.kwargs['viol_num'])
        context['form'] = form
        return render(request, 'viols/retire.html', context)

    def form_valid(self, form):
        viol = Viol.objects.get(pk=self.kwargs['viol_num'])
        viol.status = RentalState.retired
        viol.save()
        if viol.cases.exists():
            viol.cases.first().status = RentalState.retired
            viol.cases.first().save()
        if viol.bows.exists():
            viol.bows.first().status = RentalState.retired
            viol.bows.first().save()
        history = RentalHistory.objects.create(
            viol_num=viol,
            case_num=viol.cases.first() if viol.cases.exists() else None,
            bow_num=viol.bows.first() if viol.bows.exists() else None,
            event=RentalEvent.retired,
            notes=form.cleaned_data['notes'])
        history.save()

        messages.add_message(self.request, messages.SUCCESS, 'Viol Retired!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('viol-detail', args=[self.kwargs['viol_num']])
