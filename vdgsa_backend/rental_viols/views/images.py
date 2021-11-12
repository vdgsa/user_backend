import datetime
from functools import cached_property
from typing import Any, Dict, Iterable, Literal
import mimetypes
from django import forms
from django.apps import apps
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.storage import FileSystemStorage
from django.db.models import Count, F, Max, Q
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


class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('image_file_name', 'caption')


class RentalContractView(RentalViewBase, View):

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        try:
            context = {"picture_id": self.kwargs['entry_num']}
            contract = RentalContract.objects.get(entry_num=self.kwargs['entry_num'])
            file_mime, encoding = mimetypes.guess_type(contract.document.name)
            return HttpResponse(contract.document.open(mode='rb'), content_type=file_mime)
        except IOError:
            red = Image.new('RGBA', (1, 1), (255, 0, 0, 0))
            response = HttpResponse(content_type="image/jpeg")
            red.save(response, "JPEG")
            return response


class ImageView(RentalViewBase, View):

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        try:
            context = {"picture_id": self.kwargs['picture_id']}
            image = Image.objects.get(picture_id=self.kwargs['picture_id'])
            file_mime, encoding = mimetypes.guess_type(image.image_file_name.name)
            return HttpResponse(image.image_file_name.open(mode='rb'), content_type=file_mime)
        except IOError:
            red = Image.new('RGBA', (1, 1), (255, 0, 0, 0))
            response = HttpResponse(content_type="image/jpeg")
            red.save(response, "JPEG")
            return response


class DeleteImageView(RentalViewBase, View):

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {"picture_id": self.kwargs['picture_id']}
        image = Image.objects.get(picture_id=self.kwargs['picture_id'])
        type = image.type
        vbc_number = image.vbc_number
        image.delete()
        messages.add_message(self.request, messages.SUCCESS, 'Image Deleted')
        return redirect(reverse(type + '-detail', args=[vbc_number]))


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
