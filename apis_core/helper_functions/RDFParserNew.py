import json
import os
import re
import string

import pandas as pd
import rdflib
import yaml
from django.contrib.contenttypes.models import ContentType
from rdflib import URIRef, RDFS
from rdflib.namespace import SKOS

from apis_core.apis_labels.models import Label
from apis_core.apis_vocabularies.models import LabelType
from apis_core.default_settings.RDF_settings_new import sett_RDF_generic, sameAs
from apis_core.apis_metainfo.models import Uri as genUri, Collection, Uri
from django.db.models.fields import CharField as TCharField
from django.db.models.fields import FloatField as TFloatField
from django.db.models.fields.related import ForeignKey as TForeignKey
from django.db.models.fields.related import ManyToManyField as TManyToMany
from django.conf import settings

from apis_core.helper_functions.RDFparsers import harmonize_geonames_id


class PartialFormatter(string.Formatter):

    def __init__(self, missing='not specified', bad_fmt='!!'):
        self.missing, self.bad_fmt = missing, bad_fmt

    def get_field(self, field_name, args, kwargs):
        try:
            val = super().get_field(field_name, args, kwargs)
        except (KeyError, AttributeError):
            val = None, field_name
        return val 

    def format_field(self, value, spec):
        if value is None:
            return self.missing
        try:
            return super(PartialFormatter, self).format_field(value, spec)
        except ValueError:
            if self.bad_fmt is not None:
                return self.bad_fmt
            else:
                raise


fmt = PartialFormatter()


class RDFParserNew(object):
    @property
    def _settings(self):
        """
        Reads settings file and saves it
        :return: (dict) dict of settings file
        """
        base_dir = getattr(settings, 'BASE_DIR')
        sett_file = os.path.join(base_dir, getattr(settings, 'APIS_GENERICRDF_SETTINGS', 'apis_core/default_settings/RDF_default_settings.yml'))
        sett = yaml.load(open(sett_file, 'r'))
        res = {'data': []}
        for v in sett[self.kind]['data']:
            if v['base_url'] in self.uri:
                res['data'] = v
        res['matching'] = sett[self.kind]['matching']
        res['sameAs'] = sameAs
        print(res)
        return res

    def _parse(self):
        """
        Parses the URI with the definition in the settings file
        :return: (dict) dict of Pandas DataFrames containing the variables obtained from SPARQL query
        """
        g = rdflib.Graph()
        g.parse(f"{self.uri}")
        self._graph = g
        res = dict()
        for s in self._settings['data']['attributes']:
            sp = s.get('sparql', False)
            if sp:
                print(sp)
                sp2 = self._sparql_to_pandas(g.query(sp, initBindings={'subject': URIRef(self.uri)}))
                res[s.get('name', 'no identifier provided')] = pd.DataFrame(sp2)
        self._attributes = res
        return res

    def _add_same_as(self):
        """
        adds the same as links as defined in the settings to the entity
        """
        for sa in self._settings['sameAs']:
            for su in self._graph.objects((self._subject, URIRef(sa))):
                Uri.objects.create(uri=su, entity=self.objct)

    def get_or_create(self, depth=2):
        """
        Gets or creates object with given URI and entity type.
        :param depth: (int) depth of related objects to be followed
        :return: (object) created object
        """
        if not self.created:
            return self.objct
        else:
            if not self.saved:
                self.create_objct(depth=depth)
                ob = self.save()
                return ob
            else:
                return self.objct

    def save(self):
        """
        Saves specified object to DB if it doesnt exist yet
        :return: django object saved to db or False if nothing was saved
        """

        if not self.created:
            return False

        exist = genUri.objects.filter(uri=self.uri)
        if exist.count() > 0:
            if exist[0].entity is not None:
                return exist[0].entity
        self.objct.status = 'distinct'
        for obj in self._foreign_keys:
            attr2, created = obj[1].objects.get_or_create(**obj[2])
            setattr(self.objct, obj[0], attr2)
        self.objct.save()
        def_coll, created = Collection.objects.get_or_create(name='Default import collection')
        self.objct.collection.add(def_coll)
        self.saved = True
        self._objct_uri.entity = self.objct
        self._objct_uri.save()
        self._add_same_as()
        lab_new = []
        for lab in self.labels:
            lt, created = LabelType.objects.get_or_create(name=lab[2])
            l1 = Label.objects.create(label=lab[0], label_type=lt, temp_entity=self.objct)
            lab_new.append(l1)
        self.labels = lab_new
        rel_obj_new = []
        for obj in self._m2m:
            attr2, created = obj[1].objects.get_or_create(**obj[2])
            getattr(self.objct, obj[0]).add(attr2)
        for obj in self.related_objcts:
            print(obj)
            for u3 in obj[1]:
                ent1 = RDFParserNew(u3, obj[2]).get_or_create(depth=0)
                print(obj[2], self._app_label_relations, self.kind)
                if obj[2].lower() == self.kind.lower():
                    mod = ContentType.objects.get(model=f"{self.kind.lower()*2}", app_label=self._app_label_relations).model_class()()
                    setattr(mod, 'related_' + self.kind.lower() + 'A_id', self.objct.pk)
                    setattr(mod, 'related_' + self.kind.lower() + 'B_id', ent1.pk)
                else:
                    mod = ContentType.objects.filter(model__icontains=obj[2], app_label=self._app_label_relations).get(
                        model__icontains=self.kind).model_class()()
                    setattr(mod, 'related_' + self.kind.lower() + '_id', self.objct.pk)
                    setattr(mod, 'related_' + obj[2].lower() + '_id', ent1.pk)
                voc = mod._meta.get_field('relation_type').related_model
                voc1, created = voc.objects.get_or_create(name=obj[0])
                setattr(mod, 'relation_type_id', voc1.pk)
                print(voc1)
                print(ent1)
                print(mod)
                mod.save()
                rel_obj_new.append(mod)
        self.related_objcts = rel_obj_new
        return self.objct

    @staticmethod
    def _sparql_to_pandas(sparql):
        """
        Converts a RDFlib SPARQL query to Pandas DataFrame
        :param sparql: (object) RDFlib query object
        :return: (DataFrame) Pandas DataFrame of return values
        """
        sp2 = sparql._get_bindings()
        for idx, s2 in enumerate(sp2):
            sp2[idx] = {str(key): str(value) for (key, value) in s2.items()}
        return sp2

    def _prep_string(self, string, regex, linked=False):
        """
        Function that converts SPARQL return value to string used in Django attributes
        :param string: (str) Format string with values ingested from SPARQL query (via Pandas DF)
        :param regex: (tuple) tuple of regex and group to use (regex, group)
        :return: (str) converted string
        """
        if string is None:
            return None
        if not isinstance(string, str):
            raise ValueError(f"{string} is not a string")
        if regex:
            m = re.search(regex[0], string)
            if m:
                string = m.group(regex[1])
            else:
                return None
        if linked:
            g1 = rdflib.Graph()
            g1.parse(string)
            pref1 = (SKOS.prefLabel, RDFS.label)
            pref1 += tuple([URIRef(x) for x in self._settings['matching']['prefLabels']])
            string = g1.preferredLabel(URIRef(string), labelProperties=pref1)
            if len(string) > 0:
                string = str(string[0][1])
        if len(string) > 255:
            string = string[:250] + '...'
        return string

    @staticmethod
    def _normalize_uri(uri):
        """
        Normalizes URIs to canonical form
        :param uri: (url) URI to normalize
        :return: (url) converted URI
        """
        base_dir = getattr(settings, 'BASE_DIR')
        sett_file = os.path.join(base_dir, getattr(settings, 'APIS_GENERICRDF_NORMALIZATION', 'apis_core/default_settings/URI_replace_settings.yml'))
        sett = yaml.load(open(sett_file, 'r'))
        for dom in sett['mappings']:
            if dom['domain'] in uri:
                m = re.match(dom['regex'], uri)
                if m:
                    uri = dom['replace'].format(m.group(1))
                    print(uri)
        return uri


    def create_objct(self, depth=2):
        """
        Uses parsed attributes to create an object that is not yet persisted to the db.
        Stores the object in self.objct
        :param depth: (int) depth to follow
        """
        c_dict = dict()
        for s in self._settings['matching']['attributes'].keys():
            if 'domain' in self._settings['matching']['attributes'][s].keys():
                if self._settings['matching']['attributes'][s]['domain'] not in self.uri:
                    print(f"continue: {s} / {self.uri} / {self._settings['matching']['attributes'][s]['domain']}")
                    continue
            access = self._settings['matching']['attributes'][s].get('accessor', None)
            field_name = self._settings['matching']['attributes'][s].get('field name', s)
            fields_1 = self.objct._meta.get_field(field_name)
            local_regex = self._settings['matching']['attributes'][s].get('regex', None)
            local_linked = self._settings['matching']['attributes'][s].get('linked', None)
            id_1 = self._settings['matching']['attributes'][s].get('identifier', s)
            if isinstance(fields_1, TCharField) or isinstance(fields_1, TFloatField):
                data = dict()
                if id_1 in self._attributes.keys():
                    df = self._attributes[id_1]
                    cols = [x for x in df.columns if x != 'lang']
                    for c in cols:
                        data[c] = df.at[0, c]
                    local_string = fmt.format(self._settings['matching']['attributes'][s]['string'], **data)
                    c_dict[field_name] = self._prep_string(local_string, local_regex, local_linked)
            elif isinstance(fields_1, TForeignKey):
                data = dict()
                c_dict_f = dict()
                if id_1 in self._attributes.keys():
                    df = self._attributes[id_1]
                    cols = [x for x in df.columns if x != 'lang']
                    for c in cols:
                        data[c] = df.at[0, c]
                    local_string = self._settings['matching']['attributes'][s]['string'].format(**data)
                    c_dict_f[access] = self._prep_string(local_string, local_regex, local_linked)
                self._foreign_keys.append((field_name, self.objct._meta.get_field(s).related_model, c_dict_f))
            elif isinstance(fields_1, TManyToMany):
                df = self._attributes[id_1]
                for idx, row in df.iterrows():
                    data = dict()
                    if id_1 in self._attributes.keys():
                        cols = [x for x in df.columns if x != 'lang']
                        for c in cols:
                            data[c] = row[c]
                        c_dict_f = dict()
                        local_string = self._settings['matching']['attributes'][s]['string'].format(**data)
                        c_dict_f[access] = self._prep_string(local_string, local_regex, local_linked)
                    self._m2m.append((field_name, self.objct._meta.get_field(s).related_model, c_dict_f))
        if 'labels' in self._settings['matching'].keys():
            for lab in self._settings['matching']['labels']:
                at1 = lab['identifier'].split('.')
                if at1[0] in self._attributes.keys():
                    u2 = self._attributes[at1[0]][[at1[-1], 'lang']]
                    for idx, row in u2.iterrows():
                        self.labels.append((row[at1[-1]], row['lang'], lab['label type']))
                    print(self.labels)

        if depth > 0 and 'linked objects' in self._settings['matching'].keys():
            for v in self._settings['matching']['linked objects']:
                at1 = v['identifier'].split('.')
                if at1[0] in self._attributes.keys():
                    u2 = self._attributes[at1[0]][at1[-1]].tolist()
                    self.related_objcts.append((v['kind'], u2, v['type']))
        self.objct = self.objct(**c_dict)

    def __init__(self, uri, kind, app_label_entities="apis_entities", app_label_relations="apis_relations",
                 app_label_vocabularies="apis_vocabularies", **kwargs):
        """
        :param uri: (url) Uri to parse the object from (http://test.at). The uri must start with a base url mentioned in the RDF parser settings file.
        :param kind: (string) Kind of entity (Person, Place, Institution, Work, Event)
        :param app_label_entities: (string) Name of the Django app that contains the entities that we create.
        :param app_label_relations: (string) Name of the Django app that contains the relations for the merging process.
        :param app_label_vocabularies: (string) Name of the Django app that contains the vocabularies defining the entities and relations.
        """

        def exist(uri, create_uri=False):
            if self.objct.objects.filter(uri__uri=uri).count() > 0:
                return True, self.objct.objects.get(uri__uri=uri)
            elif create_uri:
                self._objct_uri = Uri.objects.create(uri=uri)
                return False, False
            else:
                return False, False

        self.objct = ContentType.objects.get(app_label=app_label_entities, model=kind).model_class()
        self._app_label_relations = app_label_relations
        self.kind = kind
        self._foreign_keys = []
        self._m2m = []
        self.uri = self._normalize_uri(uri)
        self._objct_uri = Uri(uri=self.uri)
        self._subject = URIRef(self.uri)
        self.related_objcts = []
        owl = "http://www.w3.org/2002/07/owl#"
        force = kwargs.get('force', None)
        self.labels = []
        self.related_objcts = []

        self.saved = False
        test = exist(self.uri, create_uri=True)
        if test[0] and not force:
            self.objct = test[1]
            self.created = False
        else:
            self.created = True
            o = self._parse()
            print('worked')

