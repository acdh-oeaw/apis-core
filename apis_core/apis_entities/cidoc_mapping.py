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


cd_mp = {
        'places_place of birth': m_place_of_birth,
        'places_geboren in': m_place_of_birth,
        'places_place of death': m_place_of_death,
        'places_gestorben in': m_place_of_death
}


def m_place(g, ns, data, drill_down=False):
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
        if data['lng'] is not None:
            g.add((place_uri, ns['cidoc'].P168_place_is_defined_by, Literal(f"Point( {data['lng']} {data['lat']} )", datatype="geo:wktLiteral")))
        g = m_add_uris(g, ns, place_uri, data['uris'])        
        return g, place_uri


def m_person(g, ns, data, drill_down=False):
    k_uri = URIRef(data["url"])
    g.add((k_uri, RDF.type, ns['cidoc'].E21_Person))
    b_app = BNode()
    g.add((k_uri, ns['cidoc'].P1_is_identified_by, b_app))
    g.add((b_app, RDF.type, ns['cidoc'].E41_Appellation))
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
            g.add((b_birth, RDF.type, ns['cidoc'].E67_Birth))
            g.add((b_birth, RDFS.label, Literal(f"Geburt von {data['first_name']} {data['name']}", lang="de")))
            b_birth_time_span = BNode()
            g.add((b_birth, ns['cidoc']["P4_has_time-span"], b_birth_time_span))
            g.add((b_birth_time_span, RDF.type, ns['cidoc']["E52_Time-Span"]))
            g.add((b_birth_time_span, ns['cidoc'].P82a_begin_of_the_begin, Literal(data["start_date"], datatype=XSD.date)))
            g.add((b_birth_time_span, ns['cidoc'].P82b_end_of_the_end, Literal(data["start_date"], datatype=XSD.date)))
            g.add((b_birth_time_span, RDFS.label, Literal(f"{data['start_date']}")))
            g.add((b_birth, ns['cidoc'].P98_brought_into_life, k_uri))
    if data["end_date"] is not None:
        if len(data["end_date"]) > 0:
            b_death = URIRef(f"{base_uri}/appellation/death/{data['id']}")
            g.add((b_death, RDF.type, ns['cidoc'].E69_Death))
            g.add((b_death, RDFS.label, Literal(f"Tod von {data['first_name']} {data['name']}", lang="de")))
            b_death_time_span = BNode()
            g.add((b_death, ns['cidoc']["P4_has_time-span"], b_death_time_span))
            g.add((b_death_time_span, RDF.type, ns['cidoc']["E52_Time-Span"]))
            g.add((b_death_time_span, ns['cidoc'].P82a_begin_of_the_begin, Literal(data["end_date"], datatype=XSD.date)))
            g.add((b_death_time_span, ns['cidoc'].P82b_end_of_the_end, Literal(data["end_date"], datatype=XSD.date)))
            g.add((b_death_time_span, RDFS.label, Literal(f"{data['end_date']}")))
            g.add((b_death, ns['cidoc'].P100_was_death_of, k_uri))
    for ent_1 in data['relations']:
        for p in data['relations'][ent_1]:
            if f"{ent_1}_{p['relation_type']['label']}" in cd_mp.keys():
                g = cd_mp[f"{ent_1}_{p['relation_type']['label']}"](g, k_uri, ns, p) 
    g = m_add_uris(g, ns, k_uri, data['uris'])
    return g, k_uri


def m_institution(g, ns, data):
    inst_uri = URIRef(f"{base_uri}/apis/api2/entity/{data['id']}")
    if (inst_uri, RDF.type, ns['cidoc'].E74_Group) in g:
        return g, inst_uri
    else:
        g.add((inst_uri, RDF.type, ns['cidoc'].E74_Group))
        g.add((inst_uri, RDFS.label, Literal(data['name'], lang=lang)))


