# Generated by Django 3.2.11 on 2022-02-28 20:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('conclave_registration', '0029_fees'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workstudyapplication',
            name='home_timezone',
        ),
        migrations.RemoveField(
            model_name='workstudyapplication',
            name='other_timezone',
        ),
    ]
