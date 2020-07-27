#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import operator
import re
from functools import reduce

import dateutil.parser
import requests
from dal import autocomplete
from django import http
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldError
from django.db.models import Q

from apis_core.apis_metainfo.models import Uri, Collection
from apis_core.apis_vocabularies.models import VocabsBaseClass
from apis_core.default_settings.NER_settings import autocomp_settings as ac_settings
from .models import AbstractEntity


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
        ent_model = AbstractEntity.get_entity_class_of_name(ac_type)
        if self.q.startswith('http'):
            res = ent_model.objects.filter(uri__uri=self.q.strip())
        elif len(self.q) > 0:
            q1 = re.match('^([^\[]+)\[([^\]]+)\]$', self.q)
            if q1:
                q = q1.group(1).strip()
                q3 = q1.group(2).split(',')
                q3 = [e.strip() for e in q3]
            else:
                q = re.match('^[^\[]+', self.q).group(0)
                q3 = False
            if re.match('^[^*]+\*$', q.strip()):
                search_type = '__istartswith'
                q = re.match('^([^*]+)\*$', q.strip()).group(1)
            elif re.match('^\*[^*]+$', q.strip()):
                search_type = '__iendswith'
                q = re.match('^\*([^*]+)$', q.strip()).group(1)
            elif re.match('^\"[^"]+\"$', q.strip()):
                search_type = ''
                q = re.match('^\"([^"]+)\"$', q.strip()).group(1)
            elif re.match('^[^*]+$', q.strip()):
                search_type = '__icontains'
                q = q.strip()
            else:
                search_type = '__icontains'
                q = q.strip()
            arg_list = [Q(**{x+search_type: q}) for x in settings.APIS_ENTITIES[ac_type.title()]['search']]
            res = ent_model.objects.filter(reduce(operator.or_, arg_list)).distinct()
            if q3:
                f_dict2 = {}
                for fd in q3:
                    f_dict2[fd.split('=')[0].strip()] = fd.split('=')[1].strip()
                try:
                    res = res.filter(**f_dict2)
                except Exception as e:
                    choices.append({'name': str(e)})
        else:
            q = ''
            res = []
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
                if self.q.startswith('http'):
                    q = False
                    match_url_geo = re.search(r'geonames[^0-9]+([0-9]+)', self.q.strip())
                    if match_url_geo:
                        url = 'http://sws.geonames.org/{}/'.format(match_url_geo.group(1))
                    else:
                        url = self.q.strip()
                    params = {'id': url, 'ldpath': ldpath}
                    headers = {'Content-Type': 'application/json'}
                    w = requests.get(y['url'].replace('find', 'entity'), params=params, headers=headers)
                    res3 = dict()
                    ldpath_fields = [y['fields'][d][0] for d in y['fields'].keys()]
                    print(w.status_code)
                    if w.status_code == 200:
                        for x in w.json()['representation'].keys():
                            if x in ldpath_fields:
                                for d in y['fields'].keys():
                                    if y['fields'][d][0] == x:
                                        res3[d] = w.json()['representation'][x]
                        res = dict()
                        res3['id'] = w.json()['id']
                        res['results'] = [res3]
                    else:
                        continue
                else:

                    data = {
                        'limit': page_size,
                        'ldpath': ldpath,
                        'offset': offset,
                        'constraints': [{
                            "type": "text",
                            "patternType": "wildcard",
                            "field": "http://www.w3.org/2000/01/rdf-schema#label",
                            "text": q.split()
                        }]
                    }
                    if q3 and 'search fields' in y.keys():
                        for fd in q3:
                            fd = [fd2.strip() for fd2 in fd.split('=')]
                            if fd[0] in y['search fields'].keys():
                                fd3 = y['search fields'][fd[0]]
                                v = False
                                if isinstance(fd3[1], dict):
                                    if fd[1] in fd3[1].keys():
                                        v = fd3[1][fd[1]]
                                else:
                                    v = fd3[1](fd[1])
                                if fd3[2] == 'reference' and v:
                                    fd_4 = {
                                        'type': 'reference',
                                        'value': v,
                                        'field': fd3[0]
                                    }
                                    data['constraints'].append(fd_4)
                                elif fd3[2] == 'date_exact' and v:
                                    fd_4 = {
                                        'type': 'value',
                                        'value': v,
                                        'field': fd3[0],
                                        "datatype": "xsd:dateTime"
                                    }
                                    data['constraints'].append(fd_4)
                                elif fd3[2] == 'date_gt' and v:
                                    fd_4 = {
                                        'type': 'range',
                                        'lowerBound': v,
                                        'upperBound': "2100-12-31T23:59:59.999Z",
                                        'field': fd3[0],
                                        "datatype": "xsd:dateTime"
                                    }
                                    data['constraints'].append(fd_4)
                                elif fd3[2] == 'date_lt' and v:
                                    fd_4 = {
                                        'type': 'range',
                                        'lowerBound': "1-01-01T23:59:59.999Z",
                                        'upperBound': v,
                                        'field': fd3[0],
                                        "datatype": "xsd:dateTime"
                                    }
                                    data['constraints'].append(fd_4)
                            else:
                                choices.append({'name': 'No additional query setting for Stanbol'})
                    try:
                        url2 = y['url'].replace('find', 'query')
                        r = requests.post(url2, data=json.dumps(data), headers=headers)
                        if r.status_code != 200:
                            choices.append({'name': 'Connection to Stanbol failed'})
                            continue
                        res = r.json()
                    except Exception as e:
                        choices.append({'name': 'Connection to Stanbol failed'})
                        print(e)
                        continue
                if len(res['results']) < page_size:
                    test_stanbol_list[y['url']] = False
                else:
                    test_stanbol_list[y['url']] = True
                for x in res['results']:
                    f = dict()
                    dataclass = ""
                    name = x['name'][0]['value']
                    if ac_settings['score'] in x.keys():
                        score = str(x[ac_settings['score']][0]['value'])
                    else:
                        score = 'NA'
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
        cust_auto_more = False
        if q:
            cust_auto = CustomEntityAutocompletes(ac_type, q, page_size=page_size, offset=offset)
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
        page_size = 20
        offset = (int(self.request.GET.get('page', 1))-1)*page_size
        more = False
        vocab = self.kwargs['vocab']
        direct = self.kwargs['direct']
        q = self.q
        vocab_model = ContentType.objects.get(app_label='apis_vocabularies', model=vocab).model_class()
        if direct == 'normal':
            if vocab_model.__bases__[0] == VocabsBaseClass:
                choices = [{'id': x.pk, 'text': x.label} for x in vocab_model.objects.filter(name__icontains=q).order_by('parent_class__name', 'name')[offset:offset+page_size]]
            else:
                choices = [{'id': x.pk, 'text': x.label} for x in vocab_model.objects.filter(
                    Q(name__icontains=q) | Q(name_reverse__icontains=q)).order_by('parent_class__name', 'name')[offset:offset+page_size]]
        elif direct == 'reverse':
            choices = [{'id': x.pk, 'text': x.label_reverse} for x in vocab_model.objects.filter(
                Q(name__icontains=q) | Q(name_reverse__icontains=q)).order_by('parent_class__name', 'name')[offset:offset+page_size]]
        if len(choices) == page_size:
            more = True
        return http.HttpResponse(json.dumps({
            'results': choices + [],
            'pagination': {'more': more}
        }), content_type='application/json')


class GenericNetworkEntitiesAutocomplete(autocomplete.Select2ListView):
    def get(self, request, *args, **kwargs):
        entity = self.kwargs['entity']
        q = self.q
        if q.startswith('cl:'):
            res = Collection.objects.filter(name__icontains=q[3:])
            results = [{'id': 'cl:'+str(x.pk), 'text': x.name} for x in res]
        elif q.startswith('reg:'):
            results = []
            if entity.lower() == 'person':
                filen = 'reg_persons.json'
            elif entity.lower() == 'place':
                filen = 'reg_places.json'
            with open(filen, 'r') as reg:
                r1 = json.load(reg)
                r_dict = dict()
                for r2 in r1:
                    if q[4:].lower() in r2[1].lower():
                        if r2[1] in r_dict.keys():
                            r_dict[r2[1]] += "|{}".format(r2[0])
                        else:
                            r_dict[r2[1]] = r2[0]
            for k in r_dict.keys():
                results.append({'id': 'reg:'+r_dict[k], 'text': k})

        else:
            ent_model = ContentType.objects.get(
                app_label__startswith='apis_', model=entity
            ).model_class()
            try:
                arg_list = [
                    Q(
                        **{x + '__icontains': q}
                    ) for x in settings.APIS_ENTITIES[entity.title()]['search']
                ]
            except KeyError:
                arg_list = [
                    Q(
                        **{x + '__icontains': q}
                    ) for x in ['name']
                ]
            try:
                res = ent_model.objects.filter(reduce(operator.or_, arg_list)).distinct()
            except FieldError:
                arg_list = [
                    Q(
                        **{x + '__icontains': q}
                    ) for x in ['text']
                ]
                res = ent_model.objects.filter(reduce(operator.or_, arg_list)).distinct()
            results = [{'id': x.pk, 'text': str(x)} for x in res]
        return http.HttpResponse(json.dumps({
            'results': results
        }), content_type='application/json')
