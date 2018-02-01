#!/usr/bin/python
# -*- coding: utf-8 -*-
from entities.models import Place, Person, Institution, Event, Work
from metainfo.models import Uri, Collection
from apis.settings.NER_settings import autocomp_settings as ac_settings
from django.conf import settings
from .custom_autocompletes import *

from dal import autocomplete
from django.db.models import Q
from django import http
from django.contrib.contenttypes.models import ContentType

import requests
import json
import operator
from functools import reduce
import dateutil.parser
import re

from vocabularies.models import VocabsBaseClass


class CustomEntityAutocompletes(object):
    """A class for collecting all the custom autocomplete functions for one entity.

    Attributes:

    - self.entity: (string) entity types
    - self.more: (boolean) if more results can be fetched (pagination)
    - self.page_size: (integer) page size
    - self.results: (list) results
    - self.query: (string) query string

    Methods:
    - self.more(): fetch more results
    """

    def __init__(self, entity, query, page_size=20, offset=0, *args, **kwargs):
        """
        :param entity: (string) entity type to fetch additional autocompletes for
        """
        func_list = {}
        if entity not in func_list.keys():
            self.results = None
            return None
        res = []
        more = dict()
        more_gen = False
        for x in func_list[entity]:
            res2 = x().query(query, page_size, offset)
            if len(res2) == page_size:
                more[x.__name__] = (True, offset+1)
                more_gen = True
            res.extend(res2)
        self.results = res
        self.page_size = page_size
        self.more = more_gen
        self._more_dict = more
        self.query = query
        self.offset = offset

    def get_more(self):
        """
        Function to retrieve more results.
        """
        res4 = []
        for key, value in self._more_dict.items():
            if value[0]:
                res3 = globals()[key](self.query, self.page_size, value[1])
                if len(res3) == self.page_size:
                    self._more_dict[key] = (True, value[1]+1)
                else:
                    self._more_dict[key] = (False, value[1])
                self.results.extend(res3)
                res4.extend(res3)
        return res4


class GenericEntitiesAutocomplete(autocomplete.Select2ListView):

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

    def get(self, request, *args, **kwargs):
        page_size = 20
        offset = (int(self.request.GET.get('page', 1))-1)*page_size
        ac_type = self.kwargs['entity']
        db_include = self.kwargs.get('db_include', False)
        choices = []
        headers = {'Content-Type': 'application/json'}
        q = self.q
        ent_model = ContentType.objects.get(app_label='entities', model=ac_type).model_class()
        arg_list = [Q(**{x+'__icontains': q}) for x in settings.APIS_ENTITIES[ac_type.title()]['search']]
        res = ent_model.objects.filter(reduce(operator.or_, arg_list)).distinct()
        test_db = True
        test_stanbol = False
        test_stanbol_list = dict()
        more = True
        if not db_include:
            for r in res[offset:offset+page_size]:
                f = dict()
                dataclass = ""
                try:
                    f['id'] = Uri.objects.filter(entity=r)[0].uri
                except:
                    continue
                if hasattr(r, 'lng'):
                    if r.lng and r.lat:
                        dataclass = 'data-vis-tooltip="{}" data-lat="{}" \
                        data-long="{}"  class="apis-autocomplete-span"'.format(ac_type, r.lat, r.lng)
                f['text'] = '<span {}><small>db</small> {}</span>'.format(dataclass, str(r))
                choices.append(f)
            if len(choices) < page_size:
                test_db = False
        else:
            test_db = False
        if ac_type.title() in ac_settings.keys():
            for y in ac_settings[ac_type.title()]:
                ldpath = ""
                for d in y['fields'].keys():
                    ldpath += "{} = <{}>;\n".format(d, y['fields'][d][0])
                data = {
                    'limit': page_size,
                    'name': q,
                    'ldpath': ldpath,
                    'offset': offset
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
                if len(res['results']) < page_size:
                    test_stanbol_list[y['url']] = False
                else:
                    test_stanbol_list[y['url']] = True
                for x in res['results']:
                    f = dict()
                    dataclass = ""
                    name = x['name'][0]['value']
                    score = str(x[ac_settings['score']][0]['value'])
                    id = x[ac_settings['uri']]
                    score = score
                    f['id'] = id
                    source = y['source']
                    if 'lat' in x.keys() and 'long' in x.keys():
                        dataclass = 'data-vis-tooltip="{}" \
                        data-lat="{}" data-long="{}"'.format(
                            ac_type, x['lat'][0]['value'], x['long'][0]['value'])
                    if 'descr' in x.keys():
                        descr = x['descr'][0]['value']
                    else:
                        descr = None
                    f['text'] = '<span {} class="apis-autocomplete-span"><small>{}</small> <b>{}</b>\
                    ({}): {}</span>'.format(dataclass, source, name, score, descr)
                    choices.append(f)
            for k in test_stanbol_list.keys():
                if test_stanbol_list[k]:
                    test_stanbol = True
        else:
            test_stanbol = False
        cust_auto = CustomEntityAutocompletes(ac_type, q, page_size=page_size, offset=offset)
        cust_auto_more = False
        if cust_auto.results is not None:
            cust_auto_more = cust_auto.more
            if len(cust_auto.results) > 0:
                choices.extend(cust_auto.results)
        if not test_db and not test_stanbol and not cust_auto_more:
            more = False
        return http.HttpResponse(json.dumps({
            'results': choices + [],
            'pagination': {'more': more}
        }), content_type='application/json')


class GenericVocabulariesAutocomplete(autocomplete.Select2ListView):
    def get(self, request, *args, **kwargs):
        vocab = self.kwargs['vocab']
        direct = self.kwargs['direct']
        q = self.q
        vocab_model = ContentType.objects.get(app_label='vocabularies', model=vocab).model_class()
        if direct == 'normal':
            if vocab_model.__bases__[0] == VocabsBaseClass:
                choices = [{'id': x.pk, 'text': x.name} for x in vocab_model.objects.filter(name__icontains=q)]
            else:
                choices = [{'id': x.pk, 'text': x.label} for x in vocab_model.objects.filter(
                    Q(name__icontains=q) | Q(name_reverse__icontains=q))]
        elif direct == 'reverse':
            choices = [{'id': x.pk, 'text': x.label_reverse} for x in vocab_model.objects.filter(
                Q(name__icontains=q) | Q(name_reverse__icontains=q))]
        return http.HttpResponse(json.dumps({
            'results': choices + []
        }), content_type='application/json')


class GenericNetworkEntitiesAutocomplete(autocomplete.Select2ListView):
    def get(self, request, *args, **kwargs):
        entity = self.kwargs['entity']
        q = self.q
        if q.startswith('cl:'):
            res = Collection.objects.filter(name__icontains=q[3:])
            results = [{'id': 'cl:'+str(x.pk), 'text': x.name} for x in res]
        else:
            ent_model = ContentType.objects.get(app_label='entities', model=entity).model_class()
            arg_list = [Q(**{x + '__icontains': q}) for x in settings.APIS_ENTITIES[entity.title()]['search']]
            res = ent_model.objects.filter(reduce(operator.or_, arg_list)).distinct()
            results = [{'id': x.pk, 'text': str(x)} for x in res]
        return http.HttpResponse(json.dumps({
            'results': results
        }), content_type='application/json')
