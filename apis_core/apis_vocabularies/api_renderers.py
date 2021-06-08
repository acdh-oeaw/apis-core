from django.conf import settings
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import SKOS, RDF, DC, RDFS
from rest_framework import renderers

try:
    from webpage.metadata import PROJECT_METADATA
except ImportError:
    from webpage.utils import PROJECT_METADATA


base_uri_web = getattr(settings, 'APIS_BASE_URI', 'http://apis.info')
if base_uri_web.endswith('/'):
    base_uri_web = base_uri_web[:-1]
lang = getattr(settings, 'LANGUAGE_CODE', 'de')


class VocabToSkos(renderers.BaseRenderer):

    media_type = "text/rdf"

    def render(self, data1, media_type=None, g=None, renderer_context=None, format1=None, binary=True, store=None):
        if g is None:
            g = Graph()
        set_skos = getattr(settings, "APIS_SKOSMOS")
        base_uri = set_skos.get('url')
        if base_uri.endswith('/'):
            base_uri = base_uri[:-1]
        title = PROJECT_METADATA.get('title', 'TITLE')
        v_title = set_skos.get("vocabs-name", False)
        if not v_title:
            v_title = f"{title.lower()}thesaurus/"
        uri_1 = f"{base_uri}/{v_title}"
        uri = URIRef(f"{uri_1}/{title.title()}Schema")
        g.add((uri, RDFS.label, Literal(f"{title}Schema", lang=lang)))
        g.add((RDF.Description, RDF.about, uri))
        g.add((uri, RDF.type, SKOS.ConceptScheme))
        g.add((uri, DC.description, Literal(f"{set_skos.get('description', 'DESCRIPTION')}", lang=lang)))
        g.add((uri, DC.license, URIRef(set_skos.get("license", "https://opensource.org/licenses/MIT"))))
        g.add((uri, DC.relation, URIRef(base_uri_web)))
        
        cols = {}
        for d in data1:
            if not cols.get(d["vocab_name"], False):
                vc = URIRef(f"{uri_1}/{d['vocab_name']}")
                g.add((vc, RDF.type, SKOS.Collection))
                g.add((vc, SKOS.prefLabel, Literal(d['vocab_name'], lang=lang)))
                cols[d["vocab_name"]] = vc
            else:
                vc = cols.get(d["vocab_name"])
            conc = URIRef(f"{uri_1}/{d['id']}")
            g.add((vc, SKOS.member, conc))
            g.add((conc, RDF.type, SKOS.Concept))
            g.add((conc, SKOS.prefLabel, Literal(d['name'], lang=lang)))
            if d['name'] != d['label']:
                g.add((conc, SKOS.altLabel, Literal(d['label'], lang=lang)))
            rev = d.get('name_reverse', False)
            if rev:
                g.add((conc, SKOS.altLabel, Literal(f"reverse name: {rev}", lang=lang)))
                if d['name_reverse'] != d['label_reverse']:
                    g.add((conc, SKOS.altLabel, Literal(f"reverse label: {d['label_reverse']}", lang=lang)))
            if d.get('userAdded', False):
                if (uri, DC.creator, Literal(d['userAdded'], lang=lang)) not in g:
                    g.add((uri, DC.creator, Literal(d['userAdded'], lang=lang)))
            broader = d.get('parent_class', False)
            if broader:
                g.add((conc, SKOS.broader, URIRef(f"{uri_1}/{broader}")))
            else:
                g.add((conc, SKOS.topConceptOf, uri))
                g.add((uri, SKOS.hasTopConcept, conc))
        if format1:
            return g.serialize(format1)
        elif binary:
            return g, store
