# Generated by Django 3.1.7 on 2021-04-22 23:31

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ConclavePermissions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'permissions': (('conclave_team', 'Conclave Team'),),
                'managed': False,
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='ConclaveRegistrationConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(unique=True)),
                ('phase', models.CharField(choices=[('unpublished', 'Unpublished'), ('open', 'Open'), ('late', 'Late Registration'), ('closed', 'Closed')], default='unpublished', max_length=50)),
                ('faculty_registration_password', models.CharField(blank=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Class',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('period', models.IntegerField(choices=[(1, '1st Period'), (2, '2nd Period'), (3, '3rd Period'), (4, '4th Period')])),
                ('instructor', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('conclave_config', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='classes', to='conclave_registration.conclaveregistrationconfig')),
                ('level', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('Any', 'Any'), ('B', 'B'), ('B+', 'B+'), ('LI', 'LI'), ('LI+', 'LI+'), ('I', 'I'), ('I+', 'I+'), ('UI', 'UI'), ('UI+', 'UI+'), ('A', 'A'), ('A+', 'A+')], max_length=50), size=None)),
            ],
            options={
                'order_with_respect_to': 'conclave_config',
                'unique_together': {('name', 'period')},
            },
        ),
        migrations.CreateModel(
            name='RegistrationEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('conclave_config', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registration_entries', to='conclave_registration.conclaveregistrationconfig')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('program', models.CharField(choices=[('regular', 'Regular'), ('faculty_guest_other', 'Faculty/Guest/Other')], max_length=50)),
                ('is_late', models.BooleanField(blank=True, default=False)),
            ],
            options={
                'unique_together': {('conclave_config', 'user')},
            },
        ),
        migrations.CreateModel(
            name='InstrumentBringing',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_if_other', models.CharField(blank=True, max_length=100)),
                ('level', models.TextField(choices=[('B', 'B'), ('B+', 'B+'), ('LI', 'LI'), ('LI+', 'LI+'), ('I', 'I'), ('I+', 'I+'), ('UI', 'UI'), ('UI+', 'UI+'), ('A', 'A'), ('A+', 'A+')])),
                ('clefs', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('treble', 'Treble clef'), ('octave_treble', 'Octave Treble clef'), ('alto', 'Alto clef'), ('bass', 'Bass clef')], max_length=50), size=None)),
                ('registration_entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='instruments_bringing', to='conclave_registration.registrationentry')),
                ('size', models.CharField(choices=[('treble', 'Treble'), ('tenor', 'Tenor'), ('bass', 'Bass'), ('other', 'Other')], max_length=100)),
            ],
            options={
                'order_with_respect_to': 'registration_entry',
            },
        ),
        migrations.CreateModel(
            name='PaymentInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('donation', models.IntegerField(blank=True, default=0)),
                ('registration_entry', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='payment_info', to='conclave_registration.registrationentry')),
                ('stripe_payment_method_id', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='TShirts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registration_entry', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='tshirts', to='conclave_registration.registrationentry')),
                ('tshirt1', models.CharField(blank=True, choices=[('XS', 'X Small'), ('XS (Fitted)', 'X Small Fitted'), ('S', 'Small'), ('S (Fitted)', 'Small Fitted'), ('M', 'Medium'), ('M (Fitted)', 'Medium Fitted'), ('L', 'Large'), ('L (Fitted)', 'Large Fitted'), ('XL', 'X Large'), ('XL (Fitted)', 'X Large Fitted')], max_length=50)),
                ('tshirt2', models.CharField(blank=True, choices=[('XS', 'X Small'), ('XS (Fitted)', 'X Small Fitted'), ('S', 'Small'), ('S (Fitted)', 'Small Fitted'), ('M', 'Medium'), ('M (Fitted)', 'Medium Fitted'), ('L', 'Large'), ('L (Fitted)', 'Large Fitted'), ('XL', 'X Large'), ('XL (Fitted)', 'X Large Fitted')], max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='RegularProgramClassChoices',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registration_entry', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='regular_class_choices', to='conclave_registration.registrationentry')),
                ('period1_choice1', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period1_choice2', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period1_choice3', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period2_choice1', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period2_choice2', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period2_choice3', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period3_choice1', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period3_choice2', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period3_choice3', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period4_choice1', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period4_choice2', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period4_choice3', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period1_choice1_instrument', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.instrumentbringing')),
                ('period1_choice2_instrument', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.instrumentbringing')),
                ('period1_choice3_instrument', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.instrumentbringing')),
                ('period2_choice1_instrument', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.instrumentbringing')),
                ('period2_choice2_instrument', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.instrumentbringing')),
                ('period2_choice3_instrument', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.instrumentbringing')),
                ('period3_choice1_instrument', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.instrumentbringing')),
                ('period3_choice2_instrument', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.instrumentbringing')),
                ('period3_choice3_instrument', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.instrumentbringing')),
                ('period4_choice1_instrument', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.instrumentbringing')),
                ('period4_choice2_instrument', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.instrumentbringing')),
                ('period4_choice3_instrument', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.instrumentbringing')),
                ('tuition_option', models.TextField(choices=[('full_time', 'Full Time (2-3 Classes)'), ('part_time', 'Part Time (1 Class)')], default='full_time')),
            ],
        ),
        migrations.CreateModel(
            name='WorkStudyApplication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registration_entry', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='work_study', to='conclave_registration.registrationentry')),
                ('age_if_under_22', models.IntegerField(blank=True, default=None, null=True)),
                ('alternate_address', models.TextField(blank=True)),
                ('can_arrive_before_sunday_morning', models.BooleanField()),
                ('earliest_could_arrive', models.TextField()),
                ('first_time_applying', models.BooleanField()),
                ('has_car', models.BooleanField()),
                ('interest_in_work_study', models.TextField(max_length=500)),
                ('is_full_time_student', models.BooleanField()),
                ('job_first_choice', models.TextField(choices=[('hospitality', 'Hospitality'), ('moving_crew', 'Moving Crew'), ('copy_crew_auction', 'Copy Crew/Auction'), ('money_store', 'Money/Store'), ('any', 'Any')])),
                ('job_second_choice', models.TextField(choices=[('hospitality', 'Hospitality'), ('moving_crew', 'Moving Crew'), ('copy_crew_auction', 'Copy Crew/Auction'), ('money_store', 'Money/Store'), ('any', 'Any')])),
                ('other_skills', models.TextField(blank=True, max_length=500)),
                ('phone_number', models.CharField(blank=True, max_length=50)),
                ('questions_comments', models.TextField(blank=True, max_length=500)),
                ('student_degree', models.TextField(blank=True)),
                ('student_graduation_date', models.TextField(blank=True)),
                ('student_school', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='BasicRegistrationInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_first_time_attendee', models.BooleanField()),
                ('buddy_willingness', models.TextField(choices=[('yes', 'Yes'), ('no', 'No'), ('maybe', 'Maybe')])),
                ('willing_to_help_with_small_jobs', models.BooleanField(blank=True)),
                ('wants_display_space', models.BooleanField(blank=True)),
                ('photo_release_auth', models.BooleanField()),
                ('liability_release', models.BooleanField()),
                ('registration_entry', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='basic_info', to='conclave_registration.registrationentry')),
                ('other_info', models.TextField(blank=True)),
            ],
        ),
    ]