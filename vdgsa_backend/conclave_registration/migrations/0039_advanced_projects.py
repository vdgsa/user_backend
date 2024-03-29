# Generated by Django 3.2.11 on 2022-03-11 15:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('conclave_registration', '0038_auto_20220309_0114'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registrationentry',
            name='program',
            field=models.CharField(choices=[('regular', 'Regular Curriculum'), ('part_time', 'Part-Time Curriculum (1 class + optional freebie)'), ('beginners', 'Introduction to the Viol (free)'), ('consort_coop', 'Consort Cooperative'), ('seasoned_players', 'Seasoned Players'), ('advanced_projects', 'Advanced Projects'), ('faculty_guest_other', 'Faculty'), ('non_playing_attendee', 'Non-Playing Attendee')], max_length=50),
        ),
        migrations.CreateModel(
            name='AdvancedProjectsInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('participation', models.TextField(choices=[('participate', 'I would like to participate in other projects'), ('propose_a_project', 'I would like to propose a project')], default='')),
                ('project_proposal', models.TextField(blank=True)),
                ('registration_entry', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='advanced_projects', to='conclave_registration.registrationentry')),
            ],
        ),
    ]
