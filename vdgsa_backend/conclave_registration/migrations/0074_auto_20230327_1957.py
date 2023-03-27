# Generated by Django 3.2.13 on 2023-03-27 19:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conclave_registration', '0073_conclaveregistrationconfig_instruments_page_markdown'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advancedprojectsinfo',
            name='participation',
            field=models.TextField(choices=[('yes', 'Yes'), ('no', 'No')], default=''),
        ),
        migrations.AlterField(
            model_name='registrationentry',
            name='program',
            field=models.CharField(choices=[('regular', 'Regular Curriculum Full-time (2-3 classes + optional "Freebie")'), ('part_time', 'Regular Curriculum Part-time (1 class only)'), ('beginners', 'Beginning Viol (free to local attendees)'), ('consort_coop', 'Consort Co-op (CC 3+1 or CC 2+2)'), ('seasoned_players', 'Seasoned Players'), ('faculty_guest_other', 'Faculty'), ('non_playing_attendee', 'Non-playing Attendee')], max_length=50),
        ),
    ]
