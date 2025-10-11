from __future__ import annotations

from datetime import datetime
from html.parser import HTMLParser
from sqlite3 import Date
from typing import Any, Final, Iterable
from urllib import request

from dateutil.relativedelta import relativedelta
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.db.models import Q
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.template.loader import get_template
from django.urls.base import reverse
from django.utils import timezone
from django.views import View

from vdgsa_backend.accounts.models import MembershipType, User
from vdgsa_backend.accounts.views.permissions import is_membership_secretary

FROM_EMAIL: Final = 'membership@vdgsa.org'
BCC_TO_EMAIL: Final = 'membership@vdgsa.org'
JOB_NOTIFICATION_TO_EMAIL: Final = ['membership@vdgsa.org', 'doug.poplin@gmail.com']

EXPIRING_THIS_MONTH: Final = dict(title='Expiring this month', months=0,
                                  message="needs to be renewed in the next month ")

EXPIRED_LAST_MONTH: Final = dict(title='Expired last month', months=1, message="has just expired ")

EXPIRED_PAST: Final = dict(title='Expired 6 months ago', months=6, message="expired 6 months ago ")


def subtract_months(date: Date, months: int) -> Date:
    return date + relativedelta(months=-months)


class ExpiringEmails():
    """
    runJob will query the databse and send emails.
    Designed to be run by a cron job.
    """

    def list_expiring_members(self, months: int) -> Iterable[User]:
        """
        Query membership for expiring in - months
        """
        # fakeToday = datetime.today() + relativedelta(days=+7)
        # targetDate = subtract_months(fakeToday, months)

        targetDate = subtract_months(datetime.today(), months)
        expiring_members = User.objects.filter(
            Q(is_deceased=False)
            & ~Q(owned_subscription__membership_type=MembershipType.lifetime)
            & ~Q(owned_subscription__membership_type=MembershipType.complementary)
            & Q(owned_subscription__valid_until__month=targetDate.month)
            & Q(owned_subscription__valid_until__year=targetDate.year)
            & Q(receives_expiration_reminder_emails=True)
        )
        return expiring_members

    def sendEmail(self, member: User,
                  job: dict[str, object], send: bool) -> EmailMultiAlternatives:
        logo = "hume.vdgsa.org/static/vdgsa_logo.gif"
        link = f'''hume.vdgsa.org{reverse('current-user-account')}'''

        subject = 'VdGSA membership'
        to_email = member.username
        data = {'message': job['message'],
                'link': link, 'logo': logo, 'member': member}
        mail_template = get_template('member_expiring_email.html')
        html_content = mail_template.render(data)

        f = HTMLFilter()
        f.feed(html_content)
        text_content = f.text

        msg = EmailMultiAlternatives(subject, text_content, FROM_EMAIL, [to_email],
                                     bcc=[BCC_TO_EMAIL])
        msg.attach_alternative(html_content, "text/html")
        if send:
            msg.send()
        return msg

    def runJob(self) -> None:
        jobs = [EXPIRING_THIS_MONTH, EXPIRED_LAST_MONTH, EXPIRED_PAST]
        logging = []

        for job in jobs:
            expiring_members = self.list_expiring_members(job['months'])
            title = job['title']
            for member in expiring_members:
                msg = self.sendEmail(member, job, send=True)
                log = f'{title}: {member.email}, expired \
on {member.subscription.valid_until.strftime("%m/%d/%Y")} \n'
                logging.append(log)

        email = EmailMessage(
            subject=f'Monthly Membership email has been run!',
            from_email=None,
            to=JOB_NOTIFICATION_TO_EMAIL,
            body=f'Results of Membership job ' + datetime.today().strftime("%B %d, %Y")
                    + '\n\n'
                    + '\n'.join(logging)
        )
        email.send(fail_silently=True)


class Viewemails(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Webpage view (sanity check)bto display what would happen if job was run now
    """
    jobs = [EXPIRING_THIS_MONTH, EXPIRED_LAST_MONTH, EXPIRED_PAST]

    def test_func(self) -> bool:
        return is_membership_secretary(self.request.user)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        context: dict[str, Any] = {'emails': []}

        expemails = ExpiringEmails()
        context['results'] = []
        context['html'] = []
        for job in self.jobs:

            context['expiring_members'] = ExpiringEmails.list_expiring_members(self, job['months'])
            title = job['title']
            for member in context['expiring_members']:
                result = f'{title}: {member.email}, expired\
                           on {member.subscription.valid_until.strftime("%m/%d/%Y")} '
                context['results'].append(result)

                msg = ExpiringEmails.sendEmail(self, member, job, send=False)
                context['html'].append(msg.alternatives[0][0])

                print(job['title'], member.email,
                      member.subscription.valid_until.strftime("%m/%d/%Y"))

        return render(request, 'viewMemberEmails.html', context)


class HTMLFilter(HTMLParser):
    text = ""

    def handle_data(self, data: str) -> None:
        self.text += data
