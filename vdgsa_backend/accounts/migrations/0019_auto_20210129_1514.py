# Generated by Django 3.1.4 on 2021-01-29 15:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0018_auto_20210119_2249'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='is_builder',
            new_name='is_bow_maker',
        ),
        migrations.AddField(
            model_name='user',
            name='is_deceased',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='is_instrument_maker',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='is_repairer',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='membershipsubscription',
            name='membership_type',
            field=models.CharField(choices=[('regular', 'Regular ($35)'), ('student', 'Student ($20)'), ('international', 'International ($40)'), ('lifetime', 'Lifetime'), ('complementary', 'Complementary'), ('organization', 'Organization')], max_length=50),
        ),
        migrations.AlterField(
            model_name='pendingmembershipsubscriptionpurchase',
            name='membership_type',
            field=models.CharField(choices=[('regular', 'Regular ($35)'), ('student', 'Student ($20)'), ('international', 'International ($40)'), ('lifetime', 'Lifetime'), ('complementary', 'Complementary'), ('organization', 'Organization')], max_length=50),
        ),
    ]
