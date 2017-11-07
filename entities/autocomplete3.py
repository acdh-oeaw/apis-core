#!/usr/bin/python
# -*- coding: utf-8 -*-
from entities.models import Place, Person, Institution, Event, Work
from metainfo.models import Uri, Collection
from apis.settings.NER_settings import autocomp_settings as ac_settings
from django.conf import settings

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
        ac_type = self.kwargs['entity']
        choices = []
        headers = {'Content-Type': 'application/json'}
        q = self.q
        ent_model = ContentType.objects.get(app_label='entities', model=ac_type).model_class()
        arg_list = [Q(**{x+'__icontains': q}) for x in settings.APIS_ENTITIES[ac_type.title()]['search']]
        res = ent_model.objects.filter(reduce(operator.or_, arg_list)).distinct()
        for r in res:
            f = dict()
            try:
                f['id'] = Uri.objects.filter(entity=r)[0].uri
            except:
                continue
            f['text'] = '<small>db</small> {}'.format(str(r))
            choices.append(f)
        for y in ac_settings[ac_type.title()]:
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
                score = score
                f['id'] = id
                source = y['source']
                if 'descr' in x.keys():
                    descr = x['descr'][0]['value']
                else:
                    descr = None
                f['text'] = '<small>{}</small> <b>{}</b> ({}): {}'.format(source, name, score, descr)
                choices.append(f)
        return http.HttpResponse(json.dumps({
            'results': choices + []
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