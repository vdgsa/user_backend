# Generated by Django 3.2.11 on 2023-04-12 21:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conclave_registration', '0080_auto_20230412_2146'),
    ]

    operations = [
        migrations.AddField(
            model_name='conclaveregistrationconfig',
            name='canadian_discount_text',
            field=models.TextField(blank=True),
        ),
    ]
