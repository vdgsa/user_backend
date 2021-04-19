# Generated by Django 3.1.7 on 2021-04-19 17:07

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [('conclave_registration', '0001_initial'), ('conclave_registration', '0002_auto_20210324_1608'), ('conclave_registration', '0003_auto_20210324_1613'), ('conclave_registration', '0004_auto_20210325_1347'), ('conclave_registration', '0005_remove_class_level'), ('conclave_registration', '0006_class_level'), ('conclave_registration', '0007_remove_class_level'), ('conclave_registration', '0008_class_level'), ('conclave_registration', '0009_auto_20210325_1505'), ('conclave_registration', '0010_remove_class_level'), ('conclave_registration', '0011_class_level'), ('conclave_registration', '0012_conclaveregistrationconfig_faculty_registration_password'), ('conclave_registration', '0013_auto_20210401_1933'), ('conclave_registration', '0014_auto_20210401_2115'), ('conclave_registration', '0015_auto_20210407_1824'), ('conclave_registration', '0016_instrumentbringing_registration_entry'), ('conclave_registration', '0017_auto_20210408_2005'), ('conclave_registration', '0018_auto_20210408_2011'), ('conclave_registration', '0019_auto_20210408_2036'), ('conclave_registration', '0020_auto_20210409_1418'), ('conclave_registration', '0021_auto_20210409_1433'), ('conclave_registration', '0022_auto_20210409_1433'), ('conclave_registration', '0023_auto_20210409_1543'), ('conclave_registration', '0024_auto_20210413_2014'), ('conclave_registration', '0025_basicregistrationinfo_other_info'), ('conclave_registration', '0026_auto_20210414_1934'), ('conclave_registration', '0027_auto_20210414_2027'), ('conclave_registration', '0028_tshirts'), ('conclave_registration', '0029_auto_20210415_1832'), ('conclave_registration', '0030_auto_20210415_1850'), ('conclave_registration', '0031_paymentinfo'), ('conclave_registration', '0032_auto_20210415_1948'), ('conclave_registration', '0033_auto_20210415_2010'), ('conclave_registration', '0034_auto_20210415_2010'), ('conclave_registration', '0035_auto_20210415_2017'), ('conclave_registration', '0036_auto_20210416_1500'), ('conclave_registration', '0037_auto_20210419_1647')]

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
                ('level', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('Any', 'Any'), ('B', 'B'), ('B+', 'B+'), ('LI', 'LI'), ('LI+', 'LI+'), ('I', 'I'), ('I+', 'I+'), ('UI', 'UI'), ('UI+', 'UI+'), ('A', 'A'), ('A+', 'A+')], max_length=50), default=['Any'], size=None)),
            ],
            options={
                'unique_together': {('name', 'period')},
                'order_with_respect_to': 'conclave_config',
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
            name='WorkStudyApplication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registration_entry', models.OneToOneField(default=-1, on_delete=django.db.models.deletion.CASCADE, related_name='work_study', to='conclave_registration.registrationentry')),
                ('age_if_under_22', models.IntegerField(blank=True, default=None, null=True)),
                ('alternate_address', models.TextField(blank=True)),
                ('can_arrive_before_sunday_morning', models.BooleanField(default=False)),
                ('earliest_could_arrive', models.TextField(default='wee')),
                ('first_time_applying', models.BooleanField(default=False)),
                ('has_car', models.BooleanField(default=False)),
                ('interest_in_work_study', models.TextField(default='eggs', max_length=500)),
                ('is_full_time_student', models.BooleanField(default=False)),
                ('job_first_choice', models.TextField(choices=[('fixme', 'Fixme')], default='fixme')),
                ('job_second_choice', models.TextField(choices=[('fixme', 'Fixme')], default='fixme')),
                ('other_skills', models.TextField(blank=True, max_length=500)),
                ('phone_number', models.CharField(blank=True, max_length=50)),
                ('questions_comments', models.TextField(blank=True, max_length=500)),
                ('student_degree', models.TextField(blank=True)),
                ('student_graduation_date', models.TextField(blank=True)),
                ('student_school', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='InstrumentBringing',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_if_other', models.CharField(blank=True, max_length=100)),
                ('level', models.TextField(choices=[('Any', 'Any'), ('B', 'B'), ('B+', 'B+'), ('LI', 'LI'), ('LI+', 'LI+'), ('I', 'I'), ('I+', 'I+'), ('UI', 'UI'), ('UI+', 'UI+'), ('A', 'A'), ('A+', 'A+')])),
                ('clefs', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('treble', 'Treble clef'), ('octave_treble', 'Octave Treble clef'), ('alto', 'Alto clef'), ('bass', 'Bass clef')], max_length=50), size=None)),
                ('registration_entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='instruments_bringing', to='conclave_registration.registrationentry')),
                ('size', models.CharField(choices=[('treble', 'Treble'), ('tenor', 'Tenor'), ('bass', 'Bass'), ('other', 'Other')], max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='BasicRegistrationInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_first_time_attendee', models.TextField(choices=[('yes', 'Yes'), ('no', 'No'), ('maybe', 'Maybe')])),
                ('buddy_willingness', models.TextField(choices=[('yes', 'Yes'), ('no', 'No'), ('maybe', 'Maybe')])),
                ('willing_to_help_with_small_jobs', models.BooleanField(blank=True)),
                ('wants_display_space', models.BooleanField(blank=True)),
                ('photo_release_auth', models.BooleanField()),
                ('liability_release', models.BooleanField()),
                ('registration_entry', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='basic_info', to='conclave_registration.registrationentry')),
                ('other_info', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='RegularProgramClassChoices',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registration_entry', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='regular_class_choices', to='conclave_registration.registrationentry')),
                ('period1_choice1', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period1_choice2', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period1_choice3', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period2_choice1', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period2_choice2', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period2_choice3', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period3_choice1', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period3_choice2', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period3_choice3', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period4_choice1', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period4_choice2', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
                ('period4_choice3', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='conclave_registration.class')),
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
            ],
        ),
        migrations.CreateModel(
            name='TShirts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registration_entry', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='tshirts', to='conclave_registration.registrationentry')),
                ('tshirt1', models.CharField(blank=True, choices=[('XS', 'X Small'), ('XS (Fitted)', 'X Small Fitted'), ('S', 'Small'), ('S (Fitted)', 'Small Fitted'), ('M', 'Medium'), ('M (Fitted)', 'Medium Fitted'), ('L', 'Large'), ('L (Fitted)', 'Large Fitted'), ('XL', 'X Large'), ('XL (Fitted)', 'X Large Fitted')], max_length=50)),
                ('tshirt2', models.CharField(blank=True, choices=[('XS', 'X Small'), ('XS (Fitted)', 'X Small Fitted'), ('S', 'Small'), ('S (Fitted)', 'Small Fitted'), ('M', 'Medium'), ('M (Fitted)', 'Medium Fitted'), ('L', 'Large'), ('L (Fitted)', 'Large Fitted'), ('XL', 'X Large'), ('XL (Fitted)', 'X Large Fitted')], max_length=50)),
                ('tshirt3', models.CharField(blank=True, choices=[('XS', 'X Small'), ('XS (Fitted)', 'X Small Fitted'), ('S', 'Small'), ('S (Fitted)', 'Small Fitted'), ('M', 'Medium'), ('M (Fitted)', 'Medium Fitted'), ('L', 'Large'), ('L (Fitted)', 'Large Fitted'), ('XL', 'X Large'), ('XL (Fitted)', 'X Large Fitted')], max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='PaymentInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('donation', models.IntegerField(blank=True)),
                ('registration_entry', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='payment_info', to='conclave_registration.registrationentry')),
                ('stripe_payment_method_id', models.TextField(blank=True)),
            ],
        ),
    ]
