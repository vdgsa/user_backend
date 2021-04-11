import datetime
from functools import cached_property
from typing import Any, Dict, Iterable, Literal
from django import forms
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.apps import apps
from django.forms.widgets import DateTimeBaseInput
from django.http import response
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.http import Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.urls.base import reverse, reverse_lazy
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
    Bow, Case, RentalEvent, RentalHistory, Viol, WaitingList, RentalEvent, ViolSize,
    RentalContract, Image, ItemType
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
            print(rental)
            if self.request.POST.get('bow_num'):
                bow = Bow.objects.get(pk=self.request.POST['bow_num'])
                bow.status = RentalEvent.attached
                bow.save()
                rental.bow_num = bow
                rental.save()
                messages.add_message(self.request, messages.SUCCESS, 'Bow attached!')

            if self.request.POST.get('case_num'):
                case = Case.objects.get(pk=self.request.POST['case_num'])
                case.status = RentalEvent.attached
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
            context['waiting'] = WaitingList.objects.all().filter(viol_num=context['viol'])
        return render(request, 'renters/rentOut.html', context)


class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('image_file_name', 'caption')


class AttachImageView(RentalViewBase, FormView):
    """Attach Image"""
    template_name = 'upload_image.html'
    form_class = ImageForm
    model = Image

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {"type": self.kwargs['to'],
                   "vbc_number": self.kwargs['pk']}
        if self.kwargs['to'] == 'viol':
            context['viol'] = Viol.objects.get(pk=self.kwargs['pk'])
        if self.kwargs['to'] == 'bow':
            context['bow'] = Bow.objects.get(pk=self.kwargs['pk'])
        if self.kwargs['to'] == 'case':
            context['case'] = Case.objects.get(pk=self.kwargs['pk'])
        context['form'] = ImageForm(
            {})

        return render(request, 'upload_image.html', context)

    def form_valid(self, form):
        image = Image.objects.create(
            image_file_name=form.cleaned_data['image_file_name'],
            caption=form.cleaned_data['caption'],
            vbc_number=self.request.POST.get('vbc_number'),
            type=self.request.POST.get('type'))
        image.save()

        messages.add_message(self.request, messages.SUCCESS, 'Image Saved!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(self.request.POST.get('type') + '-detail',
                       args=[self.request.POST.get('vbc_number')])

    # def post(self, request: HttpRequest, *args: Any, **kwargs: Any):
    #     context = {}

    #     if self.request.POST.get('viol_num'):
    #         context['viol'] = Viol.objects.get(pk=self.request.POST['viol_num'])
    #         context['user'] = User.objects.get(pk=self.request.POST['user_id'])
    #     return render(request, 'renters/createAgreement.html', context)


class RentalHistoryForm(forms.ModelForm):
    class Meta:
        model = RentalHistory
        fields = ('notes', 'rental_start', 'rental_end')

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
        if self.request.POST.get('viol_num'):
            context['viol'] = Viol.objects.get(pk=self.request.POST['viol_num'])
            context['user'] = User.objects.get(pk=self.request.POST['user_id'])
        return render(request, 'renters/createAgreement.html', context)


class RentalRenewView(RentalViewBase, FormView):
    """Renew Rental Agreement"""
    template_name = 'renters/rentOut.html'
    form_class = RentalHistoryForm
    model = RentalHistory

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        if self.kwargs['entry_num']:
            oldrental = RentalHistory.objects.get(pk=self.kwargs['entry_num'])
            print('oldrental:', oldrental)
            context['form'] = RentalHistoryForm(
                {"event": RentalEvent.rented, "viol_num": oldrental.viol_num,
                 "case_num": oldrental.case_num,
                 "bow_num": oldrental.bow_num,
                 "renter_num": oldrental.renter_num})

        return render(request, 'renters/rentOut.html', context)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        if self.request.POST.get('viol_num'):
            context['viol'] = Viol.objects.get(pk=self.request.POST['viol_num'])
            context['user'] = User.objects.get(pk=self.request.POST['user_id'])
        return render(request, 'renters/createAgreement.html', context)


class RetireViolView(RentalViewBase, FormView):
    """Renew Rental Agreement"""
    template_name = './retireMulti.html'
    form_class = RentalHistoryForm
    model = RentalHistory

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        viol = Viol.objects.get(pk=self.kwargs['viol_num'])
        print(viol)
        context['form'] = RentalHistoryForm(
            {"event": RentalEvent.retired, "viol_num": viol.viol_num,
                "case_num": viol.cases.first().case_num if viol.cases.exists() else None,
                "bow_num": viol.bows.first().bow_num if viol.bows.exists() else None})

        return render(request, 'viols/retire.html', context)

    def form_valid(self, form):
        viol = Viol.objects.get(pk=self.request.POST['viol_num'])
        viol.status = RentalEvent.retired
        viol.save()
        history = RentalHistory.objects.create(
            renter_num=form.cleaned_data['renter_num'],
            viol_num=form.cleaned_data['viol_num'],
            case_num=form.cleaned_data['case_num'],
            bow_num=form.cleaned_data['bow_num'],
            event=RentalEvent.retired,
            notes=form.cleaned_data['notes'])
        history.save()

        messages.add_message(self.request, messages.SUCCESS, 'Rental Returned!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('viol-detail', args=[self.request.POST.get('viol_num')])

    # def post(self, request: HttpRequest, *args: Any, **kwargs: Any):
        # context = {}
        # if self.request.POST.get('viol_num'):
        #     viol = Viol.objects.get(pk=self.request.POST['viol_num'])
        #     viol.status = RentalEvent.retired
        #     history = RentalHistoryForm(
        #         {"event": RentalEvent.retired, "viol_num": viol.viol_num,
        #          "case_num": viol.cases.first().case_num if viol.cases.exists() else None,
        #          "bow_num": viol.bows.first().bow_num if viol.bows.exists() else None})
        #     history.save()
        #     viol.save()
        # return redirect(reverse('viol-detail', args=[self.request.POST.get('viol_num')]))


class RentalReturnView(RentalViewBase, FormView):
    """Return Rental """
    template_name = './return.html'
    form_class = RentalHistoryForm
    model = RentalHistory

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        if self.kwargs['entry_num']:
            oldrental = RentalHistory.objects.get(pk=self.kwargs['entry_num'])
            print('oldrental:', oldrental)
            context['form'] = RentalHistoryForm(
                {"event": RentalEvent.rented, "viol_num": oldrental.viol_num,
                 "case_num": oldrental.case_num,
                 "bow_num": oldrental.bow_num,
                 "renter_num": oldrental.renter_num})

        return render(request, 'renters/rentOut.html', context)


class RentalSubmitView(RentalViewBase, View):
    """Create Rental Agreement"""

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any):
        if self.request.POST.get('viol_num'):
            viol = Viol.objects.get(pk=self.request.POST['viol_num'])
            user = User.objects.get(pk=self.request.POST['user_id'])
            viol.renter = user
            viol.save()

            history = RentalHistoryForm(
                {"event": RentalEvent.rented, "viol_num": viol.viol_num,
                 "case_num": viol.cases.first().case_num if viol.cases.exists() else None,
                 "bow_num": viol.bows.first().bow_num if viol.bows.exists() else None,
                 "renter_num": user.id})
            history.save()
            messages.add_message(self.request, messages.SUCCESS, 'Rented!')
        return redirect(reverse('list-renters'))

# TODO: Rental Actions
# RentalContract scan of signed contract


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
        print('form_valid ', self.kwargs['entry_num'])
        rh = RentalHistory.objects.get(pk=self.kwargs['entry_num'])
        response = super().form_valid(form)
        form.instance.rental.set([rh])
        return response

    def get_context_data(self, **kwargs):
        if 'form' not in kwargs:
            kwargs['form'] = self.get_form()
        return super().get_context_data(**kwargs)

# COULDN'T GET THIS TO WORK.
# class ViewRentalAgreement (RentalViewBase, View):
#     def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
#         rc = RentalContract.objects.get(pk=self.kwargs['entry_num'])
#         print(rc.document)
#         fs = FileSystemStorage()
#         if fs.exists(rc.document):
#             with fs.open(rc.document) as pdf:
#                 response = HttpResponse(pdf, content_type='application/pdf')
#                 # user will be prompted display the PDF in the browser
#                 response['Content-Disposition'] = 'inline; filename="mypdf.pdf"'
#                 return response
#         else:
#             return HttpResponseNotFound("Rental agreement: could not be found!")


class UpdateRentalView(RentalViewBase, SuccessMessageMixin, UpdateView):
    model = RentalHistory
    form_class = RentalHistoryForm
    template_name = 'renters/updateRental.html'
    success_message = "Rental was updated successfully"

    def get_success_url(self, **kwargs) -> str:
        return reverse('rental-detail', args=[self.object.entry_num])


class ReserveViolModelForm(forms.ModelForm):
    class Meta:
        model = WaitingList
        fields = [
            'entry_num',
            'viol_num',
            'renter_num',
            'date_req',
            'size'
        ]


class ReserveViolView(RentalViewBase, FormView):
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
        if self.request.GET.get('user_id'):
            renter = User.objects.get(pk=self.request.GET.get('user_id'))
            initial['renter_num'] = renter
        return initial

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
        waitinglist = WaitingList.objects.create(
            renter_num=form.cleaned_data['renter_num'],
            viol_num=form.cleaned_data['viol_num'],
            date_req=form.cleaned_data['date_req'],
            size=form.cleaned_data['size'])
        waitinglist.save()
        history = RentalHistoryForm(
            {"event": RentalEvent.reserved,
                "viol_num": form.cleaned_data['viol_num'].viol_num,
                "renter_num": form.cleaned_data['renter_num'].id})
        history.save()
        messages.add_message(self.request, messages.SUCCESS, 'Waiting List created!')
        return super().form_valid(form)


class ViolUpdateForm(forms.Form):
    viol_num = forms.IntegerField()
    user_id = forms.IntegerField()


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
        elif self.getFilter() == 'retired':
            queryset = Viol.objects.get_retired()
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
        queryset = WaitingList.objects.all()
        print(queryset)
        return queryset

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
        print('context[viol] ', context['viol'].pk)
        context['now'] = timezone.now()

        context['images'] = Image.objects.get_images('viol', context['viol'].pk)

        print('context[images] ', context['images'])
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
