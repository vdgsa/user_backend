import datetime
from functools import cached_property
from typing import Any, Dict, Iterable, Literal

from django import forms
from django.apps import apps
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.storage import FileSystemStorage
from django.db.models import Count, F, Max, Q, IntegerField
from django.db.models.functions import Cast
from django.forms.widgets import DateTimeBaseInput, HiddenInput
from django.http import Http404, JsonResponse, response
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls.base import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import urlencode
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.generic.list import ListView

from vdgsa_backend.accounts.models import User
from vdgsa_backend.rental_viols.managers.InstrumentManager import AccessoryManager, ViolManager
from vdgsa_backend.rental_viols.managers.RentalItemBaseManager import (
    RentalEvent, RentalItemBaseManager, RentalState
)
from vdgsa_backend.rental_viols.models import (
    Bow, Case, Image, ItemType, RentalContract, RentalHistory, RentalProgram, Viol, ViolSize,
    WaitingList
)
from vdgsa_backend.rental_viols.permissions import is_rental_manager
from vdgsa_backend.rental_viols.views.utils import (
    NotesOnlyHistoryForm, RentalViewBase, ReserveViolModelForm, _createUserStamp
)


class RentalHistoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(RentalHistoryForm, self).__init__(*args, **kwargs)
        self.fields['rental_start'].required = True
        self.fields['rental_end'].required = True
        self.fields['event'].widget = HiddenInput()

    class Meta:
        model = RentalHistory
        fields = [
            'event',
            'entry_num',
            'viol_num',
            'bow_num',
            'case_num',
            'renter_num',
            'notes',
            'rental_start',
            'rental_end',
        ]
        labels = {'event': '', }
        widgets = {
            'rental_start': forms.DateInput(format=('%Y-%m-%d'),
                                            attrs={'class': 'form-control',
                                                   'placeholder': 'Select a date',
                                                   'type': 'date'}),
            'rental_end': forms.DateInput(format=('%Y-%m-%d'),
                                          attrs={'class': 'form-control',
                                                 'placeholder': 'Select a date',
                                                 'type': 'date'}),
        }


class AttachToRentalView(RentalViewBase, View):
    """Attach a Viol or accessory to Rental Agreement"""
    template_name = 'renters/attatchToRental.html'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        if self.request.method == 'GET' and 'item' in self.request.GET:
            context['item'] = self.request.GET['item']
            context['rental'] = RentalHistory.objects.get(pk=self.request.GET['entry_num'])
            if context['rental'].viol_num:
                context['avail_cases'] = context['rental'].viol_num.cases
                context['avail_bows'] = context['rental'].viol_num.bows
            else:
                context['viol'] = Viol.objects.get_available()
                context['avail_cases'] = Case.objects.get_available()
                context['avail_bows'] = Bow.objects.get_available()

        return render(
            self.request,
            'renters/attatchToRental.html', context
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any):
        if self.request.POST.get('entry_num'):
            rental = RentalHistory.objects.get(pk=self.request.POST['entry_num'])
            if self.request.POST.get('bow_num'):
                bow = Bow.objects.get(pk=self.request.POST['bow_num'])
                bow.status = RentalState.attached
                bow.save()
                rental.bow_num = bow
                rental.save()
                messages.add_message(self.request, messages.SUCCESS, 'Bow attached!')

            if self.request.POST.get('case_num'):
                case = Case.objects.get(pk=self.request.POST['case_num'])
                case.status = RentalState.attached
                case.save()
                rental.case_num = case
                rental.save()
                messages.add_message(self.request, messages.SUCCESS, 'Case attached!')

        return redirect(reverse('rental-detail', args=[self.request.POST.get('entry_num')]))


class AttachToViolView(RentalViewBase, View):
    template_name = 'viols/attatchToViol.html'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        if self.request.method == 'GET' and 'viol_num' in self.request.GET:
            context['viol'] = Viol.objects.get(pk=self.request.GET['viol_num'])
            context['avail_cases'] = Case.objects.get_unattached(context['viol'].size)
            context['avail_bows'] = Bow.objects.get_unattached(context['viol'].size)
            # Get List of available bows and cases
        else:
            size = ''
            if 'case_num' in self.request.GET:
                case_num = self.request.GET['case_num']
                if case_num is not None and case_num != '':
                    context['case'] = Case.objects.get(pk=case_num)
                    size = context['case'].size
            if 'bow_num' in self.request.GET:
                bow_num = self.request.GET['bow_num']
                if bow_num is not None and bow_num != '':
                    context['bow'] = Bow.objects.get(pk=bow_num)
                    size = context['bow'].size

            # Get List of bachelor viols
            context['viols'] = Viol.objects.get_attachable(size)

        return render(
            self.request,
            'viols/attatchToViol.html', context
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any):
        if self.request.POST.get('viol_num'):
            viol = Viol.objects.get(pk=self.request.POST.get('viol_num'))
            if self.request.POST.get('bow_num'):
                bow = Bow.objects.get(pk=self.request.POST['bow_num'])
                bow.status = RentalState.attached
                bow.save()
                viol.bows.add(bow)
                history = RentalHistory.objects.create(
                    viol_num=viol,
                    event=RentalEvent.attached,
                    bow_num=bow)
                history.save()
                messages.add_message(self.request, messages.SUCCESS, 'Bow attached!')

            if self.request.POST.get('case_num'):
                case = Case.objects.get(pk=self.request.POST['case_num'])
                case.status = RentalState.attached
                case.save()
                viol.cases.add(case)
                history = RentalHistory.objects.create(
                    viol_num=viol,
                    event=RentalEvent.attached,
                    case_num=case)
                history.save()
                messages.add_message(self.request, messages.SUCCESS, 'Case attached!')

        return redirect(reverse('viol-detail', args=[self.request.POST.get('viol_num')]))


class RentalHomeView(RentalViewBase, TemplateView):
    template_name = 'home.html'


class RentOutForm(forms.Form):
    viol_num = forms.IntegerField()
    user_id = forms.IntegerField()


class RentOutView(RentalViewBase, FormView):
    """get to select Rental User"""
    form_class = RentOutForm

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        context['avail_viols'] = Viol.objects.get_available().annotate(vdgsa_int=Cast(
            'vdgsa_number', IntegerField())).order_by('size', 'vdgsa_int')

        if self.request.GET.get('viol_num'):
            context['viol'] = Viol.objects.get(pk=self.request.GET['viol_num'])
            context['viol_num'] = self.request.GET['viol_num']
        else:
            context['viol_num'] = None
        return render(request, 'renters/rentOut.html', context)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        form = RentOutForm(request.POST or None)
        if not form.is_valid():
            messages.add_message(self.request, messages.ERROR, 'Please select a User and a Viol.')
            context['avail_viols'] = Viol.objects.get_available()
            return render(request, 'renters/rentOut.html', context)
        else:
            context['viol'] = Viol.objects.get(pk=self.request.POST['viol_num'])
            context['user'] = User.objects.get(pk=self.request.POST['user_id'])
            context['form'] = RentalAgreementForm(
                {"event": RentalEvent.rented, "viol_num": context['viol'].viol_num,
                 "case_num": context['viol'].cases.first().case_num if
                    context['viol'].cases.exists() else None,
                 "bow_num": context['viol'].bows.first().bow_num if
                    context['viol'].bows.exists() else None,
                 "renter_num": context['user'].id, "notes": _createUserStamp(context['user'])})
            return render(request, 'renters/createAgreement.html', context)


class RentalAgreementForm(forms.ModelForm):
    contract = forms.FileField()

    def __init__(self, *args, **kwargs):
        super(RentalAgreementForm, self).__init__(*args, **kwargs)
        self.fields['rental_start'].required = True
        self.fields['rental_end'].required = True
        self.fields['event'].widget = HiddenInput()
        self.fields['contract'].required = False

    class Meta:
        model = RentalHistory
        fields = ('contract', 'notes', 'rental_start', 'rental_end', 'event')
        labels = {'event': '', 'contract': 'Rental Contract', }
        widgets = {
            'rental_start': forms.DateInput(format=('%Y-%m-%d'),
                                            attrs={'class': 'form-control',
                                                   'placeholder': 'Select a date',
                                                   'type': 'date'}),
            'rental_end': forms.DateInput(format=('%Y-%m-%d'),
                                          attrs={'class': 'form-control',
                                                 'placeholder': 'Select a date',
                                                 'type': 'date'}),
        }


class RentalCreateView(RentalViewBase, View):
    """Create Rental Agreement"""

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        context['viol'] = Viol.objects.get(pk=self.request.POST['viol_num'])
        context['user'] = User.objects.get(pk=self.request.POST['user_id'])
        return render(request, 'renters/createAgreement.html', context)


class RentalRenewView(RentalViewBase, FormView):
    """Renew Rental Agreement"""
    template_name = 'renters/rentOut.html'
    form_class = RentalAgreementForm
    model = RentalHistory

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        if self.kwargs['entry_num']:
            oldrental = RentalHistory.objects.get(pk=self.kwargs['entry_num'])
            context['oldrental'] = oldrental
            context['form'] = RentalAgreementForm(
                {"event": RentalEvent.renewed, "viol_num": oldrental.viol_num,
                 "case_num": oldrental.viol_num.cases.first().case_num if
                    oldrental.viol_num.cases.exists() else None,
                 "bow_num": oldrental.viol_num.bows.first().bow_num if
                    oldrental.viol_num.bows.exists() else None,
                 "renter_num": oldrental.renter_num.id})
            # context['form'] = RentalRenewForm({'viol_num': oldrental.viol_num,
            #                                    'renter_num': oldrental.renter_num})
            context['form'].fields['rental_end'].label = "New Rental Start"
            context['form'].fields['rental_end'].label = "New Rental End"
        return render(request, 'renters/renew.html', context)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        oldrental = RentalHistory.objects.get(pk=self.kwargs['entry_num'])
        context['oldrental'] = oldrental
        form = RentalAgreementForm(request.POST or None)
        context['form'] = form
        context['viol'] = Viol.objects.get(pk=oldrental.viol_num.viol_num)
        context['user'] = User.objects.get(pk=oldrental.renter_num.pk)
        return render(request, 'renters/createAgreement.html', context)


class RentalReturnForm(forms.ModelForm):
    class Meta:
        model = RentalHistory
        fields = ('rental_end', 'notes')
        labels = {'rental_end': 'Date Returned', }
        widgets = {
            'rental_end': forms.DateInput(format=('%Y-%m-%d'),
                                          attrs={'class': 'form-control',
                                                 'placeholder': 'Select a date',
                                                 'type': 'date'}),
        }


class RentalReturnView(RentalViewBase, FormView):
    """Return Rental """
    template_name = './return.html'
    form_class = RentalReturnForm
    model = RentalHistory

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        if self.kwargs['entry_num']:
            oldrental = RentalHistory.objects.get(pk=self.kwargs['entry_num'])
            context['oldrental'] = oldrental
            form = RentalReturnForm(initial={"rental_end": datetime.date.today})
            context['form'] = form
        return render(request, 'renters/return.html', context)

    def form_valid(self, form):
        oldrental = RentalHistory.objects.get(pk=self.kwargs['entry_num'])

        viol = Viol.objects.get(pk=oldrental.viol_num.pk)
        viol.renter = None
        viol.status = RentalState.available
        viol.save()
        history = RentalHistory.objects.create(
            renter_num=oldrental.renter_num,
            viol_num=oldrental.viol_num,
            bow_num=oldrental.bow_num,
            case_num=oldrental.case_num,
            event=RentalEvent.returned,
            notes=form.cleaned_data['notes'])
        history.save()

        messages.add_message(self.request, messages.SUCCESS, 'Rental Returned!')
        return super().form_valid(form)

    def get_success_url(self):
        oldrental = RentalHistory.objects.get(pk=self.kwargs['entry_num'])

        return reverse('viol-detail', args=[oldrental.viol_num.pk])


class RentalSubmitView(RentalViewBase, View):
    """Create Rental Agreement"""

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        form = RentalAgreementForm(request.POST or None)
        context['form'] = form
        context['RentalEvent'] = RentalEvent
        context['RentalState'] = RentalState
        if not form.is_valid():
            messages.add_message(self.request, messages.ERROR, 'Please Enter info.')
            return render(request, 'renters/rentOut.html', context)
        else:
            if self.request.POST.get('viol_num'):
                viol = Viol.objects.get(pk=self.request.POST['viol_num'])
                user = User.objects.get(pk=self.request.POST['user_id'])
                viol.renter = user
                viol.status = RentalState.rented
                viol.save()
                history = RentalHistory.objects.create(
                    event=form.cleaned_data['event'],
                    notes=form.cleaned_data['notes'],
                    viol_num=viol,
                    renter_num=user,
                    rental_start=form.cleaned_data['rental_start'],
                    rental_end=form.cleaned_data['rental_end'],
                    case_num=viol.cases.first() if viol.cases.exists() else None,
                    bow_num=viol.bows.first() if viol.bows.exists() else None)

                if request.FILES and request.FILES["contract"]:
                    contract = RentalContract.objects.create(document=request.FILES["contract"])
                    history.contract_scan = contract
                    contract.save()

                history.save()
                messages.add_message(self.request, messages.SUCCESS, 'Rented!')

            return redirect(reverse('viol-detail', args=[self.request.POST.get('viol_num')]))


class RentalContractForm(forms.ModelForm):
    rental_entry_num = forms.HiddenInput()

    class Meta:
        model = RentalContract
        fields = ('document',)


class UploadRentalView(RentalViewBase, CreateView):
    model = RentalContract
    form_class = RentalContractForm
    success_url = reverse_lazy('list-renters')
    template_name = 'renters/upload_contract.html'

    # def get_initial(self):
    #     initial = super().get_initial()
    #     initial['entry_num'] = self.kwargs['entry_num']
    #     return initial

    # def get_context_data(self, **kwargs):
    #     kwargs.setdefault('entry_num', self.kwargs['entry_num'])
    #     return kwargs

    def form_valid(self, form):
        rh = RentalHistory.objects.get(pk=self.kwargs['entry_num'])
        response = super().form_valid(form)
        form.instance.rental.set([rh])
        if rh.viol_num.pk:
            return redirect(reverse('viol-detail', args=[rh.viol_num.pk]))
        return redirect(reverse('list-viols'))

    def get_context_data(self, **kwargs):
        if 'form' not in kwargs:
            kwargs['form'] = self.get_form()
        return super().get_context_data(**kwargs)


class UpdateRentalView(RentalViewBase, SuccessMessageMixin, UpdateView):
    model = RentalHistory
    form_class = RentalHistoryForm
    template_name = 'renters/updateRental.html'
    success_message = "Rental was updated successfully"

    def get_success_url(self, **kwargs) -> str:
        return reverse('rental-detail', args=[self.object.entry_num])


class ListRentersView(RentalViewBase, ListView):
    template_name = 'renters/list.html'
    filterSessionName = 'renter_filter'

    def getFilter(self, **kwargs):
        filter = {}
        if self.request.GET.get('status') is None:
            filter = self.request.session.get(self.filterSessionName, None)
            if filter is None:
                filter = {'status': 'all'}
        else:
            filter = {'status': self.request.GET.get('status') or 'all'}

        return filter

    def get_context_data(self, **kwargs):
        context = super(ListRentersView, self).get_context_data(**kwargs)
        context['filter'] = self.getFilter()
        return context

    def get_queryset(self, *args: Any, **kwargs: Any):
        queryset = []
        filter = self.getFilter()
        self.request.session[self.filterSessionName] = filter
        if filter['status'] == 'active':
            queryset = User.objects.filter(
                (Q(rentalhistory__event=RentalEvent.rented)
                 | Q(rentalhistory__event=RentalEvent.renewed))
                & Q(pk=F('rentalhistory__viol_num__renter')))
        elif filter['status'] == 'inactive':
            queryset = User.objects.filter((Q(
                rentalhistory__event=RentalEvent.returned)) & (Q(
                    rentalhistory__viol_num__renter__isnull=True) | ~Q(
                        pk=F('rentalhistory__viol_num__renter')))
            )
        else:
            queryset = User.objects.filter(
                (Q(rentalhistory__event=RentalEvent.rented) | Q(
                    rentalhistory__event=RentalEvent.renewed)))
        
        print('sql', queryset.query)
        return queryset.annotate(num_rentals=Count('rentalhistory')).annotate(
            rental_end_date=Max('rentalhistory__rental_end', filter=Q(
                pk=F('rentalhistory__viol_num__renter'))))


class ListCustodianView(RentalViewBase, ListView):

    def get_queryset(self, *args: Any, **kwargs: Any):
        queryset = (Viol.objects.all().values('storer__username', 'storer__first_name',
                                              'storer__last_name',
                                              'storer__address_state', 'storer__address_city',
                                              'storer').annotate(total=Count('storer')).order_by(
                                                  'storer__last_name'))

        return queryset

    template_name = 'custodians/list.html'


class CustodianDetailView(RentalViewBase, DetailView):
    model = User
    template_name = 'custodians/detail.html'

    def get_context_data(self, **kwargs):
        context = super(CustodianDetailView, self).get_context_data(**kwargs)
        context['viols'] = Viol.objects.filter(storer=self.kwargs['pk'])
        return context


class RentersDetailView(RentalViewBase, DetailView):
    model = RentalHistory
    template_name = 'renters/detail.html'

    def get_context_data(self, **kwargs):
        context = super(RentersDetailView, self).get_context_data(**kwargs)
        rental = RentalHistory.objects.get(pk=self.kwargs['pk'])
        context['history'] = (RentalHistory.objects.all()
                              .filter(Q(event=RentalEvent.rented)
                              | Q(event=RentalEvent.renewed) | Q(event=RentalEvent.returned))
                              .filter(
                                  Q(renter_num=rental.renter_num)
                                  & Q(viol_num=rental.viol_num))
                              )
        return context


class SoftDeleteView(RentalViewBase, View):

    def returnUrl(self, className):
        return {
            'Viol': 'list-viols',
            'Bow': 'list-bowss',
            'Case': 'list-cases',
            'WaitingList': 'list-waiting'
        }.get(className, 'list-viols')

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        try:
            mymodel = apps.get_model('rental_viols', self.kwargs['class'])
            obj = mymodel.objects.get(pk=self.kwargs['pk'])

            obj.status = RentalState.deleted
            obj.save()

        except RentalHistory.DoesNotExist:
            raise Http404("No MyModel matches the given query.")

        return redirect(reverse(self.returnUrl(self.kwargs['class'])))


class ViewUserInfo(RentalViewBase, DetailView):
    model = User
    template_name = 'renters/userDetail.html'

    def get_context_data(self, **kwargs):

        context = super(ViewUserInfo, self).get_context_data(**kwargs)
        context['history'] = (RentalHistory.objects.all().filter(
                              Q(event=RentalEvent.rented)
                              | Q(event=RentalEvent.renewed)
                              | Q(event=RentalEvent.returned)).filter(
                                  renter_num=self.kwargs['pk'])).annotate(
                                      rental_end_date=Max('rental_end'))
        # .annotate(rental_end_date=Max('rental_end')
        return context


class UserSearchView(RentalViewBase, View):
    """Filter list of users """
    @csrf_exempt
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        url_parameter = request.GET.get("q")
        context = {}
        if url_parameter:
            users = User.objects.filter(Q(first_name__icontains=url_parameter)
                                        | Q(last_name__icontains=url_parameter))
        else:
            users = User.objects.all()

        context["users"] = users
        if request.is_ajax():
            html = render_to_string(
                template_name="users/user-results-partial.html", context={"users": users}
            )
            data_dict = {"html_from_view": html}
            return JsonResponse(data=data_dict, safe=False)

        return render(request, "artists.html", context=context)
