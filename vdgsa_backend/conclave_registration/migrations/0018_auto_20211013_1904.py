# Generated by Django 3.1.7 on 2021-10-13 19:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('conclave_registration', '0017_auto_20211013_1859'),
    ]

    operations = [
        migrations.RenameField(
            model_name='additionalregistrationinfo',
            old_name='attended_nonclave',
            new_name='attended_conclave_before',
        ),
    ]
