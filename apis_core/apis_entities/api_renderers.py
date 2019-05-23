import json

from apis_core.apis_tei.tei import TeiEntCreator
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from rdflib import RDF, RDFS, XSD, BNode, Graph, Literal, Namespace, URIRef, ConjunctiveGraph, OWL
from rdflib.plugins.memory import IOMemory
from rest_framework import renderers
from .cidoc_mapping import m_place_of_birth, m_place_of_death, m_add_uris
from webpage.metadata import PROJECT_METADATA


base_uri = getattr(settings, 'APIS_BASE_URI', 'http://apis.info')
if base_uri.endswith('/'):
    base_uri = base_uri[:-1]
lang = getattr(settings, 'LANGUAGE_CODE', 'de')


class EntityToTEI(renderers.BaseRenderer):

    media_type = "text/xml"
    format = "tei"

    def render(self, data, media_type=None, renderer_context=None):
        tei_doc = TeiEntCreator(data)
        return tei_doc.serialize_full_doc()


class EntityToCIDOC(renderers.BaseRenderer):

    media_type = "text/rdf"

    mps = {
        'places_place of birth': m_place_of_birth,
        'places_place of death': m_place_of_death
    }

    def render(self, data1, media_type=None, renderer_context=None):
        print(dir(self))
        if type(data1) != list:
            data1 = [data1]
            print('no list')
        cidoc = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
        geo = Namespace("http://www.opengis.net/ont/geosparql#")
        store = IOMemory()
        g1 = ConjunctiveGraph(store=store)
        g = Graph(store, identifier=URIRef('http://apis.acdh.oeaw.ac.at/entities#'))
        g1.bind('cidoc', cidoc, override=False)
        g1.bind('geo', geo, override=False)
        g1.bind('owl', OWL, override=False)
        apis = Namespace('https://apis.acdh.oeaw.ac.at')
        g1.bind('apis', apis, override=False)
        ns = {'cidoc': cidoc, 'geo': geo}
        for data in data1:
            k_uri = URIRef(data["url"])
            g.add((k_uri, RDF.type, cidoc.E21_Person))
            b_app = BNode()
            g.add((k_uri, cidoc.P1_is_identified_by, b_app))
            g.add((b_app, RDF.type, cidoc.E41_Appellation))
            g.add(
                (
                    b_app,
                    RDFS.label,
                    Literal("{} {}".format(data["first_name"], data["name"]), lang=lang),
                )
            )
            g.add((k_uri, RDFS.label, Literal(f"{data['first_name']} {data['name']}", lang=lang)))
            if data["start_date"] is not None:
                if len(data["start_date"]) > 0:
                    b_birth = URIRef(f"{base_uri}/appellation/birth/{data['id']}")
                    g.add((b_birth, RDF.type, cidoc.E67_Birth))
                    b_birth_time_span = BNode()
                    g.add((b_birth, cidoc["P4_has_time-span"], b_birth_time_span))
                    g.add((b_birth_time_span, RDF.type, cidoc["E52_Time-spans"]))
                    g.add((b_birth_time_span, cidoc.P82a_begin_of_the_begin, Literal(data["start_date"], datatype=XSD.date)))
                    g.add((b_birth_time_span, cidoc.P82b_end_of_the_end, Literal(data["start_date"], datatype=XSD.date)))
                    g.add((b_birth, cidoc.P98_brought_into_life, k_uri))
            if data["end_date"] is not None:
                if len(data["end_date"]) > 0:
                    b_death = URIRef(f"{base_uri}/appellation/death/{data['id']}")
                    g.add((b_death, RDF.type, cidoc.E69_Death))
                    b_death_time_span = BNode()
                    g.add((b_death, cidoc["P4_has_time-span"], b_death_time_span))
                    g.add((b_death_time_span, RDF.type, cidoc["E52_Time-spans"]))
                    g.add((b_death_time_span, cidoc.P82a_begin_of_the_begin, Literal(data["end_date"], datatype=XSD.date)))
                    g.add((b_death_time_span, cidoc.P82b_end_of_the_end, Literal(data["end_date"], datatype=XSD.date)))
                    g.add((b_death, cidoc.P100_was_death_of, k_uri))
            for ent_1 in data['relations']:
                for p in data['relations'][ent_1]:
                    if f"{ent_1}_{p['relation_type']['label']}" in self.mps.keys():
                        g = self.mps[f"{ent_1}_{p['relation_type']['label']}"](g, k_uri, ns, p) 
            g = m_add_uris(g, ns, k_uri, data['uris'])        
        return g1.serialize(format=self.format.split('+')[-1])


class EntityToCIDOCXML(EntityToCIDOC):

    format = "rdf+xml"


class EntityToCIDOCN3(EntityToCIDOC):

    format = "rdf+n3"


class EntityToCIDOCNQUADS(EntityToCIDOC):

    format = "rdf+nquads"


class EntityToCIDOCTURTLE(EntityToCIDOC):

    format = "rdf+turtle"


class EntityToProsopogrAPhI(renderers.BaseRenderer):

    media_type = "text/json+prosop"
    format = "json+prosop"

    def render(self, data, media_type=None, renderer_context=None):
        factoids = []
        fact_settings = getattr(settings, "PROSOPOGRAPHI_API", None)
        stmt_temp = "Stmt{}_{}"
        f = {"id": "apis_{}_{}".format(data["entity_type"].lower(), data["id"])}
        f[data["entity_type"].lower()] = {"id": str(data["id"])}
        f["source"] = {
            "id": PROJECT_METADATA["title"],
            "metadata": "{} export".format(PROJECT_METADATA["title"]),
        }
        f["createdBy"] = "{} export".format(PROJECT_METADATA["title"])
        f["createdWhen"] = timezone.now()
        stmt_count = 1
        stmts = []
        f[data["entity_type"].lower()]["uris"] = []
        for u in data["uris"]:
            f[data["entity_type"].lower()]["uris"].append(u["uri"])
        if data["entity_type"].lower() == "person":
            s = {
                "id": stmt_temp.format(data["id"], stmt_count),
                "name": "{}, {}".format(data["name"], data["first_name"]),
            }
            stmts.append(s)
            stmt_count += 1
        if "end_date" in data.keys():
            if data["end_date"] is not None and data["end_date"] != "":
                s = {
                    "id": stmt_temp.format(data["id"], stmt_count),
                    "date": {
                        "sortdate": data["end_date"],
                        "label": data["end_date_written"],
                    },
                    "role": {"label": "stirbt"},
                }
                stmts.append(s)
                stmt_count += 1
        if "start_date" in data.keys():
            if data["start_date"] is not None and data["start_date"] != "":
                s = {
                    "id": stmt_temp.format(data["id"], stmt_count),
                    "date": {
                        "sortdate": data["start_date"],
                        "label": data["start_date_written"],
                    },
                    "role": {"label": "geboren"},
                }
                stmts.append(s)
                stmt_count += 1
        if "gender" in data.keys():
            if data["gender"] is not None and data["gender"] != "":
                s = {
                    "id": stmt_temp.format(data["id"], stmt_count),
                    "statmentContent": [{"label": data["gender"]}],
                    "role": {"uri": "bio-crm:gender", "label": "gender"},
                }
                stmts.append(s)
                stmt_count += 1
        if "profession" in data.keys():
            if len(data["profession"]) > 0:
                s = {
                    "id": stmt_temp.format(data["id"], stmt_count),
                    "role": {"label": "profession"},
                    "statementContent": [],
                }
                for p in data["profession"]:
                    s2 = {
                        "uri": "apis_profession_type:{}".format(p["id"]),
                        "label": p["label"],
                    }
                    s["statementContent"].append(s2)
                stmts.append(s)
                stmt_count += 1
        f["statements"] = stmts
        factoids.append(f)
        facts = []
        facts_ind = {}
        if "relations" in data.keys():
            for ent in data["relations"].keys():
                for rel_1 in data["relations"][ent]:
                    s = {
                        "id": "Stmt{}_rel_{}".format(data["id"], rel_1["id"]),
                        "role": {
                            "label": rel_1["relation_type"]["label"],
                            "url": rel_1["relation_type"]["url"],
                        },
                    }
                    if "start_date" in rel_1.keys():
                        if rel_1["start_date"] != "":
                            s["date"] = {
                                "sortdate": rel_1["start_date"],
                                "label": rel_1["start_date_written"],
                            }
                            if rel_1["end_date_written"] != "":
                                s["date"]["label"] += "-{}".format(
                                    rel_1["end_date_written"]
                                )
                    ext_stc = False
                    t1 = {
                        "uri": "{}api2/entity/{}".format(base_uri, rel_1["target"]["id"]),
                        "label": rel_1["target"]["name"],
                    }
                    if fact_settings is not None:
                        if ent in fact_settings.keys():
                            if (
                                rel_1["relation_type"]["label"]
                                in fact_settings[ent].keys()
                            ):
                                s[
                                    fact_settings[ent][rel_1["relation_type"]["label"]]
                                ] = t1
                                ext_stc = True
                    if not ext_stc:
                        s["statementContent"] = [t1]
                    if len(rel_1["annotation"]) > 0:
                        stct = {
                            "id": "Annotation_{}".format(rel_1["annotation"][0]["id"]),
                            "label": rel_1["annotation"][0]["text"]
                        }
                        if "statementContent" in s.keys():
                            s["statementContent"].append(stct)
                        else:
                            s["statementContent"] = [stct,]
                    if len(rel_1["revisions"]) > 0:
                        user_1 = rel_1["revisions"][0]["user_created"]
                        date_1 = rel_1["revisions"][0]["date_created"].strftime("%Y-%m-%d")
                        rev_id = rel_1["revisions"][0]["id"]
                        if "{}_{}".format(user_1, date_1) not in facts_ind.keys():
                            facts_ind["{}_{}".format(user_1, date_1)] = len(factoids)
                            s3 = {
                                "person": factoids[0]["person"],
                                "id": "{}_{}".format(factoids[0]["id"], len(stmts)),
                                "source": {
                                    "id": "APIS",
                                    "metadata": "APIS highlighter annotations rev. {}".format(rev_id),
                                },
                                "createdBy": user_1,
                                "createdWhen": date_1,
                                "statements": [s]
                            }
                            factoids.append(s3)
                        else:
                            factoids[facts_ind["{}_{}".format(user_1, date_1)]]["statements"].append(s)
                            factoids[facts_ind["{}_{}".format(user_1, date_1)]]["source"]["metadata"] += " / {}".format(rev_id)
                    else:
                        factoids[0]["statements"].append(s)
        return json.dumps(
            {"factoids": factoids}, sort_keys=True, indent=1, cls=DjangoJSONEncoder
        )
