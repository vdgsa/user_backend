import csv
import datetime
import io
import json
import os
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, Iterable, Literal

from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.storage import FileSystemStorage
from django.core.management.color import no_style
from django.db import connection
from django.db.models import Count, Q
from django.db.models.fields import NullBooleanField
from django.forms.widgets import DateTimeBaseInput, HiddenInput, NullBooleanSelect
from django.http import Http404, JsonResponse, response
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls.base import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import urlencode
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.generic.list import ListView

from vdgsa_backend.accounts.models import User
from vdgsa_backend.rental_viols.managers.InstrumentManager import (
    AccessoryManager, ViolManager, ViolSize
)
from vdgsa_backend.rental_viols.managers.RentalItemBaseManager import (
    RentalEvent, RentalItemBaseManager, RentalState
)
from vdgsa_backend.rental_viols.models import (
    Bow, Case, Image, ItemType, RentalContract, RentalHistory, RentalProgram, Viol,
    WaitingList
)
from vdgsa_backend.rental_viols.permissions import is_rental_manager


class RentalViewBase(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self) -> bool:
        return is_rental_manager(self.request.user)

    def reverse(*args, **kwargs):
        get = kwargs.pop('get', {})
        url = reverse(*args, **kwargs)
        if get:
            url += '?' + urlencode(get)
        return url


def getLegacyDir():
    legacy_upload_dir = os.path.join(settings.MEDIA_ROOT, 'legacy_upload')
    if (not os.path.exists(legacy_upload_dir)):
        os.mkdir(legacy_upload_dir)

    return legacy_upload_dir


def openJson(tableName):
    if (os.path.exists(str(getLegacyDir()) + "/" + tableName + ".json")):
        with open(str(getLegacyDir()) + "/" + tableName + ".json", encoding='utf-8') as data_file:
            json_data = json.loads(data_file.read())
            return json_data
    else:
        return None


def searchUser(email, first, last):
    found = User.objects.filter(Q(first_name__icontains=first) & Q(
        last_name__icontains=last) | Q(username=email))
    print(found)
    return found


def findRenter(id):
    legacy_users = openJson('renters')

    persons = list(filter(lambda legacy: legacy['renter_num'] == id, legacy_users))
    if(len(persons) > 1):
        print('found more than one!', persons)
    if(len(persons) == 1):
        found = User.objects.filter(Q(first_name__icontains=persons[0]['firstname']) & Q(
            last_name=persons[0]['lastname']) | Q(username=persons[0]['email']))
        if(len(found) > 1):
            print('Found multiple in Users', found)
        if(len(found) == 1):
            return found[0]
        else:
            print('Could not find User for Renter renter_num ', id)
            return None
    else:
        print('doh! Renter not found ', id)
        legacy = persons[0]['email'] or persons[0]['firstname'] + '.' + \
            persons[0]['lastname'] + '_' + \
            str(persons[0]['renter_num']) + '@legacy.rentalviols.org',
        found = User.objects.filter(Q(first_name__icontains=persons[0]['firstname']) & Q(
            last_name=persons[0]['lastname']) | Q(username=legacy))
        if(len(found) > 1):
            print('Found multiple in Users', found)
            return found
        if(len(found) == 1):
            return found[0]
        else:
            print('Could not find User for Renter storer_num ', id)
            return None


def findStorer(id):
    legacy_users = openJson('storers')
    persons = list(filter(lambda legacy: legacy['storer_num'] == id, legacy_users))
    if(len(persons) > 1):
        print('found more than one!', persons)
    if(len(persons) == 1):
        found = User.objects.filter(Q(first_name__icontains=persons[0]['firstname']) & Q(
            last_name=persons[0]['lastname']) | Q(username=persons[0]['email']))
        if(len(found) > 1):
            print('Found multiple in Users', found)
            return found
        if(len(found) == 1):
            return found[0]
        else:
            print('Could not find User for Storer storer_num ', id)
            return None
    else:
        print('doh! Storer not found ', id)
        legacy = persons[0]['email'] or persons[0]['firstname'] + '.' + \
            persons[0]['lastname'] + '_' + \
            str(persons[0]['storer_num']) + '@legacy.rentalviols.org',
        found = User.objects.filter(Q(first_name__icontains=persons[0]['firstname']) & Q(
            last_name=persons[0]['lastname']) | Q(username=legacy))
        if(len(found) > 1):
            print('Found multiple in Users', found)
            return found
        if(len(found) == 1):
            return found[0]
        else:
            print('Could not find User for Storer storer_num ', id)
            return None


def getRentalProgram(id):
    if(id == 0):
        return 'Regular'
    elif(id == 2):
        return 'Select Reserve'
    elif(id == 3):
        return 'Consort Loan'
    else:
        return 'Regular'


def check_date(dateString):
    try:
        year, month, day = dateString.split("-")
        yearInt = int(year)
        monthInt = int(month)
        dayInt = int(day)
        newDate = datetime.datetime(yearInt, monthInt, dayInt)
        return dateString
    except ValueError:
        return None


def getViol(viol_num):
    if(viol_num == 0):
        return None
    else:
        return Viol.objects.get(pk=viol_num),


class ImportView(RentalViewBase, TemplateView):
    template_name = 'import.html'

    def validateFiles(self):
        files = ['bows.json',
                 'renters.json',
                 'viols.json',
                 'storers.json',
                 'cases.json',
                 'scan_files.json',
                 'images.json',
                 'rental_history.json', ]

        uploaded = os.listdir(getLegacyDir())
        valid = [x for x in files if x not in uploaded]
        return valid

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        context['file_list'] = os.listdir(getLegacyDir())
        context['missing'] = self.validateFiles()

        return render(
            self.request,
            'import.html', context
        )

    def post(self, *args: Any, **kwargs: Any) -> HttpResponse:
        context = {}
        request_file = self.request.FILES['document'] if 'document' in self.request.FILES else None
        if request_file:
            fs = FileSystemStorage(location=getLegacyDir())
            file = fs.save(request_file.name, request_file)
            context['fileurl'] = fs.url(file)

        context['file_list'] = os.listdir(getLegacyDir())
        context['missing'] = self.validateFiles()

        return redirect(reverse('import'))


class ImportRunView(RentalViewBase, TemplateView):
    template_name = 'import.html'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        context = {}
        context['file_list'] = os.listdir(getLegacyDir())
        context['renters'] = insertRenters()
        context['storers'] = insertStorers()
        context['viols'] = insertViols()
        context['bows'] = insertBows()
        context['cases'] = insertCases()
        context['storers'] = updateViolsRentersStorers()
        context['history'] = insertRentalHistory()
        context['images'] = insertImages()
        context['contracts'] = insertScanFiles()
        # We now need to reset the Auto increment PK fields
        sequence_sql = connection.ops.sequence_reset_sql(no_style(), [Bow, Case, Image,
                                                                      RentalContract,
                                                                      RentalHistory, Viol,
                                                                      ])
        with connection.cursor() as cursor:
            for sql in sequence_sql:
                cursor.execute(sql)

        return render(
            self.request,
            'import.html', context
        )


class ImportDeleteView(RentalViewBase, TemplateView):
    template_name = 'import.html'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any):
        for file in os.listdir(getLegacyDir()):
            os.remove(os.path.join(getLegacyDir(), file))

        return redirect(reverse('import'))


def insertRenters():
    legacy_users = openJson('renters')
    if legacy_users:
        for i, s in enumerate(legacy_users):
            found = searchUser(s['email'] or 'NONE', s['firstname']
                               or 'firstname', s['lastname'] or 'lastname')
            if found:  # leading or trailing whitespace?
                legacy_users[i]['found'] = found
            else:
                user, created = User.objects.get_or_create(
                    username=s['email'] or s['firstname'] + '.' + s['lastname']
                    + '_' + str(s['renter_num']) + '@legacy.rentalviols.org',
                    defaults={
                        'first_name': s['firstname'],
                        'last_name': s['lastname'],
                        'address_line_1': s['address1'],
                        'address_line_2': s['address2'],
                        'address_city': s['city'],
                        'address_state': s['stateprov'],
                        'address_postal_code': s['postal_code'],
                        'address_country': s['country'],
                    })
                # print(user, created)
        return sorted(legacy_users, key=lambda x: (x['lastname'], x['firstname']))
    else:
        print('no renters.json file')

    return


def insertStorers():
    legacy_users = openJson('storers')
    if legacy_users:
        for i, s in enumerate(legacy_users):
            found = searchUser(s['email'] or 'NONE', s['firstname']
                               or 'firstname', s['lastname'] or 'lastname')
            if found:  # leading or trailing whitespace?
                legacy_users[i]['found'] = found
            else:
                user, created = User.objects.get_or_create(
                    username=s['email'] or s['firstname'] + '.' + s['lastname']
                    + '_' + str(s['storer_num']) + '@legacy.rentalviols.org',
                    defaults={
                        'first_name': s['firstname'],
                        'last_name': s['lastname'],
                        'address_line_1': s['address1'],
                        'address_line_2': s['address2'],
                        'address_city': s['city'],
                        'address_state': s['stateprov'],
                        'address_postal_code': s['postal_code'],
                        'address_country': s['country'],
                    })
                print(user, created)
        return sorted(legacy_users, key=lambda x: (x['lastname'], x['firstname']))
    else:
        print('no storers.json file')

    return


def insertViols():
    viols = openJson('viols')
    result = []
    if viols:
        for i, v in enumerate(viols):
            viol, created = Viol.objects.update_or_create(
                viol_num=v['viol_num'],
                defaults={
                    'strings': v['strings'],
                    'vdgsa_number': v['vdgsa_number'],
                    'maker': v['maker'],
                    'size': v['size'].lower(),
                    'status': v['state'],
                    'value': v['inst_value'],
                    'provenance': v['provenance'],
                    'description': v['description'],
                    'accession_date': check_date(v['accession_date']),
                    'notes': v['notes'],
                    'program': getRentalProgram(v['program']),
                    # 'renter': v[''],
                    # 'storer': v[''],

                })

            print(viol, created)
            result.append(created)
    else:
        print('no viols.json file')

    return result


def updateViolsRentersStorers():
    viols = openJson('viols')
    result = []
    if viols:
        for i, v in enumerate(viols):
            viol = Viol.objects.get(pk=v['viol_num'])
            if(not viol):
                print('viol not found ', v['viol_num'])
            else:
                if(v['renter'] & v['renter'] > 0):
                    renter = findRenter(v['renter'])
                    # print('User as Renter', renter)
                    viol.renter = renter

                if(v['storer'] & v['storer'] > 0):
                    storer = findStorer(v['storer'])
                    viol.storer = storer

                viol.save()

    else:
        print('no viols.json file')

    return result


def insertBows():
    bows = openJson('bows')
    result = []
    if bows:
        for i, v in enumerate(bows):
            print('insertBows', v['bow_num'], v['viol_num'], getViol(v['viol_num']))
            bow, created = Bow.objects.update_or_create(
                bow_num=v['bow_num'],
                defaults={
                    'vdgsa_number': v['vdgsa_number'],
                    'maker': v['maker'],
                    'size': v['size'].lower(),
                    'state': v['state'],
                    'value': v['value'],
                    'provenance': v['provenance'],
                    'description': v['description'],
                    'accession_date': check_date(v['accession_date']),
                    'notes': v['notes'],
                    'program': getRentalProgram(v['program']),
                    # 'storer': v[''],

                })
            if(v['viol_num']):
                bow.viol_num = Viol.objects.get(pk=v['viol_num'])
                bow.save()

            # print(bow, created)
            result.append(created)
    else:
        print('no bows.json file')

    return result


def insertCases():
    cases = openJson('cases')
    result = []
    if cases:
        for i, v in enumerate(cases):
            case, created = Case.objects.update_or_create(
                case_num=v['case_num'],
                defaults={
                    'vdgsa_number': v['vdgsa_number'],
                    'maker': v['maker'],
                    'size': v['size'].lower(),
                    'state': v['state'],
                    'value': v['value'],
                    'provenance': v['provenance'],
                    'description': v['description'],
                    'accession_date': check_date(v['accession_date']),
                    'notes': v['notes'],
                    'program': getRentalProgram(v['program']),
                    # 'storer': v[''],

                })

            if(v['viol_num']):
                case.viol_num = Viol.objects.get(pk=v['viol_num'])
                case.save()

            # print(case, created)
            result.append(created)
    else:
        print('no cases.json file')

    return result


def insertRentalHistory():
    histories = openJson('rental_history')
    result = []

    # entry_num
    # viol_num
    # bow_num
    # case_num
    # renter_num
    # event
    # notes
    # rental_start
    # rental_end
    # contract_scan
    if histories:
        for i, h in enumerate(histories):
            history, created = RentalHistory.objects.update_or_create(
                entry_num=h['entry_num'],
                defaults={
                    'event': h['event'],
                    'notes': h['notes'],
                    'rental_start': check_date(h['rental_start']),
                    'rental_end': check_date(h['rental_end']),
                })

            if(h['viol_num'] & h['viol_num'] > 0):
                history.viol_num = Viol.objects.get(pk=h['viol_num'])
            if(h['bow_num'] & h['bow_num'] > 0):
                history.bow_num = Bow.objects.get(pk=h['bow_num'])
            if(h['case_num'] & h['case_num'] > 0):
                history.case_num = Case.objects.get(pk=h['case_num'])
            if(h['renter_num'] & h['renter_num'] > 0):
                renter = findRenter(h['renter_num'])
                # print('User as Renter', renter)
                history.renter_num = renter
            if(h['contract_scan'] & h['contract_scan'] > 0):
                contract = RentalContract.objects.get(pk=h['contract_scan'])
                # print('User as Renter', renter)
                history.contract_scan = contract

            history.save()
            # print(history, created)
            result.append(created)

    else:
        print('no rental_history.json file')

    return result


def rewritePath(path):
    if(path):
        return path.replace('/uploads/', '')
    else:
        return None


def insertImages():
    images = openJson('images')
    result = []
    if images:
        for i, v in enumerate(images):
            image, created = Image.objects.update_or_create(
                picture_id=v['picture_id'],
                defaults={
                    'vbc_number': v['vbc_number'],
                    'type': v['type'],
                    'orig_image_file_name': v['orig_image_file_name'],
                    'image_file_name': rewritePath(v['image_file_name']),
                    'image_width': v['image_width'],
                    'image_height': v['image_height'],
                    'thumb_file_name': v['thumb_file_name'],
                    'thumb_width': v['thumb_width'],
                    'thumb_height': v['thumb_height'],
                    'caption': v['caption'],
                })

            # if(v['vbc_number']):
            #     if v['type'] == 'viol':
            #         image.picture_id = Viol.objects.get(pk=v['vbc_number'])
            #     if v['type'] == 'bow':
            #         image.picture_id = Bow.objects.get(pk=v['vbc_number'])
            #     if v['type'] == 'case':
            #         image.picture_id = Case.objects.get(pk=v['vbc_number'])
            #     image.save()

            print(image, created)
            result.append(created)
    else:
        print('no images.json file')

    return result


def insertScanFiles():
    scan = openJson('scan_files')
    result = []
    if scan:
        for i, v in enumerate(scan):
            case, created = RentalContract.objects.update_or_create(
                entry_num=v['entry_num'],
                defaults={
                    'document': rewritePath(v['file_name']),
                    'file_name': rewritePath(v['file_name']),
                    'original_name': v['original_name'],
                })

    else:
        print('no scan_files.json file')

    return result
