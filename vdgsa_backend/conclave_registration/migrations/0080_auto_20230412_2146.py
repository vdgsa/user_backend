# Generated by Django 3.2.11 on 2023-04-12 21:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conclave_registration', '0079_auto_20230412_2136'),
    ]

    operations = [
        migrations.AddField(
            model_name='conclaveregistrationconfig',
            name='housing_subsidy_text',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='conclaveregistrationconfig',
            name='supplemental_2023_housing_subsidy_text',
            field=models.TextField(blank=True),
        ),
    ]
