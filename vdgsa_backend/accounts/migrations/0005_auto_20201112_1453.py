# Generated by Django 3.1.2 on 2020-11-12 14:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_auto_20201023_1640'),
    ]

    operations = [
        migrations.AddField(
            model_name='pendingmembershipsubscriptionpurchase',
            name='membership_type',
            field=models.CharField(choices=[('regular', 'Regular ($40)'), ('student', 'Student ($35)'), ('lifetime', 'Lifetime')], default='regular', max_length=50),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='membershipsubscription',
            name='membership_type',
            field=models.CharField(choices=[('regular', 'Regular ($40)'), ('student', 'Student ($35)'), ('lifetime', 'Lifetime')], max_length=50),
        ),
        migrations.AlterField(
            model_name='membershipsubscriptionhistory',
            name='membership_type',
            field=models.CharField(choices=[('regular', 'Regular ($40)'), ('student', 'Student ($35)'), ('lifetime', 'Lifetime')], max_length=50),
        ),
    ]