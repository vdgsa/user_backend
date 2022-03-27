from django.core.management.base import BaseCommand, CommandError
from vdgsa_backend.emails.views import ExpiringEmails


class Command(BaseCommand):
    help = 'Send Membership emails. Job Configuration in vdgsa_backend.emails.views'

    def handle(self, *args, **options):

        expemails = ExpiringEmails()
        expemails.runJob()
        self.stdout.write(self.style.SUCCESS('Successfully sent email'))
