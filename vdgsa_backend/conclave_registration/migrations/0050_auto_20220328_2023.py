# Generated by Django 3.2.11 on 2022-03-28 20:23

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conclave_registration', '0049_auto_20220328_2012'),
    ]

    operations = [
        migrations.AddField(
            model_name='workstudyapplication',
            name='can_arrive_before_first_meeting',
            field=models.TextField(choices=[('yes', 'Yes, I can arrive by 10am on Sunday morning'), ('yes_if_early_arrival', 'In order to make the 10am meeting, I would need to arrive early (on Friday or Saturday - specify below)'), ('no', "No, I can't arrive on time on Sunday morning")], default=''),
        ),
        migrations.AddField(
            model_name='workstudyapplication',
            name='early_arrival',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('friday_evening', 'Yes, I would like to come early, and can arrive on Friday before 6pm'), ('saturday_morning', 'Yes, I would like to come early, and can arrive on Saturday before noon'), ('saturday_evening', 'Yes, I would like to come early, and can arrive on Saturday before 6pm'), ('no', 'No, I do not want to come early, and will plan to arrive on Sunday')], max_length=100), default=list, size=None),
        ),
    ]