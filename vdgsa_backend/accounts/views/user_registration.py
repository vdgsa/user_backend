"""
Contains forms and views involved in user account creation.
"""

from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.views import View
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox

from vdgsa_backend.accounts.models import User
from vdgsa_backend.accounts.views.utils import LocationAddress


class UserRegistrationForm(PasswordResetForm):
    first_name = forms.CharField()
    last_name = forms.CharField()
    address_line_1 = forms.CharField()
    address_line_2 = forms.CharField(required=False)
    address_city = forms.CharField(label='City')
    address_state = forms.ChoiceField(
            choices=[(c.code.split('-')[1], c.name) for c in LocationAddress.getSubdivisions('US')],
            label="State/Province"
        )
    address_postal_code = forms.CharField(label='ZIP/Postal Code')
    address_country = forms.ChoiceField(
            choices=[(c.alpha_2, c.name) for c in LocationAddress.getCountries()],
            label="Select a Country",
            initial='US'
        )

    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)


class UserRegistrationView(View):


    def get(self, request: HttpRequest) -> HttpResponse:
        return self._render_form(UserRegistrationForm())

    def post(self, request: HttpRequest) -> HttpResponse:
        form = UserRegistrationForm(request.POST)

        if not form.is_valid():
            return self._render_form(form)
        
        else: 
            email = form.cleaned_data['email']
            user, created = User.objects.update_or_create(
                username=email,
                defaults={
                    'first_name': form.cleaned_data['first_name'],
                    'last_name': form.cleaned_data['last_name'],
                    'address_line_1': form.cleaned_data['address_line_1'],
                    'address_line_2': form.cleaned_data['address_line_2'],
                    'address_city': form.cleaned_data['address_city'],
                    'address_state': form.cleaned_data['address_state'],
                    'address_postal_code': form.cleaned_data['address_postal_code'],
                    'address_country': form.cleaned_data['address_country'],
                }
            )
            # Django sets the "password" field to the empty string by default.
            # If the above query loaded an existing user and that user has
            # set a password, then the requested email address is in use.
            if not created and user.password != '':
                return self._render_form(form, username_taken=True)

            form.save(
                subject_template_name='user_registration/finish_registering_subject.txt',
                email_template_name='user_registration/finish_registering_email.txt',
                domain_override=request.META['HTTP_HOST']
            )
            return render(request, 'user_registration/finish_registration.html')

    # "username_taken = True" will tell the template to show a message with a link to the
    # password reset page.
    def _render_form(self, form: PasswordResetForm, username_taken: bool = False) -> HttpResponse:
        return render(
            self.request,
            'user_registration/user_registration.html',
            {'form': form, 'username_taken': username_taken}
        )
