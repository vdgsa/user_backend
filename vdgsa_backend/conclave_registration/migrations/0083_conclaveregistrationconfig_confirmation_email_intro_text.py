# Generated by Django 3.2.11 on 2023-04-12 22:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conclave_registration', '0082_alter_additionalregistrationinfo_num_display_space_days'),
    ]

    operations = [
        migrations.AddField(
            model_name='conclaveregistrationconfig',
            name='confirmation_email_intro_text',
            field=models.TextField(blank=True),
        ),
    ]