from functools import cached_property
from typing import Any, Dict, Iterable, Literal
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.apps import apps
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseRedirect
from django.http import Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.urls.base import reverse
from django.utils.http import urlencode
from django.utils import timezone
from django.views.generic.base import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.generic.list import ListView

from vdgsa_backend.accounts.models import User
from vdgsa_backend.rental_viols.managers.InstrumentManager import AccessoryManager, ViolManager
from vdgsa_backend.rental_viols.managers.RentalItemBaseManager import (
    RentalItemBaseManager, RentalEvent)
from vdgsa_backend.rental_viols.models import (
    Bow, Case, RentalEvent, RentalHistory, Viol, WaitingList, RentalEvent
)
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


# Actions
# Attach to viol | Detach from viol - Bow, Case
# Retire | Un-retire - Bow, Case, Viol
# Rent out | Reserve | Renew rental | Return from rental | Make available (un-retire?) - Viol
# Add to waiting list | Cancel waiting list


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
            context['viols'] = Viol.objects.get_available(size)

        return render(
            self.request,
            'viols/attatchToViol.html', context
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any):
        if self.request.POST.get('viol_num'):
            viol = Viol.objects.get(pk=self.request.POST.get('viol_num'))
            if self.request.POST.get('bow_num'):
                bow = Bow.objects.get(pk=self.request.POST['bow_num'])
                bow.status = RentalEvent.attached
                bow.save()
                viol.bows.add(bow)
                history = RentalHistoryForm(
                    {"event": RentalEvent.attached, "viol_num": viol.viol_num,
                     "bow_num": bow.bow_num})
                history.save()
                messages.add_message(self.request, messages.SUCCESS, 'Bow attached!')

            if self.request.POST.get('case_num'):
                case = Case.objects.get(pk=self.request.POST['case_num'])
                case.status = RentalEvent.attached
                case.save()
                viol.cases.add(case)
                history = RentalHistoryForm(
                    {"event": RentalEvent.attached,
                     "viol_num": viol.viol_num,
                     "case_num": case.case_num})
                history.save()
                messages.add_message(self.request, messages.SUCCESS, 'Case attached!')

        return redirect(reverse('viol-detail', args=[self.request.POST.get('viol_num')]))


class DetachFromViolView(RentalViewBase, View):
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        if self.request.GET.get('viol_num'):
            viol = Viol.objects.get(pk=self.request.GET['viol_num'])
            if self.request.GET.get('bow_num'):
                bow = Bow.objects.get(pk=self.request.GET['bow_num'])
                bow.viol_num = None
                bow.status = RentalEvent.detached
                bow.save()
                history = RentalHistoryForm(
                    {"event": RentalEvent.detached, "viol_num": viol.viol_num, "bow_num":
                     bow.bow_num})
                history.save()
                messages.add_message(self.request, messages.SUCCESS, 'Bow attached!')

            if self.request.GET.get('case_num'):
                case = Case.objects.get(pk=self.request.GET['case_num'])
                case.viol_num = None
                case.status = RentalEvent.detached
                case.save()
                history = RentalHistoryForm(
                    {"event": RentalEvent.detached, "viol_num": viol.viol_num,
                     "case_num": case.case_num})
                history.save()
                messages.add_message(self.request, messages.SUCCESS, 'Case attached!')

        return redirect(reverse('viol-detail', args=[self.request.GET['viol_num']]))


class RentalHomeView(RentalViewBase, TemplateView):
    template_name = 'home.html'


class RentOutView(RentalViewBase, View):
    """get to select Rental User"""

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        if self.request.GET.get('viol_num'):
            context['viol'] = Viol.objects.get(pk=self.request.GET.get('viol_num'))
            context['users'] = User.objects.all()
        return render(request, 'renters/rentOut.html', context)


class RentalCreateView(RentalViewBase, View):
    """Create Rental Agreement"""

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        if self.request.POST.get('viol_num'):
            context['viol'] = Viol.objects.get(pk=self.request.POST['viol_num'])
            context['user'] = User.objects.get(pk=self.request.POST['user_id'])

        return render(request, 'renters/createAgreement.html', context)


class RentalSubmitView(RentalViewBase, View):
    """Create Rental Agreement"""

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any):

        if self.request.POST.get('viol_num'):
            viol = Viol.objects.get(pk=self.request.POST['viol_num'])
            user = User.objects.get(pk=self.request.POST['user_id'])

            print('user', user.id)
            viol.renter = user
            viol.save()
            # print('viol.cases.all()[0].case_num', viol.cases.all()[0].case_num)
            ###

            history = RentalHistoryForm(
                {"event": RentalEvent.rented, "viol_num": viol.viol_num,
                 "case_num": viol.cases.first().case_num if viol.cases.exists() else None,
                 "bow_num": viol.bows.first().bow_num if viol.bows.exists() else None,
                 "renter_num": user.id})
            history.save()
            print(history)
            messages.add_message(self.request, messages.SUCCESS, 'Rented!')

        return redirect(reverse('list-renters'))

# TODO: Rental Actions
# RentalContract scan of signed contract
# Return Rental
# Renew Rental
# Make Available (not sure what happens in DB)

# LIST VIEWS


class ViolsMultiListView(RentalViewBase, ListView):
    template_name = 'viols/list.html'
    filterSessionName = 'rental_filter'
    filter = None

    def getFilter(self, **kwargs):
        filter = self.request.GET.get('filter')
        if filter is None:
            filter = self.request.session.get(self.filterSessionName, None)
        self.request.session[self.filterSessionName] = filter
        return filter

    def get_context_data(self, **kwargs):
        context = super(ViolsMultiListView, self).get_context_data(**kwargs)
        context['filter'] = self.getFilter()
        return context

    def get_queryset(self, *args: Any, **kwargs: Any):
        print('getFilter()', self.getFilter())
        if self.getFilter() == 'available':
            queryset = Viol.objects.get_available()
        elif self.getFilter() == 'rented':
            queryset = Viol.objects.get_rented()
        else:
            queryset = Viol.objects.all()
        return queryset


class ListBowsView(RentalViewBase, ListView):
    model = Bow
    template_name = 'bows/list_bows.html'


class ListCasesView(RentalViewBase, ListView):
    model = Case
    template_name = 'cases/list.html'


class ListRentersView(RentalViewBase, ListView):

    def get_queryset(self, *args: Any, **kwargs: Any):

        queryset = RentalHistory.objects.all().filter(event=RentalEvent.rented)
        print(queryset)
        return queryset

    template_name = 'renters/list.html'


class ListWaitingView(RentalViewBase, ListView):
    def get_queryset(self, *args: Any, **kwargs: Any):
        return WaitingList.objects.all()

    template_name = 'waitinglist.html'

# CRUD


class RentalHistoryForm(forms.ModelForm):
    class Meta:
        model = RentalHistory
        fields = [
            'entry_num',
            'viol_num',
            'bow_num',
            'case_num',
            'renter_num',
            'event',
            'notes',
            'rental_start',
            'rental_end',
            'contract_scan',
        ]


class BowForm(forms.ModelForm):
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


class AddBowView(RentalViewBase, SuccessMessageMixin, CreateView):
    model = Bow
    form_class = BowForm
    success_message = "%(size)s bow was created successfully"
    template_name = 'bows/add_bow.html'


class UpdateBowView(RentalViewBase, SuccessMessageMixin, UpdateView):
    model = Bow
    form_class = BowForm
    template_name = 'bows/update.html'
    success_message = "%(size)s bow was created successfully"

    def get_success_url(self, **kwargs) -> str:
        print(self.object.bow_num)
        return reverse('list-bows')


class BowDetailView(RentalViewBase, DetailView):
    model = Bow
    template_name = 'bows/bow_detail.html'


class CaseForm(forms.ModelForm):
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


class AddCaseView(RentalViewBase, SuccessMessageMixin, CreateView):
    model = Case
    form_class = CaseForm
    success_message = "%(size)s case was created successfully"
    template_name = 'cases/add.html'


class UpdateCaseView(RentalViewBase, SuccessMessageMixin, UpdateView):
    model = Case
    form_class = CaseForm
    template_name = 'cases/update.html'

    success_url = 'cases/'
    success_message = "%(size)s case was updated successfully"

    def get_success_url(self, **kwargs) -> str:
        print(self.object.case_num)
        return reverse('list-cases')


class CaseDetailView(RentalViewBase, DetailView):
    model = Case
    template_name = 'cases/detail.html'


class ViolForm(forms.ModelForm):
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


class AddViolView(RentalViewBase, SuccessMessageMixin, CreateView):
    model = Viol
    form_class = ViolForm
    template_name = 'viols/add.html'
    success_message = "%(size)s viol was created successfully"


class UpdateViolView(RentalViewBase, SuccessMessageMixin, UpdateView):
    model = Viol
    form_class = ViolForm
    template_name = 'viols/update.html'
    success_message = "%(size)s viol was updated successfully"

    def get_success_url(self, **kwargs) -> str:
        print(self.object.viol_num)
        return reverse('list-viols')


class ViolDetailView(RentalViewBase, DetailView):
    model = Viol
    template_name = 'viols/detail.html'

    def get_context_data(self, **kwargs):
        context = super(ViolDetailView, self).get_context_data(**kwargs)
        print('context', context)
        context['now'] = timezone.now()
        return context


class RentersDetailView(RentalViewBase, DetailView):
    model = RentalHistory
    template_name = 'renters/detail.html'


class SoftDeleteView(RentalViewBase, View):

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        print()
        print(self.kwargs['class'])
        print(self.kwargs['pk'])

        try:
            mymodel = apps.get_model('rental_viols', self.kwargs['class'])
            obj = mymodel.objects.get(pk=self.kwargs['pk'])

            obj.status = RentalEvent.deleted
            obj.save()

        except RentalHistory.DoesNotExist:
            raise Http404("No MyModel matches the given query.")

        print(obj)
        # return HttpResponseRedirect(self.request.path_info)
        return redirect(reverse('list-renters'))
