# Generated by Django 3.1.7 on 2021-04-30 16:07

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conclave_registration', '0004_auto_20210428_2319'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='basicregistrationinfo',
            name='liability_release',
        ),
        migrations.RemoveField(
            model_name='basicregistrationinfo',
            name='willing_to_help_with_small_jobs',
        ),
        migrations.RemoveField(
            model_name='workstudyapplication',
            name='age_if_under_22',
        ),
        migrations.RemoveField(
            model_name='workstudyapplication',
            name='alternate_address',
        ),
        migrations.RemoveField(
            model_name='workstudyapplication',
            name='can_arrive_before_sunday_morning',
        ),
        migrations.RemoveField(
            model_name='workstudyapplication',
            name='earliest_could_arrive',
        ),
        migrations.RemoveField(
            model_name='workstudyapplication',
            name='first_time_applying',
        ),
        migrations.RemoveField(
            model_name='workstudyapplication',
            name='has_car',
        ),
        migrations.RemoveField(
            model_name='workstudyapplication',
            name='interest_in_work_study',
        ),
        migrations.RemoveField(
            model_name='workstudyapplication',
            name='is_full_time_student',
        ),
        migrations.RemoveField(
            model_name='workstudyapplication',
            name='job_first_choice',
        ),
        migrations.RemoveField(
            model_name='workstudyapplication',
            name='job_second_choice',
        ),
        migrations.RemoveField(
            model_name='workstudyapplication',
            name='questions_comments',
        ),
        migrations.RemoveField(
            model_name='workstudyapplication',
            name='student_degree',
        ),
        migrations.RemoveField(
            model_name='workstudyapplication',
            name='student_graduation_date',
        ),
        migrations.RemoveField(
            model_name='workstudyapplication',
            name='student_school',
        ),
        migrations.AddField(
            model_name='conclaveregistrationconfig',
            name='tshirt_image_url',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='workstudyapplication',
            name='can_receive_texts_at_phone_number',
            field=models.TextField(choices=[('yes', 'Yes'), ('no', 'No')], default='no'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='workstudyapplication',
            name='has_been_to_conclave',
            field=models.TextField(choices=[('yes', 'Yes'), ('no', 'No')], default='no'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='workstudyapplication',
            name='has_done_work_study',
            field=models.TextField(choices=[('yes', 'Yes'), ('no', 'No')], default='no'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='workstudyapplication',
            name='home_timezone',
            field=models.TextField(default='EDT'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='workstudyapplication',
            name='job_preferences',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('google_drive_file_organizing', 'Collecting and organizing files on Google Drive (before Conclave)'), ('video_editing', 'Video editing (before Conclave)'), ('assist_music_director_before_conclave', 'Assisting the music director (before Conclave)'), ('auction_prep_before_conclave', 'Auction preparation: collecting photos, writing descriptions of items (mostly in the few days before Conclave)'), ('auction_prep_during_conclave', 'Auction preparation: collecting photos, writing descriptions of items (mostly Sun-Tues during Conclave)'), ('social_event_helper', 'Social event helpers (specific times, e.g. lunchtime, ice cream social, Conclave banquet)'), ('tech_support', 'Answering tech-support type questions, like Zoom help, accessing YouTube, downloading files, etc. (specific shifts during Conclave)'), ('auction_event_helper', 'Auction event helpers (during the Conclave auction)'), ('assist_music_director_during_conclave', 'Assisting the music director (during Conclave)')], max_length=100), default=[], size=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='workstudyapplication',
            name='nickname_and_pronouns',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='workstudyapplication',
            name='other_info',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='workstudyapplication',
            name='other_timezone',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='workstudyapplication',
            name='relevant_job_experience',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='workstudyapplication',
            name='student_info',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='basicregistrationinfo',
            name='is_first_time_attendee',
            field=models.TextField(choices=[('yes', 'Yes'), ('no', 'No')]),
        ),
        migrations.AlterField(
            model_name='basicregistrationinfo',
            name='photo_release_auth',
            field=models.TextField(choices=[('yes', 'Yes'), ('no', 'No')]),
        ),
        migrations.AlterField(
            model_name='basicregistrationinfo',
            name='wants_display_space',
            field=models.TextField(choices=[('yes', 'Yes'), ('no', 'No')]),
        ),
        migrations.AlterField(
            model_name='workstudyapplication',
            name='other_skills',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='workstudyapplication',
            name='phone_number',
            field=models.CharField(max_length=50),
        ),
    ]
