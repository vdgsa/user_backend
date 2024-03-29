# Generated by Django 3.1.7 on 2021-04-27 22:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conclave_registration', '0002_auto_20210425_1508'),
    ]

    operations = [
        migrations.AddField(
            model_name='regularprogramclasschoices',
            name='comments',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='registrationentry',
            name='program',
            field=models.CharField(choices=[('regular', 'Regular'), ('faculty_guest_other', 'Faculty/Guest/Other'), ('beginners', 'Beginners'), ('consort_coop', 'Consort Cooperative'), ('seasoned_players', 'Seasoned Players'), ('advanced_projects', 'Advanced Projects'), ('exhibitor', 'Vendor')], max_length=50),
        ),
    ]
