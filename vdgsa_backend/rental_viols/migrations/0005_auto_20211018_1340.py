# Generated by Django 3.1.5 on 2021-10-18 13:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rental_viols', '0004_auto_20211013_2126'),
    ]

    operations = [
        migrations.AlterField(
            model_name='waitinglist',
            name='viol_num',
            field=models.ForeignKey(blank=True, db_column='viol_num', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='waitingList', to='rental_viols.viol'),
        ),
    ]
