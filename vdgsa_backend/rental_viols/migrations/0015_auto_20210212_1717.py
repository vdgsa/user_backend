# Generated by Django 3.1.5 on 2021-02-12 17:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rental_viols', '0014_auto_20210207_2242'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bow',
            name='status',
            field=models.TextField(choices=[('active', 'Active'), ('attached', 'Attached'), ('deleted', 'Deleted'), ('detached', 'Detached'), ('new', 'New'), ('reserved_for', 'Reserved'), ('rented', 'Rented'), ('retired', 'Retired'), ('returned', 'Returned')], default='new'),
        ),
        migrations.AlterField(
            model_name='case',
            name='status',
            field=models.TextField(choices=[('active', 'Active'), ('attached', 'Attached'), ('deleted', 'Deleted'), ('detached', 'Detached'), ('new', 'New'), ('reserved_for', 'Reserved'), ('rented', 'Rented'), ('retired', 'Retired'), ('returned', 'Returned')], default='new'),
        ),
        migrations.AlterField(
            model_name='rentalhistory',
            name='event',
            field=models.TextField(choices=[('active', 'Active'), ('attached', 'Attached'), ('deleted', 'Deleted'), ('detached', 'Detached'), ('new', 'New'), ('reserved_for', 'Reserved'), ('rented', 'Rented'), ('retired', 'Retired'), ('returned', 'Returned')]),
        ),
        migrations.AlterField(
            model_name='rentalhistory',
            name='status',
            field=models.TextField(choices=[('active', 'Active'), ('attached', 'Attached'), ('deleted', 'Deleted'), ('detached', 'Detached'), ('new', 'New'), ('reserved_for', 'Reserved'), ('rented', 'Rented'), ('retired', 'Retired'), ('returned', 'Returned')], default='new'),
        ),
        migrations.AlterField(
            model_name='viol',
            name='status',
            field=models.TextField(choices=[('active', 'Active'), ('attached', 'Attached'), ('deleted', 'Deleted'), ('detached', 'Detached'), ('new', 'New'), ('reserved_for', 'Reserved'), ('rented', 'Rented'), ('retired', 'Retired'), ('returned', 'Returned')], default='new'),
        ),
        migrations.AlterField(
            model_name='waitinglist',
            name='status',
            field=models.TextField(choices=[('active', 'Active'), ('attached', 'Attached'), ('deleted', 'Deleted'), ('detached', 'Detached'), ('new', 'New'), ('reserved_for', 'Reserved'), ('rented', 'Rented'), ('retired', 'Retired'), ('returned', 'Returned')], default='new'),
        ),
    ]