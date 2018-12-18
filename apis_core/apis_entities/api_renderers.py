from rest_framework import renderers
from apis_core.apis_tei.tei import TeiEntCreator
from rdflib import Namespace, Graph, URIRef, RDF, BNode, Literal, RDFS, XSD


class EntityToTEI(renderers.BaseRenderer):

    media_type = "text/xml"
    format = 'tei'

    def render(self, data, media_type=None, renderer_context=None):
        tei_doc = TeiEntCreator(data)
        return tei_doc.serialize_full_doc()


class EntityToCIDOC(renderers.BaseRenderer):

    media_type = "text/rdf+xml"
    format = 'rdf+xml'
    
    def render(self, data, media_type=None, renderer_context=None):
        cidoc = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
        geo = Namespace('http://www.w3.org/2003/01/geo/wgs84_pos#')
        g = Graph()
        k_uri = URIRef('http://127.0.0.1:8000/apis/api2/entity/{}'.format(data['id']))
        g.add( (k_uri, RDF.type, cidoc.P21) )
        b_app = BNode()
        g.add( (k_uri, cidoc.P131, b_app) )
        g.add( (b_app, RDF.type, cidoc.E82) )
        g.add( (b_app, RDFS.label, Literal('{} {}'.format(data['first_name'], data['name']),  lang='de')) )
        b_birth = BNode()
        g.add( (b_birth, RDF.type, cidoc.E67) )
        g.add( (b_birth, cidoc.P98, k_uri) )
        place_of_birth = URIRef('http://127.0.0.1:8000/apis/api2/entity/{}'.format(data['relations']['places'][0]['id']))
        g.add( (b_birth, cidoc.P7, place_of_birth) )
        g.add( (place_of_birth, RDF.type, cidoc.E53) )
        g.add( (place_of_birth, RDFS.label, Literal(data['relations']['places'][0]['place']['name'], lang='de'))) 
        
        b_place_of_birth_app2 = BNode()
        g.add( (place_of_birth, cidoc.P87, b_place_of_birth_app2) )
        g.add(( b_place_of_birth_app2, RDF.type, cidoc.E47 ))
        g.add( (b_place_of_birth_app2, geo.lat, Literal(data['relations']['places'][0]['place']['lat'])) )
        g.add( (b_place_of_birth_app2, geo.long, Literal(data['relations']['places'][0]['place']['lng'])) )

        b_date_of_birth = BNode()
        g.add( (b_date_of_birth, RDF.type, cidoc.E50) )
        g.add( (b_date_of_birth, cidoc.P114, Literal(data['start_date'], datatype=XSD.date)) )

        return g.serialize(format='xml')
