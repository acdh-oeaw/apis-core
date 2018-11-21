#!/usr/bin/python
# -*- coding: utf-8 -*-
from apis_core.apis_entities.models import Place, Institution, Person, Work
from apis_core.apis_relations.models import (
    InstitutionInstitution, InstitutionPlace, PersonPerson,
    PersonWork, PersonPlace, PersonInstitution, PlacePlace, PlaceEvent, PlaceWork)
from apis_core.apis_metainfo.models import Uri as genUri
from apis_core.apis_labels.models import Label
from apis_core.apis_vocabularies.models import (
    LabelType, InstitutionInstitutionRelation,
    InstitutionPlaceRelation, VocabsUri, ProfessionType, PersonWorkRelation,
    PersonPersonRelation, PersonPlaceRelation, WorkType, PersonInstitutionRelation,
    PlaceType, PlacePlaceRelation)
from apis_core.default_settings.NER_settings import geonames_feature_codes as gn_f
from apis_core.default_settings.RDF_settings import sett_RDF_generic
from apis_core.apis_metainfo.models import Collection, Uri

import rdflib
from rdflib import ConjunctiveGraph, URIRef, RDFS, Literal, OWL
import re
from datetime import datetime
import types
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.core.exceptions import FieldError


def harmonize_geonames_id(uri):

    """checks if a geonames Url points to geonames' rdf expression"""

    if uri.startswith("http://www.geonames.org/"):
        geo_id = "".join(re.findall(r'\d', uri))
        return "http://sws.geonames.org/{}".format(geo_id)

    elif uri.startswith("http://geonames.org/"):
        geo_id = "".join(re.findall(r'\d', uri))
        return "http://sws.geonames.org/{}".format(geo_id)
    # elif uri.endswith('/'):
    #     return uri[:-1]

    else:
        return uri


class GenericRDFParser(object):
    """A generic class for parsing RDFs to the APIS data model and save
    objects to the db.

    Attributes:

    - self.objct: (object) the object created by the parser

    - self.labels: (list) list of labels created by the parser (only saved when self.save() is called)

    - self.related_objcts: (list) list of related objects (relations) (only saved when self.save() is called)

    - self.kind: (string) kind of entity of the object (Persion, Place, Institution, Work, Event)

    - self.uri: (string) uri provided when initializing the object

    - self.saved: (boolean) indicates whether the object was saved to the db

    - self.created: (boolean) indicates whether the object was created
    """

    def save(self):
        """
        :return: django object saved to db or False if nothing was saved
        """
        if not self.created:
            return False
        self.objct.status = 'distinct'
        self.objct.save()
        def_coll, created = Collection.objects.get_or_create(name='Default import collection')
        self.objct.collection.add(def_coll)
        self.saved = True
        Uri.objects.create(uri=self.uri, entity=self.objct)
        for lab in self.labels:
            lab.temp_entity = self.objct
            lab.save()
        for obj in self.related_objcts:
            if hasattr(obj, 'related_'+self.kind.lower()+'B'):
                setattr(obj, 'related_' + self.kind.lower() + 'A_id', self.objct.pk)
            else:
                setattr(obj, 'related_'+self.kind.lower()+'_id', self.objct.pk)
            obj.save()
        return self.objct

    def merge(self, m_obj, app_label_relations='apis_relations'):
        """
        :param m_obj: the object to merge with (must be an django model object instance)
        :param app_label_relations: (string) the label of the Django app that contains the relations
        :return: django object saved to db or False if nothing was saved
        """
        for rel in ContentType.objects.filter(app_label=app_label_relations, model__icontains=self.kind.lower()):
            rel_q = {'related_' + self.kind.lower(): m_obj}
            rel2 = rel.model_class()
            try:
                for rel_exst in rel2.objects.filter(**rel_q):
                    setattr(rel_exst, 'related_'+self.kind.lower()+'_id', self.objct.pk)
                    rel_exst.save()
            except FieldError:  # e.g. PlacePlace relations have different related_ fields
                rel_q = {'related_' + self.kind.lower()+'A': m_obj}
                for rel_exst in rel2.objects.filter(**rel_q):
                    setattr(rel_exst, 'related_'+self.kind.lower()+'A_id', self.objct.pk)
                    rel_exst.save()
                rel_q = {'related_' + self.kind.lower() + 'B': m_obj}
                for rel_exst in rel2.objects.filter(**rel_q):
                    setattr(rel_exst, 'related_'+self.kind.lower()+'B_id', self.objct.pk)
                    rel_exst.save()
        for z in genUri.objects.filter(entity=m_obj):
            z.entity_id = self.objct.pk
            z.save()
        for z in Label.objects.filter(temp_entity=m_obj):
            z.temp_entity_id = self.objct.pk
            z.save()
        if hasattr(m_obj, 'first_name'):
            legacy_name = '{}, {}'.format(m_obj.name, m_obj.first_name)
        else:
            legacy_name = m_obj.name
        lt, created = LabelType.objects.get_or_create(name='legacy name')
        Label.objects.create(temp_entity_id=self.objct.pk, label=legacy_name, label_type=lt)
        for col in m_obj.collection.all():
            self.objct.collection.add(col)
        if 'apis_highlighter' in settings.INSTALLED_APPS:
            for ann in m_obj.annotation_set.all():  # Todo: check if this works now with highlighter
                ann.entity_link.remove(m_obj)
                ann.entity_link.add(self.objct)
        for txt in m_obj.text.all():
            self.objct.text.add(txt)
        if m_obj.source:
            self.objct.source = m_obj.source
            self.objct.save()
        m_obj.delete()
        return self.objct

    def get_or_create(self):
        """
        :return: Returns the parsed object. Saves it to the db when needed
        """
        if not self.created:
            return self.objct
        else:
            if not self.saved:
                ob = self.save()
                return ob
            else:
                return self.objct

    def __init__(self, uri, kind, app_label_entities="apis_entities",
                 app_label_relations="apis_relations", app_label_vocabularies="apis_vocabularies", **kwargs):
        """
        :param uri: (url) Uri to parse the object from (http://test.at). The uri must start with a base url mentioned in the RDF parser settings file.
        :param kind: (string) Kind of entity (Person, Place, Institution, Work, Event)
        :param app_label_entities: (string) Name of the Django app that contains the entities that we create.
        :param app_label_relations: (string) Name of the Django app that contains the relations for the merging process.
        :param app_label_vocabularies: (string) Name of the Django app that contains the vocabularies defining the entities and relations.
        """
        owl = "http://www.w3.org/2002/07/owl#"

        def exist(uri):
            if objct.objects.filter(uri__uri=uri).count() > 0:
                return True, objct.objects.get(uri__uri=uri)
            else:
                return False, False

        def prep_string(tupl):
            if isinstance(tupl, str):
                res = tupl
            elif tupl[1]:
                m = re.match(tupl[1][0], tupl[0])
                group = tupl[1][1]
                if not group:
                    group = 0
                try:
                    res = m.group(group)
                except:
                    res = tupl[0]
            else:
                res = tupl[0]
            if len(res) > 255:
                res = res[:250] + '...'
            return res.strip()
        objct = ContentType.objects.get(app_label=app_label_entities, model=kind.lower()).model_class()
        force = kwargs.get('force', None)
        res_attrb = dict()
        labels = []
        related_objcts = []
        uri = harmonize_geonames_id(uri)
        self.uri = uri
        self.kind = kind
        self.saved = False
        test = exist(self.uri)
        if test[0] and not force:
            self.objct = test[1]
            self.created = False
        else:
            self.created = True
            rdf_t = dict()
            for x in sett_RDF_generic[kind]['data']:
                self.settings_defined = False
                if not uri.startswith(x['base_url']):
                    continue
                self.settings_defined = True
                g = rdflib.Graph()
                uri_2 = uri
                if not uri_2.endswith('/'):
                    uri_2 += '/'
                o2 = rdflib.term.URIRef(uri)
                g.parse('{}{}'.format(uri_2.strip(), x['url_appendix']), format='xml')
                sameas = rdflib.term.URIRef(owl+'sameAs')
                list_sameas = []
                for p in g.objects(subject=o2, predicate=sameas):
                    list_sameas.append(genUri(uri=p))
                self.sameas = list_sameas
                if 'kind' in x.keys():
                    for k in x['kind']:
                        kind_rdf = rdflib.term.URIRef(k[0])
                        kind_val = g.value(o2, kind_rdf)
                        if kind_val is not None:
                            break
                        else:
                            kind_val = k[1]
                    if kind_val is not None:
                        kind_objct = ContentType.objects.get(
                        app_label=app_label_vocabularies, model=kind.lower() + 'Type'.lower()).model_class()
                        kind_objct, created = kind_objct.objects.get_or_create(name=kind_val)
                        res_attrb['kind'] = kind_objct
                for uri_2 in list_sameas:
                    test = exist(uri_2)
                    if test[0]:
                        self.objct = test[1]
                        self.created = False
                        uri_3 = genUri(uri=uri, entity=self.objct)
                        uri_3.save()
                for xx in x['attributes']:
                    rdf_t[xx['name']] = ()
                    subj2 = []
                    results = []
                    ind_type = ()
                    for z in xx['identifiers']:
                        if len(results) > 0:
                            continue
                        cnt = 0
                        cnt_2 = 1
                        try:
                            k = z[cnt_2]
                        except:
                            k = '='
                        subj = [o2, ]
                        while k:
                            for indx, s in enumerate(subj):
                                if z[cnt][0] == 'objects':
                                    pred = rdflib.term.URIRef(z[cnt][2])
                                    res = g.objects(subject=s, predicate=pred)
                                    if type(res) != types.GeneratorType:
                                        break
                                    for r in res:
                                        if z[cnt][3]:
                                            if not getattr(r, z[cnt][3][0]) == z[cnt][3][1]:
                                                continue
                                        if k == '>':
                                            subj2.append(r)
                                        elif k == '=':
                                            results.append((z[cnt][1], r, indx))
                                            ind_type += ((len(ind_type), z[cnt][1]),)
                            cnt_2 += 2
                            try:
                                k = z[cnt_2]
                            except:
                                k = '='
                            if cnt + 2 > len(z):
                                k = None
                            cnt += 2
                            subj = subj2
                    for attrb in sett_RDF_generic[kind]['matching']['attributes'].keys():
                        res_2 = []
                        for x in sett_RDF_generic[kind]['matching']['attributes'][attrb]:
                            for s in x:
                                for ind, elem in filter(lambda x: x[1] == s[0], ind_type):
                                    elem = results[ind][1]
                                    res_2.append(prep_string((elem, s[1])))
                                if isinstance(s, str):
                                    res_2.append(s)
                        if len(res_2) == len(x):
                            res_attrb[attrb] = ''.join(res_2)
                    for lab in sett_RDF_generic[kind]['matching']['labels'].keys():
                        lb_type, created = LabelType.objects.get_or_create(name=lab)
                        for x in sett_RDF_generic[kind]['matching']['labels'][lab]:
                            for ind, elem in filter(lambda a: a[1]==x[0], ind_type):
                                elem = results[ind][1]
                                lb = Label(label=prep_string((elem, x[1])), isoCode_639_3=elem.language, label_type=lb_type)
                                labels.append(lb)
                    if kwargs.get('drill_down', True):
                        for con in sett_RDF_generic[kind]['matching']['linked objects']:
                            for x in con['object']:
                                for ind, elem in filter(lambda a: a[1]==x[0], ind_type):
                                    elem = results[ind][1]
                                    ob = GenericRDFParser(elem, con['type'], drill_down=False)
                                    if ob.created and not ob.saved:
                                        ob.save()   # TODO: We should move the save of related objects in the save routine
                                    try:
                                        u = ContentType.objects.get(app_label=app_label_relations, model=kind.lower()+con['type'].lower())
                                        u_kind = ContentType.objects.get(app_label=app_label_vocabularies, model=kind.lower()+con['type'].lower()+'Relation'.lower())
                                    except ContentType.DoesNotExist:
                                        u = ContentType.objects.get(app_label=app_label_relations, model=con['type'].lower()+kind.lower())
                                        u_kind = ContentType.objects.get(app_label=app_label_vocabularies, model=con['type'].lower()+kind.lower()+'Relation'.lower())
                                    u_kind_2 = u_kind.model_class()
                                    u2 = u.model_class()()
                                    uk, created = u_kind_2.objects.get_or_create(name=con['kind'])
                                    if con['type'] == kind:
                                        setattr(u2, 'related_' + con['type'].lower() + 'B_id', ob.objct.pk)
                                    else:
                                        setattr(u2, 'related_' + con['type'].lower() + '_id', ob.objct.pk)
                                    setattr(u2, 'relation_type_id', uk.pk)
                                    related_objcts.append(u2)
            self.objct = objct(**res_attrb)
            self.labels = labels
            self.related_objcts = related_objcts
