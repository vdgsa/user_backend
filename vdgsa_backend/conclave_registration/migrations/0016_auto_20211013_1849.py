# Generated by Django 3.1.7 on 2021-10-13 18:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('conclave_registration', '0015_additionalregistrationinfo_phone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='additionalregistrationinfo',
            name='registration_entry',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='additional_info', to='conclave_registration.registrationentry'),
        ),
    ]
