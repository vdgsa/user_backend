# Generated by Django 3.2.19 on 2025-01-20 22:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('conclave_registration', '0090_conclaveregistrationconfig_overall_level_question_markdown'),
    ]

    operations = [
        migrations.AddField(
            model_name='instrumentbringing',
            name='relative_level',
            field=models.TextField(choices=[('at_level', 'At my level'), ('below_level', 'A little below my level'), ('just_beginning', "I'm just beginning to play this instument")], default='at_level'),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='SelfRatingInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.TextField(choices=[('B', 'B'), ('B+', 'B+'), ('LI', 'LI'), ('LI+', 'LI+'), ('I', 'I'), ('I+', 'I+'), ('UI', 'UI'), ('UI+', 'UI+'), ('A', 'A'), ('A+', 'A+')])),
                ('registration_entry', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='self_rating', to='conclave_registration.registrationentry')),
            ],
        ),
    ]
