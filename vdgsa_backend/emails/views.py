from __future__ import annotations

import json
import string
from datetime import date, timedelta
from tkinter import W
from typing import Any, Dict, Final, Iterable, List
from urllib import request
from urllib.parse import urlencode

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import EmailMultiAlternatives, send_mail
from django.db.models import Count, F, IntegerField, Max, Q
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.template.loader import get_template
from django.urls.base import reverse
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from vdgsa_backend.accounts.models import (
    MembershipSubscription, MembershipType, PendingMembershipSubscriptionPurchase, User
)
from vdgsa_backend.accounts.views.permissions import is_membership_secretary


FROM_EMAIL: Final = 'membership@vdgsa.org'
BCC_TO_EMAIL: Final = 'membership@vdgsa.org'

EXPIRING_SOON = dict(days=30, message="This message is to inform you that your VdGSA\
membership will be expiring on {}.\n\
You can renew your membership online at ")

EXPIRED_NOW: Final = dict(days=0, message="This message is to inform you that your VdGSA\
membership will expire on {}.\n\
You can renew your membership online at ")

EXPIRED_PAST: Final = dict(days=-180, message="This message is to remind you that your VdGSA\
membership expired on {} days.\n\
You can renew your membership online at ")


class ExpiringEmails():
    """
    This Job will query the databse and send emails. 
    This is ususally run by a cron job.
    """

    def list_expiring_members(self, numdays: int) -> Iterable[User]:
        """
        Query membership for expiring in +/- days
        """

        startdate = timezone.now() + timedelta(days=numdays)
        endate = timezone.now() + timedelta(days=(numdays + 7))
        print('startdate', startdate, 'endate', endate)
        expiring_members = User.objects.filter(~Q(owned_subscription__membership_type=MembershipType.lifetime)
                                            & ~Q(owned_subscription__membership_type=MembershipType.complementary)
                                            & Q(owned_subscription__valid_until__gte=startdate)
                                            & Q(owned_subscription__valid_until__lte=endate))
        # print(expiring_members.query)
        # print('expiring_members', expiring_members)
        return expiring_members

    def sendEmail(self, request: HttpRequest, member: User,
                  message: string, send: boolean) -> EmailMultiAlternatives:
        logo = "hume.vdgsa.org/static/vdgsa_logo.gif"
        link = f'''hume.vdgsa.org{reverse('current-user-account')}'''

        subject = 'VdGSA membership'
        # to_email = member.emails
        to_email = 'doug.poplin@gmail.com'
        text_content = f'Dear {member.first_name.strip()},\n' + \
            message.format(member.subscription.valid_until.strftime("%m/%d/%Y")) + ' ' + link

        data = {'message': message.format(member.subscription.valid_until.strftime("%m/%d/%Y")),
                'link': link, 'logo': logo, 'member': member}
        mail_template = get_template('member_expiring_email.html')
        html_content = mail_template.render(data)

        msg = EmailMultiAlternatives(subject, text_content, FROM_EMAIL, [to_email],
                                     bcc=[BCC_TO_EMAIL])
        msg.attach_alternative(html_content, "text/html")
        if(send):
            msg.send()
        return msg

    def runJob(self) -> None:
        jobs = [EXPIRING_SOON, EXPIRED_NOW, EXPIRED_PAST]

        for job in jobs:
            expiring_members = self.list_expiring_members(job['days'])
            for member in expiring_members:
                print(job['days'], member.email,
                      member.subscription.valid_until.strftime("%m/%d/%Y"))

                msg = self.sendEmail(request, member, job['message'], send=True)


class Viewemails(LoginRequiredMixin, UserPassesTestMixin, View):
    jobs = [EXPIRING_SOON, EXPIRED_NOW, EXPIRED_PAST]

    def test_func(self) -> bool:
        return is_membership_secretary(self.request.user)

    def reverse(*args, **kwargs):
        get = kwargs.pop('get', {})
        url = reverse(*args, **kwargs)
        if get:
            url += '?' + urlencode(get)
        return url

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        context = {'emails': []}

        expemails = ExpiringEmails()
        for job in self.jobs:

            context['expiring_members'] = ExpiringEmails.list_expiring_members(self, job['days'])

            for member in context['expiring_members']:

                print(job['days'], member.email,
                      member.subscription.valid_until.strftime("%m/%d/%Y"))
                msg = expemails.sendEmail(request, member, job['message'], send=False)
                context['emails'].append(msg)

        return render(request, 'viewMemberEmails.html', context)

