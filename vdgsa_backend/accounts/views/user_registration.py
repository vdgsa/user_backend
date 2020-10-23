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

        # Create a new user object so that form.save() sends them
        # an email.
        User.objects.get_or_create(username=form.cleaned_data['email'])

        form.save(
            subject_template_name='user_registration/finish_registering_subject.txt',
            email_template_name='user_registration/finish_registering_email.txt',
            domain_override=request.META['HTTP_HOST']
        )
        return render(request, 'user_registration/finish_registration.html')

    def _render_form(self, form: PasswordResetForm) -> HttpResponse:
        return render(self.request, 'user_registration/user_registration.html', {'form': form})
