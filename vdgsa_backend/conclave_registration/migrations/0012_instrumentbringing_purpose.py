# Generated by Django 3.1.7 on 2021-10-13 17:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conclave_registration', '0011_auto_20210601_1246'),
    ]

    operations = [
        migrations.AddField(
            model_name='instrumentbringing',
            name='purpose',
            field=models.CharField(choices=[('bringing_for_self', 'Bringing For Self'), ('willing_to_loan', 'Willing To Loan'), ('wants_to_borrow', 'Wants To Borrow')], default='bringing_for_self', max_length=100),
            preserve_default=False,
        ),
    ]
