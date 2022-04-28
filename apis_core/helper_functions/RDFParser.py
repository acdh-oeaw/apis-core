import os
import os
import re
import string
import time
import unicodedata

import pandas as pd
import rdflib
import yaml
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldError, MultipleObjectsReturned
from django.db.models.fields import CharField as TCharField
from django.db.models.fields import FloatField as TFloatField
from django.db.models.fields.related import ForeignKey as TForeignKey
from django.db.models.fields.related import ManyToManyField as TManyToMany
from rdflib import URIRef, RDFS
from rdflib.namespace import SKOS, OWL

from apis_core.apis_labels.models import Label
from apis_core.apis_metainfo.models import Uri as genUri, Collection, Uri
from apis_core.apis_vocabularies.models import LabelType
from apis_core.default_settings.RDF_settings_new import sameAs

APIS_RDF_YAML_SETTINGS = getattr(
        settings,
        'APIS_RDF_YAML_SETTINGS',
        os.path.join(os.path.dirname(__file__), '../default_settings', 'RDF_default_settings.yml')
    )

APIS_RDF_URI_SETTINGS = getattr(
        settings,
        'APIS_RDF_URI_SETTINGS',
        os.path.join(os.path.dirname(__file__), '../default_settings', "URI_replace_settings.yml")
    )


def clean_uri(sett, uri):
    for dom in sett['mappings']:
        if dom['domain'] in uri:
            m = re.match(dom['regex'], uri)
            if m:
                uri = dom['replace'].format(m.group(1))
    return uri


class PartialFormatter(string.Formatter):

    def __init__(self, missing='-', bad_fmt='!!'):
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


class RDFParser(object):

    _reserved_uris = dict()

    @property
    def _settings_complete(self):
        sett = yaml.load(open(self._rdf_settings_file, 'r'))
        return sett

    @property
    def _settings(self):
        """
        Reads settings file and saves it
        :return: (dict) dict of settings file
        """
        sett = yaml.load(open(self._rdf_settings_file, 'r'))
        res = {'data': []}
        for v in sett[self.kind]['data']:
            if v['base_url'] in self.uri:
                res['data'] = v
        res['matching'] = sett[self.kind]['matching']
        res['sameAs'] = sameAs
        return res

    @staticmethod
    def _clean_uri_store():
        del_items = []
        for key, value in RDFParser._reserved_uris.items():
            if (time.time() - value) > (30 * 60):
                del_items.append(key)
        for d in del_items:
            del RDFParser._reserved_uris[d]

    def _exist(self, uri, uri_check=True):

        if self.objct.objects.filter(uri__uri=uri).count() > 0:
            return True, self.objct.objects.get(uri__uri=uri)
        else:
            if uri in RDFParser._reserved_uris.keys() and uri_check:
                if (time.time() - RDFParser._reserved_uris[uri]) < (self._preserve_uri_minutes * 60):
                    raise ValueError("URI used by other instance")
                else:
                    RDFParser._reserved_uris[uri] = time.time()
                    return False, False
            elif uri_check:
                RDFParser._reserved_uris[uri] = time.time()
                return False, False
            else:
                return False, False

    def _parse(self):
        """
        Parses the URI with the definition in the settings file
        :return: (dict) dict of Pandas DataFrames containing the variables obtained from SPARQL query
        """
        g = rdflib.Graph()
        g.parse(f"{self.uri}")
        if self._use_preferred:
            lst_pref = []
            pref_fin = []
            u = None
            count = 0
            u = self._settings_complete[self.kind]['data'][count]['base_url']
            while u:
                if u not in self.uri:
                    lst_pref.append(u)
                    count += 1
                    u = self._settings_complete[self.kind]['data'][count]['base_url']
                else:
                    u = False
            for o in g.objects(URIRef(self.uri), OWL.sameAs):
                for idx1, o2 in enumerate(lst_pref):
                    if o2 in str(o):
                        pref_fin.append((idx1, o))
            if len(pref_fin) > 0:
                pref_fin.sort(key=lambda tup: tup[0])
                self._parse = g.parse(pref_fin[0][1])
                self.uri = pref_fin[0][1]
        self._graph = g
        res = dict()
        for s in self._settings['data']['attributes']:
            sp = s.get('sparql', False)
            if sp:
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
            try:
                attr2, created = obj[1].objects.get_or_create(**obj[2])
                setattr(self.objct, obj[0], attr2)
            except MultipleObjectsReturned:
                pass
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
            try:
                attr2, created = obj[1].objects.get_or_create(**obj[2])
                getattr(self.objct, obj[0]).add(attr2)
            except MultipleObjectsReturned:
                pass
        for obj in self.related_objcts:
            for u3 in obj[1]:
                ent1 = RDFParser(u3, obj[2], uri_check=self._uri_check, preserve_uri_minutes=self._preserve_uri_minutes).get_or_create(depth=0)
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

    def _prep_string(self, string, regex, linked=False, data_type=False):
        """
        Function that converts SPARQL return value to string used in Django attributes
        :param string: (str) Format string with values ingested from SPARQL query (via Pandas DF)
        :param regex: (tuple) tuple of regex and group to use (regex, group)
        :return: (str) converted string
        """
        conv_mapping = {
            'str': str,
            'string': str,
            'float': float,
            'int': int,
            'integer': int
        }
        if string is None:
            return None
        if isinstance(string, str):
            if regex:
                m = re.search(regex[0], string)
                if m:
                    string = m.group(regex[1])
                else:
                    return None
            if len(string) > 255:
                string = string[:250] + '...'
            if linked:
                g1 = rdflib.Graph()
                g1.parse(string)
                pref1 = (SKOS.prefLabel, RDFS.label)
                pref1 += tuple([URIRef(x) for x in self._settings['matching']['prefLabels']])
                string = g1.preferredLabel(URIRef(string), labelProperties=pref1)
                if len(string) > 0:
                    string = str(string[0][1])
            string = unicodedata.normalize("NFC", string)
        if data_type:
            try:
                string = conv_mapping[data_type](string)
            except ValueError:
                string = None
        return string

    def _normalize_uri(self, uri):
        """
        Normalizes URIs to canonical form
        :param uri: (url) URI to normalize
        :return: (url) converted URI
        """
        sett = yaml.load(open(self._uri_settings_file, 'r'))
        return clean_uri(sett, uri)

    def merge(self, m_obj, app_label_relations='apis_relations'):
        """
        :param m_obj: the object to merge into (must be an django model object instance)
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
                ann.entity_link = self.objct
                ann.save()
        for txt in m_obj.text.all():
            self.objct.text.add(txt)
        if m_obj.source:
            self.objct.source = m_obj.source
            self.objct.save()
        m_obj.delete()
        return self.objct


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
            local_data_type = self._settings['matching']['attributes'][s].get('data type', False)
            id_1 = self._settings['matching']['attributes'][s].get('identifier', s).split('.')[0]
            if isinstance(fields_1, TCharField) or isinstance(fields_1, TFloatField):
                data = dict()
                if id_1 in self._attributes.keys():
                    df = self._attributes[id_1]
                    cols = [x for x in df.columns if x != 'lang']
                    for c in cols:
                        data[c] = df.at[0, c]
                    print(f"data: {data}")
                    if 'string' in self._settings['matching']['attributes'][s].keys():
                        local_string = fmt.format(self._settings['matching']['attributes'][s]['string'], **data)
                    else:
                        local_string = fmt.format("{"+self._settings['matching']['attributes'][s]['identifier'].split('.')[-1]+"}", **data)
                    c_dict[field_name] = self._prep_string(local_string, local_regex, local_linked, local_data_type)
            elif isinstance(fields_1, TForeignKey):
                data = dict()
                c_dict_f = dict()
                if id_1 in self._attributes.keys():
                    df = self._attributes[id_1]
                    cols = [x for x in df.columns if x != 'lang']
                    for c in cols:
                        data[c] = df.at[0, c]
                    local_string = fmt.format(self._settings['matching']['attributes'][s]['string'], **data)
                    c_dict_f[access] = self._prep_string(local_string, local_regex, local_linked, local_data_type)
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
                        local_string = fmt.format(self._settings['matching']['attributes'][s]['string'], **data)
                        c_dict_f[access] = self._prep_string(local_string, local_regex, local_linked, local_data_type)
                    self._m2m.append((field_name, self.objct._meta.get_field(s).related_model, c_dict_f))
        if 'labels' in self._settings['matching'].keys():
            for lab in self._settings['matching']['labels']:
                at1 = lab['identifier'].split('.')
                if at1[0] in self._attributes.keys():
                    if at1[-1] not in self._attributes[at1[0]].columns:
                        print('label_missing')
                        continue
                    if 'lang' not in self._attributes[at1[0]]:
                        self._attributes[at1[0]]['lang'] = 'deu'
                    u2 = self._attributes[at1[0]][[at1[-1], 'lang']]
                    for idx, row in u2.iterrows():
                        self.labels.append((row[at1[-1]], row['lang'], lab['label type']))

        if depth > 0 and 'linked objects' in self._settings['matching'].keys():
            for v in self._settings['matching']['linked objects']:
                at1 = v['identifier'].split('.')
                if at1[0] in self._attributes.keys():
                    if at1[-1] in self._attributes[at1[0]].columns:
                        u2 = self._attributes[at1[0]][at1[-1]].tolist()
                        self.related_objcts.append((v['kind'], u2, v['type']))
        self.objct = self.objct(**c_dict)

    def __init__(self, uri, kind, app_label_entities="apis_entities", app_label_relations="apis_relations",
                 app_label_vocabularies="apis_vocabularies", rdf_settings=APIS_RDF_YAML_SETTINGS,
                 uri_settings=APIS_RDF_URI_SETTINGS, preserve_uri_minutes=5, use_preferred=False, uri_check=True, **kwargs):
        """
        :param uri: (url) Uri to parse the object from (http://test.at). The uri must start with a base url mentioned in the RDF parser settings file.
        :param kind: (string) Kind of entity (Person, Place, Institution, Work, Event)
        :param app_label_entities: (string) Name of the Django app that contains the entities that we create.
        :param app_label_relations: (string) Name of the Django app that contains the relations for the merging process.
        :param app_label_vocabularies: (string) Name of the Django app that contains the vocabularies defining the entities and relations.
        :param use_preferred: (boolean) if True forwards to preferred sources defined in sameAs
        """

        self._clean_uri_store()
        self._rdf_settings_file = rdf_settings
        self._uri_settings_file = uri_settings
        self._preserve_uri_minutes = preserve_uri_minutes
        self._uri_check = uri_check
        self._use_preferred = use_preferred
        self.objct = ContentType.objects.get(app_label=app_label_entities, model__iexact=kind).model_class()
        self._app_label_relations = app_label_relations
        self.kind = kind
        self._foreign_keys = []
        self._m2m = []
        self.uri = self._normalize_uri(uri)
        self._objct_uri = Uri(uri=self.uri)
        self._subject = URIRef(self.uri)
        self.related_objcts = []
        force = kwargs.get('force', None)
        self.labels = []
        self.related_objcts = []

        self.saved = False
        test = self._exist(self.uri, uri_check=uri_check)
        if test[0] and not force:
            self.objct = test[1]
            self.created = False
            print('not created')
        else:
            self.created = True
            o = self._parse()
