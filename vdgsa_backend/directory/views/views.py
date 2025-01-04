from typing import Any, Dict, cast
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models.base import Q
from django.db import models
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls.base import reverse
from django.utils.functional import cached_property
from django.views.generic import View

from vdgsa_backend.accounts.models import MembershipType, User
from vdgsa_backend.accounts.views.permissions import is_requested_user_or_membership_secretary


class CommercialMemberType(models.TextChoices):
    INSTRUMENT_MAKER = 'I', 'Instrument Maker'
    BOW_MAKER = 'B', 'Bow Maker'
    REPAIRER = 'R', 'Repairer'
    PUBLISHER = 'P', 'Publisher'
    OTHER = 'O', 'Other'

class TeachingMemberType(models.TextChoices):
    IN_PERSON = 'I', 'Lessons in Person'
    REMOTE = 'R', 'Remote Lessons'
    CIRCUIT = 'C', 'Circuit Rider'


class DirectorySearchForm(forms.Form):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        # print('address_state',[(genre, genre) for genre in list(User.objects.distinct().order_by('address_state').values_list('address_state', flat=True))])
        # self.fields['address_state'].choices = [(genre, genre) for genre in list(User.objects.distinct().order_by('address_state').values_list('address_state', flat=True))]
        
    searchtext = forms.CharField(label='Search Text', required=False)

    isAdvancedSearch =  forms.BooleanField(widget=forms.HiddenInput, required=False, initial=False, label=False)
    first_name = forms.CharField(label='First', required=False)
    last_name = forms.CharField(label='Last', required=False)
    address_city = forms.CharField(label='City', required=False)
    address_state = forms.CharField(label='State/Province', required=False,widget=forms.Select(choices=[(genre, genre) for genre in list(User.objects.distinct().order_by('address_state').values_list('address_state', flat=True))]))
    address_country = forms.CharField(label='Country', required=False)

    commercial_member_type = forms.MultipleChoiceField(label='Commercial Member', choices=CommercialMemberType.choices, widget=forms.CheckboxSelectMultiple, required=False)
    teaching_member_type = forms.MultipleChoiceField(label='Teaching Member', choices=TeachingMemberType.choices, widget=forms.CheckboxSelectMultiple, required=False)


    def clean(self) -> Dict[str, Any]:
        result = super().clean()
        return result


class DirectoryHomeView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'directory/home.html'

    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
        print('DirectoryHomeView get')
        context = {}
        context['form'] = DirectorySearchForm()
        return render(self.request, self.template_name, context)

    def getFiltered(self, form,  **kwargs):

        print('getFiltered', form.cleaned_data['searchtext'])
        q_objects = Q(is_deceased=False)
        q_objects &= (Q(owned_subscription__membership_type=MembershipType.lifetime)
                    | Q(owned_subscription__membership_type=MembershipType.complementary)
                    | Q(owned_subscription__membership_type=MembershipType.organization)
                    | Q(owned_subscription__membership_type=MembershipType.regular)
                    | Q(owned_subscription__membership_type=MembershipType.student)
                    | Q(owned_subscription__membership_type=MembershipType.international))
        
        if(form.cleaned_data['searchtext']):
            q_objects &= ( Q(first_name__icontains=form.cleaned_data['searchtext'])
                     | Q(last_name__icontains=form.cleaned_data['searchtext'])
                     | Q(address_city__icontains=form.cleaned_data['searchtext'])
                     | Q(address_line_1__icontains=form.cleaned_data['searchtext'])
                     | Q(address_line_2__icontains=form.cleaned_data['searchtext'])
                    )

        if(form.cleaned_data['isAdvancedSearch']):
            if(form.cleaned_data['first_name'] != '' & form.cleaned_data['first_name'] != None):
                q_objects &= Q(first_name__icontains=form.cleaned_data['first_name'])
            if(form.cleaned_data['last_name'] != '' & form.cleaned_data['last_name'] != None):
                q_objects &= Q(last_name__icontains=form.cleaned_data['last_name'])
            if(form.cleaned_data['address_city'] != '' & form.cleaned_data['address_city'] != None):
                q_objects &= Q(address_city__icontains=form.cleaned_data['address_city'])
            if(form.cleaned_data['address_state'] != '' & form.cleaned_data['address_state'] != None):
                q_objects &= Q(address_state__icontains=form.cleaned_data['address_state'])
            if(form.cleaned_data['address_country'] != '' & form.cleaned_data['address_country'] != None):
                q_objects &= Q(address_country__icontains=form.cleaned_data['address_country'] )

            # if(form.cleaned_data['teaching_member_type'] != '' & form.cleaned_data['teaching_member_type'] != None):
            #     q_objects &= Q(teacher_description__icontains=form.cleaned_data['teacher_description'])

            # if(form.cleaned_data['teacher_description']!= '' & form.cleaned_data['teacher_description'] != None):
            #     q_objects &= Q(commercial_member_type__icontains=form.cleaned_data['searchtext)

        return User.objects.filter(q_objects).order_by('last_name')


    def post(self, *args: Any, **kwargs: Any) -> HttpResponse:
        if 'user_pk' in self.request.POST:
            self.requested_user = get_object_or_404(User, pk=self.request.POST['user_pk'])
        else:
            self.requested_user = cast(User, self.request.user)

        form = DirectorySearchForm(self.request.POST)
        context = {}
        context['form'] = form

        if not form.is_valid():
            print(form.errors)
        else:
            context['results'] = self.getFiltered(form)
            # include_name_in_membership_directory = models.BooleanField(default=True)
            # include_email_in_membership_directory = models.BooleanField(default=True)
            # include_address_in_membership_directory = models.BooleanField(default=True)
            # include_phone_in_membership_directory = models.BooleanField(default=True)

        return render(self.request, self.template_name, context)

    def test_func(self) -> bool:
        return is_requested_user_or_membership_secretary(self.requested_user, self.request)
    
    @cached_property
    def requested_user(self) -> User:
        return cast(User, self.request.user)





# class ViewUserInfo(RentalViewBase, DetailView):
#     model = User
#     template_name = 'renters/userDetail.html'

#     def get_context_data(self, **kwargs):

#         context = super(ViewUserInfo, self).get_context_data(**kwargs)
#         context['history'] = (RentalHistory.objects.all().filter(
#                               Q(event=RentalEvent.rented)
#                               | Q(event=RentalEvent.renewed)
#                               | Q(event=RentalEvent.returned)).filter(
#                                   renter_num=self.kwargs['pk'])).annotate(
#                                       rental_end_date=Max('rental_end'))
#         # .annotate(rental_end_date=Max('rental_end')
#         return context


# class UserSearchViewAjax(RentalViewBase, View):
#     """Filter list of users """
#     @csrf_exempt
#     def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
#         search_str = request.GET.get("q")
#         context = {}
#         if search_str:
#             users = User.objects.filter(Q(first_name___icontains=search_str)
#                                         | Q(last_name___icontains=search_str))
#         else:
#             users = User.objects.all()

#         context["users"] = users
#         html = render_to_string(
#             template_name="users/user-results-partial.html", context={"users": users}
#         )
#         data_dict = {"html_from_view": html}
#         return JsonResponse(data=data_dict, safe=False)
