# Generated by Django 3.2.13 on 2022-10-18 21:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0022_auto_20210212_1733'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='accountpermissions',
            options={'default_permissions': (), 'managed': False, 'permissions': (('membership_secretary', 'Membership Secretary'), ('board_member', 'Board Member'), ('rental_manager', 'Rental Manager'), ('rental_viewer', 'Rental View Only'))},
        ),
    ]
