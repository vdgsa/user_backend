# Generated by Django 3.2.11 on 2022-03-28 19:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('conclave_registration', '0045_auto_20220328_1649'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='conclaveregistrationconfig',
            name='work_study_scholarship_amount',
        ),
    ]
