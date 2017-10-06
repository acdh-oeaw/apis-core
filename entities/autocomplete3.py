#!/usr/bin/python
# -*- coding: utf-8 -*-
from entities.models import Place, Person, Institution, Event, Work
from metainfo.models import Uri
from apis.settings.NER_settings import autocomp_settings as ac_settings
from relations.models import PersonPerson, PersonPlace, PersonInstitution

from dal import autocomplete
from django.db.models import Q
from django import http

import requests
import json
import operator
from functools import reduce
import dateutil.parser
import re


class GenericEntitiesAutocomplete(autocomplete.Select2ListView):
    #autocomplete_template = 'autocomplete/stanbol.html'

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

    def get_result_label(self, item):
        print(item)
        return '{}'.format(item['name'])

    def get(self, request, *args, **kwargs):
        print(dir(autocomplete.Select2ListView))
        ac_type = [self.kwargs['entity']]
        choices = []
        headers = {'Content-Type': 'application/json'}
        q = self.q
        print(q)
        for o in ac_type:
            for y in ac_settings[o.title()]:
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
                    #f['ac_type'] = '_'.join(ac_type)
                    f['text'] = name
                    #f['score'] = score
                    f['id'] = id
                    #f['source'] = y['source']
                    # for field in y['fields'].keys():
                    #     if field in x.keys():
                    #         f[field] = self.parse_stanbol_object(y['fields'][field], field, x)
                    #     else:
                    #         f[field] = None
                    choices.append(f)
        #return choices
        return http.HttpResponse(json.dumps({
            'results': choices + []
        }), content_type='application/json')



