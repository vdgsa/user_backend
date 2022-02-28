# Generated by Django 3.2.9 on 2022-01-14 14:55

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conclave_registration', '0023_auto_20220113_2014'),
    ]

    operations = [
        migrations.AlterField(
            model_name='housing',
            name='banquet_food_choice',
            field=models.TextField(choices=[('beef', 'Beef'), ('salmon', 'Salmon'), ('vegan', 'Vegan'), ('not_attending', 'Not Attending')], default=''),
        ),
        migrations.AlterField(
            model_name='housing',
            name='banquet_guest_food_choice',
            field=models.TextField(blank=True, choices=[('beef', 'Beef'), ('salmon', 'Salmon'), ('vegan', 'Vegan')]),
        ),
        migrations.AlterField(
            model_name='housing',
            name='dietary_needs',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('vegetarian', 'Vegetarian'), ('vegan', 'Vegan'), ('dairy_free', 'Dairy Free'), ('gluten_free', 'Gluten Free'), ('nut_allergy', 'Nut Allergy'), ('shellfish_allergy', 'Shellfish Allergy')], max_length=50), blank=True, size=None),
        ),
        migrations.AlterField(
            model_name='housing',
            name='is_bringing_guest_to_banquet',
            field=models.TextField(choices=[('yes', 'Yes'), ('no', 'No')]),
        ),
    ]