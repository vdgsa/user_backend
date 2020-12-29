from django.contrib.auth.forms import PasswordResetForm
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.views import View

from vdgsa_backend.accounts.models import User


class UserRegistrationView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return self._render_form(PasswordResetForm())

    def post(self, request: HttpRequest) -> HttpResponse:
        form = PasswordResetForm(request.POST)
        if not form.is_valid():
            self._render_form(form)

        email = form.cleaned_data['email']
        user, created = User.objects.get_or_create(username=email)
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
