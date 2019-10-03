import re

import pandas as pd
import rdflib
from django.contrib.contenttypes.models import ContentType

from apis_core.default_settings.RDF_settings_new import sett_RDF_generic
from apis_core.apis_metainfo.models import Uri as genUri, Collection, Uri
from django.db.models.fields import CharField as TCharField
from django.db.models.fields import FloatField as TFloatField
from django.db.models.fields.related import ForeignKey as TForeignKey
from django.db.models.fields.related import ManyToManyField as TManyToMany

from apis_core.helper_functions.RDFparsers import harmonize_geonames_id



class RDFParserNew(object):
    @property
    def _settings(self):
        res = {'data': []}
        for v in sett_RDF_generic[self.kind]['data']:
            if v['base_url'] in self.uri:
                res['data'] = v
        res['matching'] = sett_RDF_generic[self.kind]['matching']
        return res

    def _parse(self):
        g = rdflib.Graph()
        g.parse(f"{self.uri}")
        self._graph = g
        res = dict()
        for s in self._settings['data']['attributes']:
            sp = s.get('sparql', False)
            if sp:
                sp = sp.format(subject=self.uri)
                sp2 = self._sparql_to_pandas(g.query(sp))
                res[s.get('name', 'no identifier provided')] = pd.DataFrame(sp2)
        self._attributes = res
        return res

    def _add_same_as(self):
        

    def get_or_create(self):
        if not self.created:
            return self.objct
        else:
            if not self.saved:
                ob = self.save()
                return ob
            else:
                return self.objct

    def save(self):
        """
        :return: django object saved to db or False if nothing was saved
        """
        if not self.created:
            return False

        exist = genUri.objects.filter(uri=self.uri)
        if exist.count() > 0:
            if exist[0].entity is not None:
                return exist[0].entity
        self.objct.status = 'distinct'
        self.objct.save()
        def_coll, created = Collection.objects.get_or_create(name='Default import collection')
        self.objct.collection.add(def_coll)
        self.saved = True
        self._objct_uri.entity = self.objct
        self._objct_uri.save()
        for lab in self.labels:
            lab.temp_entity = self.objct
            lab.save()
        for obj in self.related_objcts:
            if hasattr(obj, 'related_' + self.kind.lower() + 'B'):
                setattr(obj, 'related_' + self.kind.lower() + 'A_id', self.objct.pk)
            else:
                setattr(obj, 'related_' + self.kind.lower() + '_id', self.objct.pk)
            obj.save()
        return self.objct

    @staticmethod
    def _sparql_to_pandas(sparql):
        sp2 = sparql._get_bindings()
        for idx, s2 in enumerate(sp2):
            sp2[idx] = {str(key): str(value) for (key, value) in s2.items()}
        return sp2

    @staticmethod
    def _prep_string(string, regex):
        if not isinstance(string, str):
            raise ValueError(f"{string} is not a string")
        if regex:
            string = re.match(regex[0], string).group(regex[1])
        if len(string) > 255:
            string = string[:250] + '...'
        return string

    def _create_related(self, depth=2):
        for s in self._settings['matching']['linked objects']:
            sp = s['sparql'].format(subject=self.uri)
            d1 = pd.DataFrame(self._graph.query(sp)._get_bindings())

    def create_objct(self, depth=2):
        c_dict = dict()
        for s in self._settings['matching']['attributes'].keys():
            fields_1 = self.objct._meta.get_field(s)
            if isinstance(fields_1, TCharField) or isinstance(fields_1, TFloatField):
                data = dict()
                id_1 = self._settings['matching']['attributes'][s].get('identifier', s)
                df = self._attributes[id_1]
                cols = [x for x in df.columns if x != 'lang']
                for c in cols:
                    data[c] = df.at[0, c]
                c_dict[s] = self._prep_string(self._settings['matching']['attributes'][s]['string'].format(**data),
                                              self._settings['matching']['attributes'][s].get('regex', None))
            elif isinstance(fields_1, TForeignKey):
                data = dict()
                c_dict_f = dict()
                s1 = self._settings['matching']['attributes'][s]
                for s2 in s1:
                    id_1 = s2.get('identifier', s)
                    df = self._attributes[id_1]
                    cols = [x for x in df.columns if x != 'lang']
                    for c in cols:
                        data[c] = df.at[0, c]
                    c_dict_f[s2['accessor']] = self._prep_string(s2['string'].format(**data), s2.get('regex', None))
                self._foreign_keys.append((s, self.objct._meta.get_field(s).related_model, c_dict_f))
            elif isinstance(fields_1, TManyToMany):
                for idx, row in df.iterrows(self):
                    data = dict()
                    id_1 = self._settings['matching']['attributes'][s].get('identifier', s)
                    df = self._attributes[id_1]
                    cols = [x for x in df.columns if x != 'lang']
                    for c in cols:
                        data[c] = row[c]
                    c_dict_f = dict()
                    s1 = self._settings['matching']['attributes'][s]
                    for s2 in s1:
                        c_dict_f[s2['accessor']] = self._prep_string(s2['string'].format(**data),
                    self._settings['matching']['attributes'][s].get('regex', None))
                    self._foreign_keys.append((s, self.objct._meta.get_field(s).related_model, c_dict_f))
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
        self.kind = kind
        self._foreign_keys = []
        self._m2m = []
        self.related_objcts = []
        owl = "http://www.w3.org/2002/07/owl#"
        force = kwargs.get('force', None)
        labels = []
        related_objcts = []
        uri = harmonize_geonames_id(uri)
        self.uri = uri

        self.saved = False
        test = exist(self.uri, create_uri=True)
        if test[0] and not force:
            self.objct = test[1]
            self.created = False
        else:
            self.created = True
            o = self._parse()
            print('worked')

