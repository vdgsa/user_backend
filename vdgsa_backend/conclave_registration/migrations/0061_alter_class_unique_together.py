# Generated by Django 3.2.11 on 2022-04-01 22:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('conclave_registration', '0060_conclaveregistrationconfig_covid_policy_markdown'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='class',
            unique_together={('conclave_config', 'name', 'period')},
        ),
    ]
