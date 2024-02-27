# Generated by Django 3.2.19 on 2024-02-27 02:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conclave_registration', '0086_auto_20240227_0151'),
    ]

    operations = [
        migrations.RenameField(
            model_name='conclaveregistrationconfig',
            old_name='beginners_extra_class_fee',
            new_name='beginners_extra_class_off_campus_fee',
        ),
        migrations.RenameField(
            model_name='conclaveregistrationconfig',
            old_name='beginners_two_extra_classes_fee',
            new_name='beginners_extra_class_on_campus_fee',
        ),
        migrations.AddField(
            model_name='conclaveregistrationconfig',
            name='beginners_two_extra_classes_off_campus_fee',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='conclaveregistrationconfig',
            name='beginners_two_extra_classes_on_campus_fee',
            field=models.IntegerField(blank=True, default=0),
        ),
    ]
