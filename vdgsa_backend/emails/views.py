from __future__ import annotations
from html.parser import HTMLParser

import json
import string
from datetime import date, timedelta
from tkinter import W
from turtle import title
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

# message = {needs to be renewed in the next month | has just expired | expired 6 months ago}
# {“Renew your membership” | action to take when your membership has expired | }


FROM_EMAIL: Final = 'membership@vdgsa.org'
BCC_TO_EMAIL: Final = 'membership@vdgsa.org'

EXPIRING_THIS_MONTH = dict(title='Expiring this month', days=-30, message="needs to be renewed in the next month ")

EXPIRED_LAST_MONTH: Final = dict(title='Expired last month', days=0, message="has just expired ")

EXPIRED_PAST: Final = dict(title='Expired 6 months ago', days=150, message="expired 6 months ago ")


class ExpiringEmails():
    """
    runJob will query the databse and send emails. 
    This is ususally run by a cron job.
    """

    def list_expiring_members(self, days: int) -> Iterable[User]:
        """
        Query membership for expiring in +/- days
        """

        endate = (timezone.now() - timedelta(days=days)).replace(day=1, hour=0, minute=0, second=0, 
                                                                 microsecond=0) - timedelta(days=1)
        startdate = endate.replace(day=1)
        # print('date', startdate, endate)
        expiring_members = User.objects.filter(~Q(owned_subscription__membership_type=MembershipType.lifetime)
                                               & ~Q(owned_subscription__membership_type=MembershipType.complementary)
                                               & Q(owned_subscription__valid_until__gte=startdate)
                                               & Q(owned_subscription__valid_until__lte=endate))
        # print(expiring_members.query)
        # print('expiring_members', expiring_members)
        return expiring_members

    def sendEmail(self, request: HttpRequest, member: User,
                  job: dict, send: bool) -> EmailMultiAlternatives:
        logo = "hume.vdgsa.org/static/vdgsa_logo.gif"
        link = f'''hume.vdgsa.org{reverse('current-user-account')}'''

        subject = 'VdGSA membership'
        # to_email = member.username
        to_email = 'doug.poplin@gmail.com'
        # text_content = f'Dear {member.first_name.strip()},\n' + \
        #     message.format(member.subscription.valid_until.strftime("%m/%d/%Y")) + ' ' + link

        data = {'message': job['message'],
                'link': link, 'logo': logo, 'member': member}
        mail_template = get_template('member_expiring_email.html')
        html_content = mail_template.render(data)

        f = HTMLFilter()
        f.feed(html_content)
        text_content = f.text
        print('text_content', text_content)
        msg = EmailMultiAlternatives(subject, text_content, FROM_EMAIL, [to_email],
                                     bcc=[BCC_TO_EMAIL])
        msg.attach_alternative(html_content, "text/html")
        if(send):
            msg.send()
        return msg

    def runJob(self) -> None:
        jobs = [EXPIRING_THIS_MONTH, EXPIRED_LAST_MONTH, EXPIRED_PAST]

        for job in jobs:
            expiring_members = self.list_expiring_members(job['days'])
            for member in expiring_members:
                msg = self.sendEmail(request, member, job, send=True)


class Viewemails(LoginRequiredMixin, UserPassesTestMixin, View):
    jobs = [EXPIRING_THIS_MONTH, EXPIRED_LAST_MONTH, EXPIRED_PAST]

    def test_func(self) -> bool:
        return is_membership_secretary(self.request.user)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        context = {'emails': []}

        expemails = ExpiringEmails()
        context['results'] = []
        for job in self.jobs:

            context['expiring_members'] = ExpiringEmails.list_expiring_members(self, job['days'])
            title = job['title']
            for member in context['expiring_members']:
                result = f'{title}: ${member.email}, expired on {member.subscription.valid_until.strftime("%m/%d/%Y")} '

                context['results'].append(result)

                print(job['days'], member.email,
                      member.subscription.valid_until.strftime("%m/%d/%Y"))
            #     msg = expemails.sendEmail(request, member, job['message'], send=False)
            #     context['emails'].append(msg)

        return render(request, 'viewMemberEmails.html', context)


class HTMLFilter(HTMLParser):
    text = ""

    def handle_data(self, data):
        self.text += data
