# Generated by Django 3.1.5 on 2021-01-23 00:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rental_viols', '0002_auto_20210123_0019'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bow',
            name='program',
            field=models.ForeignKey(blank=True, db_column='program', null=True, on_delete=django.db.models.deletion.PROTECT, to='rental_viols.program'),
        ),
    ]