# Generated by Django 3.2.9 on 2022-01-14 15:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conclave_registration', '0024_auto_20220114_1455'),
    ]

    operations = [
        migrations.AddField(
            model_name='workstudyapplication',
            name='wants_work_study',
            field=models.TextField(choices=[('yes', 'Yes'), ('no', 'No')], default='yes'),
            preserve_default=False,
        ),
    ]
