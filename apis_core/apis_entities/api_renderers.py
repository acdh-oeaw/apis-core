import json
import os
import pickle
from datetime import date

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from rdflib import XSD, Graph, Literal, Namespace, URIRef, ConjunctiveGraph, OWL
from rdflib.namespace import DCTERMS, VOID
from rdflib import plugin
from rdflib.store import Store
from rdflib.void import generateVoID
from rest_framework import renderers

from apis_core.apis_tei.tei import TeiEntCreator
from .api_mappings.cidoc_mapping import m_person, m_place, m_work, m_institution

try:
    from webpage.metadata import PROJECT_METADATA
except ImportError:
    try:
        from webpage.utils import PROJECT_METADATA
    except ImportError:
        PROJECT_METADATA = getattr(settings, "PROJECT_DEFAULT_MD")


base_uri = getattr(settings, "APIS_BASE_URI", "http://apis.info")
if base_uri.endswith("/"):
    base_uri = base_uri[:-1]
lang = getattr(settings, "LANGUAGE_CODE", "de")


class EntityToTEI(renderers.BaseRenderer):

    media_type = "text/xml"
    format = "tei"

    def render(self, data, media_type=None, renderer_context=None):
        tei_doc = TeiEntCreator(data)
        return tei_doc.serialize_full_doc()


class EntityToCIDOC(renderers.BaseRenderer):

    media_type = "text/rdf"

    ent_func = {
        "Person": m_person,
        "Place": m_place,
        "Work": m_work,
        "Institution": m_institution,
    }

    def render(
        self,
        data1,
        media_type=None,
        renderer_context=None,
        format_1=None,
        binary=False,
        store=False,
        named_graph=None,
        provenance=False,
    ):
        if isinstance(data1, dict):
            data1 = [data1]
        if format_1 is not None:
            self.format = format_1
        cidoc = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
        geo = Namespace("http://www.opengis.net/ont/geosparql#")
        frbroo = Namespace("http://iflastandards.info/ns/fr/frbr/frbroo#")
        if not store:
            store = plugin.get("Memory", Store)()
        if named_graph:
            uri_entities = URIRef(named_graph)
        else:
            uri_entities = URIRef(f"{base_uri}/entities#")
        g = Graph(store, identifier=uri_entities)
        g.bind("cidoc", cidoc, override=False)
        g.bind("geo", geo, override=False)
        g.bind("owl", OWL, override=False)
        g.bind("frbroo", frbroo, override=False)
        ns = {"cidoc": cidoc, "geo": geo, "frbroo": frbroo}
        if type(data1) == list:
            for data in data1:
                g, ent = self.ent_func[data["entity_type"]](
                    g, ns, data, drill_down=True
                )
        elif type(data1) == str:
            directory = os.fsencode(data1)
            for fn in os.listdir(directory):
                with open(os.path.join(directory, fn), "rb") as inf:
                    data2 = pickle.load(inf)
                    for data in data2:
                        g, ent = self.ent_func[data["entity_type"]](
                            g, ns, data, drill_down=True
                        )
        if provenance:
            g_prov = Graph(
                store, identifier=URIRef("https://omnipot.acdh.oeaw.ac.at/provenance")
            )
            g_prov.bind("dct", DCTERMS, override=False)
            g_prov.bind("void", VOID, override=False)
            g_prov.add(
                (
                    uri_entities,
                    DCTERMS.title,
                    Literal(PROJECT_METADATA["title"], lang=lang),
                )
            )
            g_prov.add(
                (
                    uri_entities,
                    DCTERMS.description,
                    Literal(PROJECT_METADATA["description"], lang=lang),
                )
            )
            g_prov.add(
                (
                    uri_entities,
                    DCTERMS.creator,
                    Literal(PROJECT_METADATA["author"], lang=lang),
                )
            )
            g_prov.add(
                (uri_entities, DCTERMS.publisher, Literal("ACDH-OeAW", lang=lang))
            )
            g_prov.add((uri_entities, DCTERMS.source, URIRef(base_uri)))
            g_prov.add(
                (
                    uri_entities,
                    DCTERMS.created,
                    Literal(str(date.today()), datatype=XSD.date),
                )
            )
            g_prov, g = generateVoID(g, dataset=uri_entities, res=g_prov)
        g_all = ConjunctiveGraph(store=store)
        if binary:
            return g_all, store
        return g_all.serialize(format=self.format.split("+")[-1])


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
        f = {"@id": "apis_{}_{}".format(data["entity_type"].lower(), data["id"])}
        f[data["entity_type"].lower()] = {"@id": str(data["id"])}
        f["source"] = {
            "@id": PROJECT_METADATA["title"],
            "label": "{} export".format(PROJECT_METADATA["title"]),
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
                "@id": stmt_temp.format(data["id"], stmt_count),
                "name": "{}, {}".format(data["name"], data["first_name"]),
            }
            stmts.append(s)
            stmt_count += 1
        if "end_date" in data.keys():
            if data["end_date"] is not None and data["end_date"] != "":
                s = {
                    "@id": stmt_temp.format(data["id"], stmt_count),
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
                    "@id": stmt_temp.format(data["id"], stmt_count),
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
                    "@id": stmt_temp.format(data["id"], stmt_count),
                    "statmentType": [{"label": data["gender"]}],
                    "role": {"uri": "bio-crm:gender", "label": "gender"},
                }
                stmts.append(s)
                stmt_count += 1
        if "profession" in data.keys():
            if len(data["profession"]) > 0:
                s = {
                    "@id": stmt_temp.format(data["id"], stmt_count),
                    "role": {"label": "profession"},
                    "statementType": [],
                }
                for p in data["profession"]:
                    s2 = {
                        "uri": "apis_profession_type:{}".format(p["id"]),
                        "label": p["label"],
                    }
                    s["statementType"].append(s2)
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
                        "@id": "Stmt{}_rel_{}".format(data["id"], rel_1["id"]),
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
                        "uri": "{}/api2/entity/{}".format(
                            base_uri, rel_1["target"]["id"]
                        ),
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
                        s["statementType"] = [t1]
                    try:
                        if len(rel_1["annotation"]) > 0:
                            s["statementContent"] = rel_1["annotation"][0]["text"]
                    except TypeError:
                        pass
                        # stct = {
                        #    "@id": "Annotation_{}".format(rel_1["annotation"][0]["id"]),
                        #    "label": rel_1["annotation"][0]["text"]
                        # }
                        # if "statementContent" in s.keys():
                        #    s["statementContent"].append(stct)
                        # else:
                        #    s["statementContent"] = [stct,]
                    if len(rel_1["revisions"]) > 0:
                        user_1 = rel_1["revisions"][0]["user_created"]
                        date_1 = rel_1["revisions"][0]["date_created"].strftime(
                            "%Y-%m-%d"
                        )
                        rev_id = rel_1["revisions"][0]["id"]
                        if "{}_{}".format(user_1, date_1) not in facts_ind.keys():
                            facts_ind["{}_{}".format(user_1, date_1)] = len(factoids)
                            s3 = {
                                "person": factoids[0]["person"],
                                "@id": "{}_{}".format(factoids[0]["@id"], len(stmts)),
                                "source": {
                                    "@id": "APIS",
                                    "label": "APIS highlighter annotations rev. {}".format(
                                        rev_id
                                    ),
                                },
                                "createdBy": user_1,
                                "createdWhen": date_1,
                                "statements": [s],
                            }
                            factoids.append(s3)
                        else:
                            factoids[facts_ind["{}_{}".format(user_1, date_1)]][
                                "statements"
                            ].append(s)
                            factoids[facts_ind["{}_{}".format(user_1, date_1)]][
                                "source"
                            ]["label"] += " / {}".format(rev_id)
                    else:
                        factoids[0]["statements"].append(s)
        return json.dumps(
            {"factoids": factoids}, sort_keys=True, indent=1, cls=DjangoJSONEncoder
        )
