# Generated by Django 3.1.5 on 2021-01-31 23:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('rental_viols', '0011_auto_20210130_1534'),
    ]

    operations = [
        migrations.DeleteModel(
            name='RentalPermissions',
        ),
        migrations.AlterField(
            model_name='rentalhistory',
            name='bow_num',
            field=models.ForeignKey(blank=True, db_column='bow_num', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bow', to='rental_viols.bow'),
        ),
        migrations.AlterField(
            model_name='rentalhistory',
            name='case_num',
            field=models.ForeignKey(blank=True, db_column='case_num', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='case', to='rental_viols.case'),
        ),
        migrations.AlterField(
            model_name='rentalhistory',
            name='renter_num',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='rentalhistory',
            name='viol_num',
            field=models.ForeignKey(blank=True, db_column='viol_num', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='viol', to='rental_viols.viol'),
        ),
    ]
