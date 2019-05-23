from rdflib import RDF, RDFS, XSD, BNode, Graph, Literal, URIRef, OWL 
from django.conf import settings

base_uri = getattr(settings, 'APIS_BASE_URI', 'http://apis.info')
if base_uri.endswith('/'):
    base_uri = base_uri[:-1]
lang = getattr(settings, 'LANGUAGE_CODE', 'de')


def m_add_uris(g, ns, obj, uris):
    for u in uris:
        b_uri = URIRef(u['uri'])
        g.add((obj, OWL.sameAs, b_uri))
    return g


def m_place(g, ns, data):
    place_uri = URIRef("{}/apis/api2/entity/{}".format(base_uri, data["id"]))
    if (place_uri, RDF.type, ns['cidoc'].E53_Place) in g:
        return g, place_uri
    else:
        g.add((place_uri, RDF.type, ns['cidoc'].E53_Place))
        b_place_app1 = URIRef(f"{base_uri}/appellation/place/{data['id']}")
        g.add((place_uri, ns['cidoc'].P1_is_identified_by, b_place_app1))
        g.add((b_place_app1, RDF.type, ns['cidoc'].E41_Appellation))
        g.add(
            (
                b_place_app1,
                RDFS.label,
                Literal(data["name"], lang=lang),
            )
        )
        g.add((place_uri, RDFS.label, Literal(data["name"], lang=lang)))
        g.add((place_uri, ns['cidoc'].P168_place_is_defined_by, Literal(f"Point( {data['lng']} {data['lat']} )", datatype="geo:wktLiteral")))
        g = m_add_uris(g, ns, place_uri, data['uris'])        
        return g, place_uri


def m_place_of_birth(g, p, ns, data):
    if (None, ns['cidoc'].P98_brought_into_life, p) in g:
        b_birth = g.value(None, ns['cidoc'].P98_brought_into_life, p, any=False) 
    else:
        b_birth = URIRef(f"{base_uri}/appellation/birth/{data['id']}")
        g.add((b_birth, RDF.type, ns['cidoc'].E67_Birth))
        g.add((b_birth, ns['cidoc'].P98_brought_into_life, p))
    g, place_of_birth = m_place(g, ns, data["target"])
    g.add((b_birth, ns['cidoc'].P7_took_place_at, place_of_birth))

    return g
    

def m_place_of_death(g, p, ns, data):
    if (None, ns['cidoc'].P100_was_death_of, p) in g:
        b_death = g.value(None, ns['cidoc'].P100_was_death_of, p, any=False) 
    else:
        b_death = URIRef(f"{base_uri}/appellation/death/{data['id']}")
        g.add((b_death, RDF.type, ns['cidoc'].E69_Death))
        g.add((b_death, ns['cidoc'].P100_was_death_of, p))
    g, place_of_death = m_place(g, ns, data["target"])
    g.add((b_death, ns['cidoc'].P7_took_place_at, place_of_death))

    return g
