from typing import Any, Dict, cast

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db import models
from django.db.models.base import Q
from django.db.models.functions import Upper
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.functional import cached_property
from django.views.generic import View

from vdgsa_backend.accounts.models import MembershipType, User
from vdgsa_backend.accounts.views.permissions import is_active_member


class CommercialMemberType(models.TextChoices):
    INSTRUMENT_MAKER = "I", "Instrument Maker"
    BOW_MAKER = "B", "Bow Maker"
    REPAIRER = "R", "Repairer"
    PUBLISHER = "P", "Publisher"
    OTHER = "O", "Other"


class TeachingMemberType(models.TextChoices):
    IN_PERSON = "I", "Lessons in Person"
    REMOTE = "R", "Remote Lessons"
    # CIRCUIT = 'C', 'Circuit Rider'


class DirectorySearchForm(forms.Form):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

    searchtext = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Search Text for any field'}), label=False, required=False)

    isAdvancedSearch = forms.BooleanField(
        widget=forms.HiddenInput, required=False, initial=False, label=False
    )
    first_name = forms.CharField(label="First", required=False)
    last_name = forms.CharField(label="Last", required=False)
    address_city = forms.CharField(label="City", required=False)
    address_state = forms.CharField(
        label="State/Province",
        required=False,
        widget=forms.Select(
            choices=[
                (genre, genre)
                for genre in list(
                    User.objects.distinct()
                    .order_by(Upper("address_state"))
                    .values_list(Upper("address_state"), flat=True)
                )
            ]
        ),
    )
    address_country = forms.CharField(label="Country", required=False)

    commercial_member_type = forms.MultipleChoiceField(
        label="Commercial Member",
        choices=CommercialMemberType.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    teaching_member_type = forms.MultipleChoiceField(
        label="Teaching Member",
        choices=TeachingMemberType.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    page = forms.IntegerField(widget=forms.HiddenInput, initial=1, label=False)

    def clean(self) -> Dict[str, Any]:
        result = super().clean()
        return result


class DirectoryMemberDetailView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "directory/memberDetail.html"

    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
        context = {}
        if self.kwargs["pk"]:
            context["member"] = self.getMember(self.kwargs["pk"])
        else:
            context["member"] = self.getMember(1)
        return render(self.request, self.template_name, context)

    def getMember(self, pk, **kwargs):
        q_objects = Q(pk=pk)
        q_objects &= Q(is_deceased=False) & Q(include_name_in_membership_directory=True)
        subscr_member = (
            Q(owned_subscription__membership_type=MembershipType.regular)
            | Q(owned_subscription__membership_type=MembershipType.student)
            | Q(owned_subscription__membership_type=MembershipType.international)
            | Q(owned_subscription__membership_type=MembershipType.complementary)
            | Q(owned_subscription__membership_type=MembershipType.organization)
        )

        subscr_member &= Q(owned_subscription__valid_until__gt=timezone.now())

        q_objects &= Q(
            subscr_member
            | Q(owned_subscription__membership_type=MembershipType.lifetime)
        )

        return User.objects.filter(q_objects).first()

    def test_func(self) -> bool:
        return is_active_member(self.request.user)


class DirectoryHomeView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "directory/home.html"

    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
        context = {}
        context["form"] = DirectorySearchForm()
        return render(self.request, self.template_name, context)

    def getFiltered(self, form, **kwargs):
        q_objects = Q(is_deceased=False)
        q_objects &= Q(include_name_in_membership_directory=True)

        subscr_member = (
            Q(owned_subscription__membership_type=MembershipType.regular)
            | Q(owned_subscription__membership_type=MembershipType.student)
            | Q(owned_subscription__membership_type=MembershipType.international)
            | Q(owned_subscription__membership_type=MembershipType.complementary)
            | Q(owned_subscription__membership_type=MembershipType.organization)
        )
        subscr_member &= Q(owned_subscription__valid_until__gt=timezone.now())

        q_objects &= Q(
            subscr_member
            | Q(owned_subscription__membership_type=MembershipType.lifetime)
        )

        if form.cleaned_data["searchtext"]:
            q_objects &= (
                Q(first_name__icontains=form.cleaned_data["searchtext"])
                | Q(last_name__icontains=form.cleaned_data["searchtext"])
                | Q(phone1__icontains=form.cleaned_data["searchtext"])
                | Q(other_commercial__icontains=form.cleaned_data["searchtext"])
                | Q(commercial_description__icontains=form.cleaned_data["searchtext"])
                | Q(teacher_description__icontains=form.cleaned_data["searchtext"])
                | (
                    Q(include_address_in_membership_directory=True)
                    & (
                        Q(address_city__icontains=form.cleaned_data["searchtext"])
                        | Q(address_line_1__icontains=form.cleaned_data["searchtext"])
                        | Q(address_line_2__icontains=form.cleaned_data["searchtext"])
                    )
                )
                | (
                    Q(include_email_in_membership_directory=True)
                    & Q(email__icontains=form.cleaned_data["searchtext"])
                )
            )

        if form.cleaned_data["isAdvancedSearch"]:
            if form.cleaned_data["first_name"]:
                q_objects &= Q(first_name__icontains=form.cleaned_data["first_name"])
            if form.cleaned_data["last_name"]:
                q_objects &= Q(last_name__icontains=form.cleaned_data["last_name"])
            if form.cleaned_data["address_city"]:
                q_objects &= Q(include_address_in_membership_directory=True) & Q(
                    address_city__icontains=form.cleaned_data["address_city"]
                )
            if form.cleaned_data["address_state"]:
                q_objects &= Q(include_address_in_membership_directory=True) & Q(
                    address_state__icontains=form.cleaned_data["address_state"]
                )
            if form.cleaned_data["address_country"]:
                q_objects &= Q(include_address_in_membership_directory=True) & Q(
                    address_country__icontains=form.cleaned_data["address_country"]
                )

            if len(form.cleaned_data["teaching_member_type"]) > 0:
                teaching_member = Q()
                if "I" in form.cleaned_data["teaching_member_type"]:
                    teaching_member |= Q(is_teacher=True)
                if "R" in form.cleaned_data["teaching_member_type"]:
                    teaching_member |= Q(is_remote_teacher=True)
                # if('C' in form.cleaned_data['teaching_member_type']):
                #     teaching_member |= Q(is_teacher=True)
                q_objects &= teaching_member

            if len(form.cleaned_data["commercial_member_type"]) > 0:
                commercial_member = Q()
                if "I" in form.cleaned_data["commercial_member_type"]:
                    commercial_member |= Q(is_instrument_maker=True)
                if "B" in form.cleaned_data["commercial_member_type"]:
                    commercial_member |= Q(is_bow_maker=True)
                if "R" in form.cleaned_data["commercial_member_type"]:
                    commercial_member |= Q(is_repairer=True)
                if "P" in form.cleaned_data["commercial_member_type"]:
                    commercial_member |= Q(is_publisher=True)
                if "O" in form.cleaned_data["commercial_member_type"]:
                    commercial_member |= Q(other_commercial__isnull=False) & ~Q(
                        other_commercial=""
                    )
                q_objects &= commercial_member

        return User.objects.filter(q_objects).order_by("last_name")

    def post(self, *args: Any, **kwargs: Any) -> HttpResponse:
        form = DirectorySearchForm(self.request.POST)
        context = {}
        context["form"] = form
        if not form.is_valid():
            return render(self.request, self.template_name)
        else:
            p = Paginator(self.getFiltered(form), 10 )
            context["results"] = p.get_page(form.cleaned_data["page"])
        return render(self.request, self.template_name, context)

    def test_func(self) -> bool:
        return is_active_member(self.request.user)
