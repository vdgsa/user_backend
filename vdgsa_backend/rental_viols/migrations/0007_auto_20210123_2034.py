# Generated by Django 3.1.4 on 2021-01-23 20:34

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('rental_viols', '0006_auto_20210123_1641'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ScanFiles',
            new_name='RentalContract',
        ),
        migrations.DeleteModel(
            name='Manager',
        ),
        migrations.AlterModelOptions(
            name='bow',
            options={},
        ),
        migrations.AlterModelOptions(
            name='case',
            options={},
        ),
        migrations.AlterModelOptions(
            name='image',
            options={},
        ),
        migrations.AlterModelOptions(
            name='rentalcontract',
            options={},
        ),
        migrations.AlterModelOptions(
            name='rentalhistory',
            options={},
        ),
        migrations.AlterModelOptions(
            name='viol',
            options={},
        ),
        migrations.AlterModelOptions(
            name='waitinglist',
            options={'ordering': ('entry_num',)},
        ),
        migrations.RemoveField(
            model_name='case',
            name='accession_date',
        ),
        migrations.RemoveField(
            model_name='case',
            name='description',
        ),
        migrations.RemoveField(
            model_name='case',
            name='maker',
        ),
        migrations.RemoveField(
            model_name='case',
            name='notes',
        ),
        migrations.RemoveField(
            model_name='case',
            name='program',
        ),
        migrations.RemoveField(
            model_name='case',
            name='provenance',
        ),
        migrations.RemoveField(
            model_name='case',
            name='size',
        ),
        migrations.RemoveField(
            model_name='case',
            name='state',
        ),
        migrations.RemoveField(
            model_name='case',
            name='storer',
        ),
        migrations.RemoveField(
            model_name='case',
            name='value',
        ),
        migrations.RemoveField(
            model_name='case',
            name='vdgsa_number',
        ),
        migrations.AddField(
            model_name='viol',
            name='value',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='bow',
            name='accession_date',
            field=models.DateField(blank=True, default=datetime.datetime(2021, 1, 23, 20, 32, 8, 467121, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='bow',
            name='description',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='bow',
            name='maker',
            field=models.CharField(default='', max_length=50),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='bow',
            name='notes',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='bow',
            name='provenance',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='bow',
            name='size',
            field=models.TextField(choices=[('pardessus', 'Pardessus'), ('treble', 'Treble'), ('alto', 'Alto'), ('tenor', 'Tenor'), ('bass', 'Bass'), ('seven_string_bass', 'Seven-String Bass'), ('other', 'Other')], default='pardessus'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='bow',
            name='storer',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='bow',
            name='value',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='bow',
            name='vdgsa_number',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='bow',
            name='viol_num',
            field=models.ForeignKey(blank=True, db_column='viol_num', default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bows', to='rental_viols.viol'),
        ),
        migrations.AlterField(
            model_name='case',
            name='viol_num',
            field=models.ForeignKey(blank=True, db_column='viol_num', default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='case', to='rental_viols.viol'),
        ),
        migrations.AlterField(
            model_name='image',
            name='caption',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='rentalhistory',
            name='bow_num',
            field=models.ForeignKey(blank=True, db_column='bow_num', null=True, on_delete=django.db.models.deletion.SET_NULL, to='rental_viols.bow'),
        ),
        migrations.AlterField(
            model_name='rentalhistory',
            name='case_num',
            field=models.ForeignKey(blank=True, db_column='case_num', null=True, on_delete=django.db.models.deletion.SET_NULL, to='rental_viols.case'),
        ),
        migrations.AlterField(
            model_name='rentalhistory',
            name='renter_num',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='rentalhistory',
            name='viol_num',
            field=models.ForeignKey(blank=True, db_column='viol_num', null=True, on_delete=django.db.models.deletion.SET_NULL, to='rental_viols.viol'),
        ),
        migrations.AlterField(
            model_name='viol',
            name='accession_date',
            field=models.DateField(blank=True, default=datetime.datetime(2021, 1, 23, 20, 33, 43, 445584, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='viol',
            name='description',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='viol',
            name='maker',
            field=models.CharField(default='', max_length=50),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='viol',
            name='notes',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='viol',
            name='program',
            field=models.TextField(choices=[('regular', 'Regular'), ('select_reserve', 'Select Reserve'), ('consort_loan', 'Consort Loan')], default='regular'),
        ),
        migrations.AlterField(
            model_name='viol',
            name='provenance',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='viol',
            name='renter',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='viol',
            name='size',
            field=models.TextField(choices=[('pardessus', 'Pardessus'), ('treble', 'Treble'), ('alto', 'Alto'), ('tenor', 'Tenor'), ('bass', 'Bass'), ('seven_string_bass', 'Seven-String Bass'), ('other', 'Other')], default='pardessus'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='viol',
            name='state',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='viol',
            name='storer',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='viol',
            name='strings',
            field=models.PositiveIntegerField(blank=True, default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='viol',
            name='vdgsa_number',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='waitinglist',
            name='renter_num',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='waitinglist',
            name='size',
            field=models.TextField(choices=[], default='pardessus'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='waitinglist',
            name='viol_num',
            field=models.ForeignKey(blank=True, db_column='viol_num', default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='rental_viols.viol'),
        ),
        migrations.DeleteModel(
            name='Program',
        ),
        migrations.DeleteModel(
            name='Renter',
        ),
        migrations.DeleteModel(
            name='Storer',
        ),
    ]
