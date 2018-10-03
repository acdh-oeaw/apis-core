#!/usr/bin/python
# -*- coding: utf-8 -*-
from apis_core.apis_entities.models import Place, Person, Institution, Event, Work
from apis_core.apis_metainfo.models import Uri
from apis_core.default_settings.NER_settings import autocomp_settings as ac_settings
from apis_core.apis_relations.models import PersonPerson, PersonPlace, PersonInstitution

import autocomplete_light.shortcuts as al
from django.db.models import Q

import requests
import json
import operator
from functools import reduce
import dateutil.parser
import re


class StanbolAutocompleteBase(al.AutocompleteListTemplate):
    autocomplete_template = 'apis_templates/autocomplete/stanbol.html'

    widget_attrs = {

    }

    attrs = {
        'data-autocomplete-minimum-characters': 3,
        'placeholder': u'Start typing to get suggestions',
        'class': 'autocomplete-ort-uri form-control'
    }

    @staticmethod
    def parse_stanbol_object(obj, key, *args):
        if len(args) > 0:
            lst1 = args[0]
        else:
            lst1 = None
        if obj[1] == 'GNDDate':
            if lst1 is not None:
                try:
                    return dateutil.parser.parse(lst1[key][0]['value'])
                except:
                    return lst1[key][0]['value']
            else:
                return obj[0]
        elif obj[1] == 'String':
            if lst1 is not None:
                return lst1[key][0]['value']
            else:
                return obj[0]
        elif obj[1] == 'gndLong':
            if lst1 is not None:
                try:
                    return re.search('Point \( [+-]([0-9\.]+) [+-]([0-9\.]+)', lst1[key][0]['value']).group(1)
                except:
                    print('extract fails')
                    return None
            else:
                print('no match')

    def choices_for_request(self):
        ac_type = self.autocomplete_type
        ac_type_model = self.autocomplete_type_model
        choices = []
        headers = {'Content-Type': 'application/json'}
        q = self.request.GET.get('q')
        for m in ac_type_model:
            arg_list = []
            for mm in m[1]:
                arg_list.append(Q(**{mm+'__icontains': q}))
            res = m[0].objects.filter(reduce(operator.or_, arg_list)).distinct()
            for r in res:
                f = dict()
                f['ac_type'] = '_'.join(ac_type)
                f['name'] = r
                f['score'] = None
                try:
                    f['uri'] = Uri.objects.filter(entity=r)[0].uri
                except:
                    continue
                f['source'] = 'db'
                if ac_type[0] == 'Place':
                    if r.lng != None and r.lat != None:
                        f['long'] = str(r.lng)
                        f['lat'] = str(r.lat)
                f['descr'] = m[2][0].format(*[getattr(r, s) for s in m[2][1]])
                choices.append(f)

        for o in ac_type:
            for y in ac_settings[o]:
                ldpath = ""
                for d in y['fields'].keys():
                    ldpath += "{} = <{}>;\n".format(d, y['fields'][d][0])
                data = {
                    'limit': 20,
                    'name': q,
                    'ldpath': ldpath
                }
                try:
                    r = requests.get(y['url'], params=data, headers=headers)
                    if r.status_code != 200:
                        choices.append({'name': 'Connection to Stanbol failed'})
                        continue
                    res = r.json()
                except:
                    choices.append({'name': 'Connection to Stanbol failed'})
                    continue
                for x in res['results']:
                    f = dict()
                    name = x['name'][0]['value']
                    score = str(x[ac_settings['score']][0]['value'])
                    id = x[ac_settings['uri']]
                    f['ac_type'] = '_'.join(ac_type)
                    f['name'] = name
                    f['score'] = score
                    f['uri'] = id
                    f['source'] = y['source']
                    for field in y['fields'].keys():
                        if field in x.keys():
                            f[field] = self.parse_stanbol_object(y['fields'][field], field, x)
                        else:
                            f[field] = None
                    choices.append(f)
        return choices


class AddRelationBaseAutocomplete(al.AutocompleteListTemplate):
    autocomplete_template = 'apis_templates/autocomplete/AddRelation.html'

    widget_attrs = {

    }

    attrs = {
        'data-autocomplete-minimum-characters': 3,
        'placeholder': u'Start typing to get suggestions',
        'class': 'autocomplete-add-relation form-control'
    }

    def choices_for_request(self):
        q = self.request.GET.get('q', None)
        instance_pk = self.request.GET.get('instance_pk', None)
        choices = []
        model_name = self.model2.__name__.lower()
        if instance_pk and q:
            instance = self.model2.objects.get(pk=instance_pk)
        else:
            return choices
        for rel in self.relations:
            if 'related_' + model_name in dir(rel):
                dd = rel.objects.filter(**{
                        'related_' + model_name: instance,
                        'relation_type__name__icontains': q}).exclude(annotation__isnull=False)
                choices.extend(dd)
            elif 'related_' + model_name + 'A' in dir(rel):
                choices.extend(
                    rel.objects.filter(
                        Q(**{
                            'related_' + model_name + 'A': instance,
                            'relation_type__name__icontains': q}) |
                        Q(**{
                            'related_' + model_name + 'B': instance,
                            'relation_type__name__icontains': q})).distinct().exclude(annotation__isnull=False))
        return choices


class PlaceAutocomplete(StanbolAutocompleteBase):
    autocomplete_type = ['Place', ]
    autocomplete_type_model = [(Place, ['name', 'label__label'], ('Status: {}', ['status'])), ]


class InstitutionAutocomplete(StanbolAutocompleteBase):
    autocomplete_type = ['Institution', ]
    autocomplete_type_model = [(Institution, ['name', 'label__label'], ('Status: {}, Gründungsdatum: {}', ['status', 'start_date_written'])), ]


class PersonAutocomplete(StanbolAutocompleteBase):
    autocomplete_type = ['Person', ]
    autocomplete_type_model = [(Person, ['name', 'first_name', 'label__label'], ('Geburtsdatum: {}, Sterbedatum: {}', ['start_date_written', 'end_date_written']))]


class EventAutocomplete(StanbolAutocompleteBase):
    autocomplete_type = ['Event', ]
    autocomplete_type_model = [(Event, ['name', 'label__label'], ('Start date: {}, Status: {}', ['start_date', 'status'])), ]


class WorkAutocomplete(StanbolAutocompleteBase):
    autocomplete_type = ['Work', ]
    autocomplete_type_model = [(Work, ['name', 'label__label'], ('Start date: {}, Status: {}', ['start_date', 'status'])), ]


class AddRelationPersonHighlighterAutocomplete(AddRelationBaseAutocomplete):
    relations = [PersonPerson, PersonPlace, PersonInstitution]
    model2 = Person


al.register(PlaceAutocomplete)
al.register(InstitutionAutocomplete)
al.register(PersonAutocomplete)
al.register(EventAutocomplete)
al.register(WorkAutocomplete)
al.register(AddRelationPersonHighlighterAutocomplete)
