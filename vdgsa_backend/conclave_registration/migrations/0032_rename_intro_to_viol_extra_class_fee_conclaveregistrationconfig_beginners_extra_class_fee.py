# Generated by Django 3.2.11 on 2022-02-28 22:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('conclave_registration', '0031_alter_conclaveregistrationconfig_tshirt_price'),
    ]

    operations = [
        migrations.RenameField(
            model_name='conclaveregistrationconfig',
            old_name='intro_to_viol_extra_class_fee',
            new_name='beginners_extra_class_fee',
        ),
    ]