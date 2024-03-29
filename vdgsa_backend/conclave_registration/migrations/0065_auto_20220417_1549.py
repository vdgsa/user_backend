# Generated by Django 3.2.11 on 2022-04-17 15:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conclave_registration', '0064_auto_20220417_1547'),
    ]

    operations = [
        migrations.AddField(
            model_name='conclaveregistrationconfig',
            name='double_room_early_arrival_per_night_cost',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='conclaveregistrationconfig',
            name='double_room_per_night_cost',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='conclaveregistrationconfig',
            name='single_room_early_arrival_per_night_cost',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='conclaveregistrationconfig',
            name='single_room_per_night_cost',
            field=models.IntegerField(blank=True, default=0),
        ),
    ]
