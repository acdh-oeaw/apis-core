#!/usr/bin/python
# -*- coding: utf-8 -*-
import autocomplete_light.shortcuts as al
from django.utils.encoding import force_text
from vocabularies.models import (PersonInstitutionRelation, PersonPersonRelation, PersonPlaceRelation,
                                 PersonEventRelation, InstitutionEventRelation, PlaceEventRelation,
                                 RelationBaseClass, VocabsBaseClass, InstitutionInstitutionRelation,
                                 InstitutionPlaceRelation, PersonWorkRelation, InstitutionWorkRelation,
                                 PlaceWorkRelation, EventWorkRelation, PlacePlaceRelation)

import requests
import re, copy

lst_schemes = {'Oebl_brg': 'http://acdh.oeaw.ac.at/vocabs/professions/oebl/'}


class OpenSkosAutocompleteBase(al.AutocompleteListTemplate):
    autocomplete_template = 'autocomplete/openskos.html'
    base_url = 'https://clarin.oeaw.ac.at/vocabs/api/find-concepts'

    attrs = {
        'data-autocomplete-minimum-characters': 3,
        'placeholder': u'Start typing to get suggestions',
        'class': 'autocomplete-ort-uri form-control'
    }

    def parse_search(self):
        q = self.request.GET.get('q')
        if q:
            qp = re.match(r'^(?P<scheme>\[[^\]]+\])?(?P<query>.*)$', q)
            if qp.group('scheme'):
                s = qp.group('scheme').strip('[]').split('#')
                self.scheme = [x.strip() for x in s]
            if qp.group('query'):
                s = qp.group('query').split('#')
                self.query = [x.strip() for x in s]
        else:
            self.scheme = []
            self.query = []

    def choices_for_request(self):
        def run_through_dict(dict2, items, level=0, list2=[]):
            for k, v in dict2.items():
                f = dict()
                if 'broader' not in items[k].keys():
                    level = 0
                #print(items[k])
                ff = level+(len(items[k]['prefLabel'][0]))
                if level > 0:
                    f['name'] = '|{:_>{}s}'.format(items[k]['prefLabel'][0], ff)
                else:
                    f['name'] = items[k]['prefLabel'][0]
                f['uri'] = k
                list2.append(f)
                if isinstance(v, dict):
                    level += 1
                    list2 = run_through_dict(v, items, level, list2)
                    level -= 1
            return list2

        def set_path(someDict, path, value):
            for x in path[::-1]:
                value = {x: value}
            return deepupdate(someDict, value)


        def deepupdate(original, update):
            for key, value in original.items():
                if not key in update:
                    update[key] = value
                elif isinstance(value, dict):
                    deepupdate(value, update[key])
            return update

        def get_elem_uri(dict2, value):
            if value not in dict2.keys():
                headers = {'Content-Type': 'application/json'}
                data = {'format': 'json', 'id': value}
                r = requests.get(self.base_url, params=data, headers=headers)
                res = r.json()
                dict2[value] = res
            return dict2, dict2[value]


        self.parse_search()
        headers = {'Content-Type': 'application/json'}
        scheme_str = ' OR '.join(self.scheme)
        prev_elem = None
        counter = 0
        choices = []
        for x in self.query:
            if len(x) > 0:
                counter += 1
                if prev_elem:
                    data = {'format': 'json',
                            'q': '(inScheme:"{}") AND \
                            {}* AND ({})'.format(scheme_str, x, prev_elem)}
                else:
                    data = {'format': 'json',
                            'q': '(inScheme:"{}") AND {}*'.format(scheme_str, x)}
                r = requests.get(self.base_url, params=data, headers=headers)
                res = r.json()
                if counter < len(self.query):
                    prev_elem2 = []
                    for x in res['response']['docs']:
                        prev_elem2.append(x['uri'])
                    prev_elem = ' OR '.join(['broader:"{}"'.format(x) for x in prev_elem2])
                else:
                    dict_res = {i['uri']: i for i in res['response']['docs']}
                    lst_proof = []
                    dict_res2 = dict()
                    for x in dict_res.keys():
                        if 'broader' not in dict_res[x].keys():
                            lst_proof.append(x)
                            dict_res2[x] = dict()
                    dict_res_bak = copy.deepcopy(dict_res)
                    lst_proof = []
                    lst_obj_fin = []
                    for x in dict_res_bak.keys():
                        if dict_res_bak[x]['uri'] not in lst_proof:
                            list_obj = []
                            check = dict_res_bak[x]['uri']
                            while check:
                                list_obj.insert(0, check)
                                if 'broader' in dict_res[check].keys():
                                    dict_res = get_elem_uri(dict_res, dict_res[check]['broader'][0])[0]
                                    check = dict_res[check]['broader'][0]
                                else:
                                    dict_res2[check] = dict()
                                    check = False
                        lst_obj_fin.append(list_obj)
                    lst_obj_fin = sorted(lst_obj_fin, key=len)
                    for a in lst_obj_fin:
                        dict_res2 = set_path(dict_res2, a, dict())
                    choices = run_through_dict(dict_res2, dict_res)
        return choices

    def __init__(self, *args, **kwargs):
        super(OpenSkosAutocompleteBase, self).__init__(*args, **kwargs)


class VocabsAutocompleteBase(al.AutocompleteListTemplate):
    autocomplete_template = 'autocomplete/vocabs_base.html'

    attrs = {
        'data-autocomplete-minimum-characters': 3,
        'placeholder': u'Start typing to get suggestions',
        #'class': 'autocomplete-ort-uri form-control'
    }

    def choices_for_request(self):
        q = self.request.GET.get('q')
        res = []
        for d in self.vocabs:
            for x in d.objects.filter(name__icontains=q):
                res.append(x)
        return res


class VocabsAutocompleteBase2(al.AutocompleteModelTemplate):
    autocomplete_template = 'autocomplete/vocabs_base2.html'
    attrs = {
    'display': 'block'
    }

    def choice_label(self, choice):
        # if type(choice) is VocabsBaseClass:
        #     choice = RelationBaseClass.objects.get(pk=choice.pk)
        # d = choice
        # res = getattr(choice, self.choice_attr)
        # while d.parent_class:
        #     f = d.parent_class
        #     if type(f) is VocabsBaseClass:
        #         f = RelationBaseClass.objects.get(pk=f.pk)
        #     res = getattr(f, self.choice_attr) + ' >> ' + res
        #     d = f
        if self.reverse:
            res = choice.label_reverse
        else:
            res = choice.label
        return force_text(res)

    def choices_for_request(self):
        if self.request.user.is_superuser:
            self.choices = self.choices.all()
        else:
            self.choices = self.choices.filter(userAdded__groups__in=self.request.user.groups.all())
        return super(VocabsAutocompleteBase2, self).choices_for_request()

    def order_choices(self, choices):
        lst_choices = []
        for x in choices:
            lst2 = [x]
            x.label = self.choice_label(x)
            d = x
            while d.parent_class:
                lst2.append(d.parent_class)
                d = d.parent_class
            lst_choices.append(lst2)
        result = []
        lst_choices_sort = sorted(lst_choices, key=lambda x: '_'.join([z.name for z in reversed(x)]))
        for x in lst_choices_sort:
            result.append(x[0])
        return result

    def __init__(self, *args, **kwargs):
        if self.reverse:
            self.choice_attr = 'name_reverse'
        else:
            self.choice_attr = 'name'
        super(VocabsAutocompleteBase2, self).__init__(*args, **kwargs)



class OSProfessionsAutocomplete(OpenSkosAutocompleteBase):
    scheme = ['http://acdh.oeaw.ac.at/vocabs/professions/oebl/']


# class VCPersonInstitutionAutocomplete(VocabsAutocompleteBase):
#     vocabs = [PersonInstitutionRelation]

class VCPersonInstitutionAutocomplete(VocabsAutocompleteBase2):
    search_fields = ('name',)
    choices = PersonInstitutionRelation.objects.all()
    reverse = False


class VCPersonInstitutionReverseAutocomplete(VCPersonInstitutionAutocomplete):
    search_fields = ('name_reverse', )
    reverse = True


class VCPersonPlaceAutocomplete(VocabsAutocompleteBase2):
    search_fields = ('name',)
    choices = PersonPlaceRelation.objects.all()
    reverse = False


class VCPersonPlaceReverseAutocomplete(VCPersonPlaceAutocomplete):
    search_fields = ('name_reverse', )
    reverse = True


class VCPersonPersonAutocomplete(VocabsAutocompleteBase2):
    search_fields = ('name', )
    choices = PersonPersonRelation.objects.all()
    reverse = False


class VCPersonEventAutocomplete(VocabsAutocompleteBase2):
    search_fields = ('name', )
    choices = PersonEventRelation.objects.all()
    reverse = False


class VCPersonEventReverseAutocomplete(VCPersonEventAutocomplete):
    search_fields = ('name_reverse', )
    reverse = True


class VCInstitutionEventAutocomplete(VocabsAutocompleteBase2):
    search_fields = ('name', )
    choices = InstitutionEventRelation.objects.all()
    reverse = False


class VCInstitutionEventReverseAutocomplete(VCInstitutionEventAutocomplete):
    search_fields = ('name_reverse', )
    reverse = True


class VCInstitutionInstitutionAutocomplete(VocabsAutocompleteBase2):
    search_fields = ('name', )
    choices = InstitutionInstitutionRelation.objects.all()
    reverse = False


class VCInstitutionInstitutionReverseAutocomplete(VCInstitutionInstitutionAutocomplete):
    search_fields = ('name_reverse',)
    reverse = True


class VCInstitutionPlaceAutocomplete(VocabsAutocompleteBase2):
    search_fields = ('name',)
    choices = InstitutionPlaceRelation.objects.all()
    reverse = False


class VCInstitutionPlaceReverseAutocomplete(VCInstitutionPlaceAutocomplete):
    search_fields = ('name_reverse',)
    reverse = True


class VCPlaceEventAutocomplete(VocabsAutocompleteBase2):
    search_fields = ('name', )
    choices = PlaceEventRelation.objects.all()
    reverse = False


class VCPlaceEventReverseAutocomplete(VCPlaceEventAutocomplete):
    search_fields = ('name_reverse', )
    reverse = True


class VCPlacePlaceAutocomplete(VocabsAutocompleteBase2):
    search_fields = ('name', )
    choices = PlacePlaceRelation.objects.all()
    reverse = False


class VCPlacePlaceReverseAutocomplete(VCPlacePlaceAutocomplete):
    search_fields = ('name_reverse',)
    reverse = True


class VCPersonPersonReverseAutocomplete(VCPersonPersonAutocomplete):
    search_fields = ('name_reverse',)
    reverse = True


class VCPersonWorkAutocomplete(VocabsAutocompleteBase2):
    search_fields = ('name', )
    choices = PersonWorkRelation.objects.all()
    reverse = False


class VCPersonWorkReverseAutocomplete(VCPersonWorkAutocomplete):
    search_fields = ('name_reverse',)
    reverse = True


class VCInstitutionWorkAutocomplete(VocabsAutocompleteBase2):
    search_fields = ('name', )
    choices = InstitutionWorkRelation.objects.all()
    reverse = False


class VCInstitutionWorkReverseAutocomplete(VCInstitutionWorkAutocomplete):
    search_fields = ('name_reverse',)
    reverse = True


class VCPlaceWorkAutocomplete(VocabsAutocompleteBase2):
    search_fields = ('name', )
    choices = PlaceWorkRelation.objects.all()
    reverse = False


class VCPlaceWorkReverseAutocomplete(VCPlaceWorkAutocomplete):
    search_fields = ('name_reverse',)
    reverse = True


class VCEventWorkAutocomplete(VocabsAutocompleteBase2):
    search_fields = ('name', )
    choices = EventWorkRelation.objects.all()
    reverse = False


class VCEventWorkReverseAutocomplete(VCEventWorkAutocomplete):
    search_fields = ('name_reverse',)
    reverse = True


al.register(OSProfessionsAutocomplete)
al.register(VCPersonInstitutionAutocomplete)
al.register(VCPersonPlaceAutocomplete)
al.register(VCPersonPersonAutocomplete)
al.register(VCPersonEventAutocomplete)
al.register(VCInstitutionEventAutocomplete)
al.register(VCPlaceEventAutocomplete)
al.register(VCPersonPersonReverseAutocomplete)
al.register(VCInstitutionInstitutionAutocomplete)
al.register(VCInstitutionInstitutionReverseAutocomplete)
al.register(VCPersonInstitutionReverseAutocomplete)
al.register(VCPersonPlaceReverseAutocomplete)
al.register(VCPersonEventReverseAutocomplete)
al.register(VCInstitutionEventReverseAutocomplete)
al.register(VCPlaceEventReverseAutocomplete)
al.register(VCInstitutionPlaceAutocomplete)
al.register(VCInstitutionPlaceReverseAutocomplete)
al.register(VCPersonWorkAutocomplete)
al.register(VCPersonWorkReverseAutocomplete)
al.register(VCInstitutionWorkAutocomplete)
al.register(VCInstitutionWorkReverseAutocomplete)
al.register(VCPlaceWorkAutocomplete)
al.register(VCPlaceWorkReverseAutocomplete)
al.register(VCEventWorkAutocomplete)
al.register(VCEventWorkReverseAutocomplete)
al.register(VCPlacePlaceAutocomplete)
al.register(VCPlacePlaceReverseAutocomplete)
