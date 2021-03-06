# Generated by Django 3.1.2 on 2020-10-23 16:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_accountpermissions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pendingmembershipsubscriptionpurchase',
            name='is_completed',
            field=models.BooleanField(blank=True, default=False, help_text='Indicates whether payment has succeeded and the subscription has been purchased.'),
        ),
        migrations.CreateModel(
            name='ChangeEmailRequest',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('new_email', models.EmailField(max_length=254)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
