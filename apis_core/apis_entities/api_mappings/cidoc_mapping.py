from django.conf import settings
from rdflib import RDF, RDFS, XSD, BNode, Literal, URIRef, OWL

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


def get_skos_url():
    set_skos = getattr(settings, "APIS_SKOSMOS")
    base_uri = set_skos.get("url")
    if base_uri.endswith("/"):
        base_uri = base_uri[:-1]
    title = PROJECT_METADATA.get("title", "TITLE")
    v_title = set_skos.get("vocabs-name", False)
    if not v_title:
        v_title = f"{title.lower()}thesaurus/"
    uri_1 = f"{base_uri}/{v_title}"
    return uri_1


def m_h_find_map_function(rel, ent_type):
    r1 = [
        (k.split("_")[0], k.split("_")[1], k, cd_mp[k])
        for k in cd_mp.keys()
        if k.startswith(ent_type)
    ]
    res = []
    for rr in r1:
        if "*" not in rr[1]:
            if f"{ent_type}_{rel}" == rr[2]:
                return rr[3]
        elif len(rr[1]) > 1:
            if rr[1].startswith("*") and rel.endswith(rr[1][1:]):
                res.append((1, rr[3]))
            elif rr[1].endswith("*") and rel.startswith(rr[1][:-1]):
                res.append((1, rr[3]))
        else:
            res.append((2, rr[3]))
    if len(res) > 0:
        res.sort(key=lambda tup: tup[0])
        return res[0][1]
    else:
        return None


def m_add_uris(g, ns, obj, uris):
    for u in uris:
        b_uri = URIRef(u["uri"])
        if obj != b_uri:
            g.add((obj, OWL.sameAs, b_uri))
            g.add((b_uri, RDF.type, ns["cidoc"].E42_Identifier))
    return g


def m_add_time_span(g, ns, event, date, date_written, id_ev):
    time_span = URIRef(f"{base_uri}/appellation/{event}/date/{id_ev}")
    g.set((time_span, RDF.type, ns["cidoc"]["E52_Time-Span"]))
    g.set(
        (
            time_span,
            ns["cidoc"].P82a_begin_of_the_begin,
            Literal(date, datatype=XSD.date),
        )
    )
    g.set(
        (time_span, ns["cidoc"].P82b_end_of_the_end, Literal(date, datatype=XSD.date))
    )
    g.set((time_span, RDFS.label, Literal(f"{date_written}")))
    return g, time_span


def m_place_of_birth(g, p, ns, data):
    if (None, ns["cidoc"].P98_brought_into_life, p) in g:
        b_birth = g.value(None, ns["cidoc"].P98_brought_into_life, p, any=False)
    else:
        b_birth = URIRef(f"{base_uri}/entity/{data['id']}/birth")
        """URI for person specific birth event"""
        g.set((b_birth, RDF.type, ns["cidoc"].E67_Birth))
        g.set((b_birth, ns["cidoc"].P98_brought_into_life, p))
    g, place_of_birth = m_place(g, ns, data["target"])
    g.set((b_birth, ns["cidoc"].P7_took_place_at, place_of_birth))

    return g


def m_place_of_death(g, p, ns, data):
    if (None, ns["cidoc"].P100_was_death_of, p) in g:
        b_death = g.value(None, ns["cidoc"].P100_was_death_of, p, any=False)
    else:
        b_death = URIRef(f"{base_uri}/entity/{data['id']}/death")
        """URI for person specific death event"""
        g.set((b_death, RDF.type, ns["cidoc"].E69_Death))
        g.set((b_death, ns["cidoc"].P100_was_death_of, p))
    g, place_of_death = m_place(g, ns, data["target"])
    g.set((b_death, ns["cidoc"].P7_took_place_at, place_of_death))

    return g


def m_institutions_rel(g, p, ns, data, drill_down=False):
    b_joining = URIRef(f"{base_uri}/events/joined/{data['id']}")
    g.add((b_joining, RDF.type, ns["cidoc"].E85_Joining))
    g.add((b_joining, ns["cidoc"].P143_joined, p))
    b_pc_joining = URIRef(f"{base_uri}/events/joined_pc/{data['id']}")
    g.add((b_pc_joining, RDF.type, ns["cidoc"].PC144_joined_with))
    g.add((b_pc_joining, ns["cidoc"].P01_has_domain, b_joining))
    inst_uri = URIRef(f"{base_uri}/entity/{data['target']['id']}")
    join_type = URIRef(f"{get_skos_url()}/{data['relation_type']['id']}")
    g.add((join_type, RDF.type, ns["cidoc"].E55_Type))
    g.add((join_type, RDFS.label, Literal(data["relation_type"]["label"])))
    g.add((b_pc_joining, ns["cidoc"]["P144.1_kind_of_member"], join_type))
    if (inst_uri, RDF.type, ns["cidoc"].E74_Group) not in g:
        g, inst_uri = m_institution(g, ns, data["target"])
    if data["start_date"] is not None:
        g, start_date_node = m_add_time_span(
            g, ns, "joined", data["start_date"], data["start_date_written"], data["id"]
        )
        g.set((b_joining, ns["cidoc"]["P4_has_time-span"], start_date_node))
    if data["end_date"] is not None:
        b_leaving = URIRef(f"{base_uri}/events/left/{data['id']}")
        g.add((b_leaving, RDF.type, ns["cidoc"].E86_Leaving))
        g.add((b_leaving, ns["cidoc"].P145_seperated, p))
        g.add((b_leaving, ns["cidoc"].P146_seperated_from, inst_uri))
        g, end_date_node = m_add_time_span(
            g, ns, "left", data["end_date"], data["end_date_written"], data["id"]
        )
        g.set((b_leaving, ns["cidoc"]["P4_has_time-span"], end_date_node))
    g.add((b_pc_joining, ns["cidoc"].P02_has_range, inst_uri))
    return g


cd_mp = {
    "places_place of birth": m_place_of_birth,
    "places_geboren in": m_place_of_birth,
    "places_place of death": m_place_of_death,
    "places_gestorben in": m_place_of_death,
    "institutions_*": m_institutions_rel,
}


def m_place(g, ns, data, drill_down=False):
    place_uri = URIRef("{}/entity/{}".format(base_uri, data["id"]))
    """URI for location"""
    if (place_uri, RDF.type, ns["cidoc"].E53_Place) in g and not drill_down:
        return g, place_uri
    else:
        g.set((place_uri, RDF.type, ns["cidoc"].E53_Place))
        b_place_app1 = URIRef(f"{base_uri}/appellation/place/{data['id']}")
        """URI for location appellation"""
        g.set((place_uri, ns["cidoc"].P1_is_identified_by, b_place_app1))
        g.set((b_place_app1, RDF.type, ns["cidoc"].E41_Appellation))
        g.set(
            (
                b_place_app1,
                RDFS.label,
                Literal(data["name"], lang=lang),
            )
        )
        g.set((place_uri, RDFS.label, Literal(data["name"], lang=lang)))
        if data["lng"] is not None:
            g.set(
                (
                    place_uri,
                    ns["cidoc"].P168_place_is_defined_by,
                    Literal(
                        f"Point( {data['lng']} {data['lat']} )",
                        datatype="geo:wktLiteral",
                    ),
                )
            )
        g = m_add_uris(g, ns, place_uri, data["uris"])
        if drill_down:
            for ent_1 in data["relations"]:
                for p in data["relations"][ent_1]:
                    rel_map = m_h_find_map_function(p["relation_type"]["label"], ent_1)
                    if rel_map is not None:
                        g = rel_map(g, place_uri, ns, p)
        return g, place_uri


def m_work(g, ns, data, drill_down=False):
    k_uri = URIRef(data["url"])
    if (k_uri, RDF.type, ns["cidoc"].E73_Information_Object) in g and not drill_down:
        return g, k_uri
    else:
        k_label_string = f"{data['name']}".strip()
        g.set((k_uri, RDF.type, ns["cidoc"].E73_Information_Object))
        g.set((k_uri, RDFS.label, Literal(k_label_string, lang=lang)))
        b_app = BNode()
        g.set((k_uri, ns["cidoc"].P1_is_identified_by, b_app))
        g.set((b_app, RDF.type, ns["cidoc"].E41_Appellation))
        g.set((b_app, RDFS.label, Literal(k_label_string, lang=lang)))
        g = m_add_uris(g, ns, k_uri, data["uris"])
        return g, k_uri


def m_person(g, ns, data, drill_down=False):
    k_uri = URIRef(data["url"])
    if (k_uri, RDF.type, ns["cidoc"].E21_Person) in g and not drill_down:
        return g, k_uri
    else:
        g.set((k_uri, RDF.type, ns["cidoc"].E21_Person))
        apisid_stmt = URIRef(f"{base_uri}/entity/{data['id']}/apisid")
        """URI for APIS ID"""
        oblid_stmt = URIRef(f"{base_uri}/entity/{data['id']}/oblid")
        """URI for OEBL ID"""
        pnappell_stmt = URIRef(
            f"{base_uri}/pnappellation#{data['id']}/{data['name'].replace(' ', '_')}"
        )
        """URI for preferred name"""
        lname_stmt = URIRef(
            f"{base_uri}/appellationsn#{data['id']}/{data['name'].replace(' ', '_')}"
        )
        """URI for surname"""
        fname_stmt = URIRef(
            f"{base_uri}/appellationfn#{data['id']}/{data['name'].replace(' ', '_')}"
        )
        """URI for last name"""
        gender_stmt = URIRef(f"{get_skos_url()}/gender/{data['gender']}")
        """replace URI with valid acdh.vocabs-URI and use namespace"""
        g.set((pnappell_stmt, ns["cidoc"].P2_has_type, ns["cidoc"].E55_Type))
        g.set((k_uri, ns["cidoc"].P1_is_identified_by, apisid_stmt))
        g.add((k_uri, ns["cidoc"].P1_is_identified_by, pnappell_stmt))
        g.set((apisid_stmt, RDF.type, ns["cidoc"].E42_Identifier))
        g.set(
            (
                apisid_stmt,
                RDFS.label,
                Literal(
                    "is identified by APIS Identifier as {}".format(data["id"]),
                    lang=lang,
                ),
            )
        )
        g.set(
            (
                apisid_stmt,
                RDF.value,
                Literal(data["id"]),
            )
        )
        g.add((k_uri, ns["cidoc"].P1_is_identified_by, oblid_stmt))
        g.set((oblid_stmt, RDF.type, ns["cidoc"].E42_Identifier))
        g.set(
            (
                oblid_stmt,
                RDFS.label,
                Literal("is identified by ÖBL Identifier as XXXX", lang=lang),
                # Literal("is identified by ÖBL Identifier as {}".format(data['orig_id']), lang=lang),
            )
        )
        g.set(
            (
                oblid_stmt,
                RDF.value,
                Literal("XXXX"),
                # Literal(data['orig_id']),
            )
        )
        g.set(
            (
                pnappell_stmt,
                ns["cidoc"]["P2_has_type"],
                URIRef(f"{get_skos_url()}/name/preferrred_name"),
            )
        )
        """replace URI with valid acdh.vocabs-URI and use namespace"""
        g.set(
            (
                pnappell_stmt,
                RDFS.label,
                Literal(
                    f"Preferred name is {data['first_name']} {data['name']}", lang=lang
                ),
            )
        )
        g.set((pnappell_stmt, ns["cidoc"]["P106_is_composed_of"], lname_stmt))
        g.add((pnappell_stmt, ns["cidoc"]["P106_is_composed_of"], fname_stmt))
        g.set(
            (
                lname_stmt,
                ns["cidoc"]["P2_has_type"],
                URIRef(f"{get_skos_url()}/name/surname"),
            )
        )
        """replace with valid acdh.vocabs-URI and use namespace"""
        g.set(
            (lname_stmt, RDFS.label, Literal(f"Surname is {data['name']}", lang=lang))
        )
        g.add((lname_stmt, RDF.value, Literal(data["name"])))
        g.add(
            (
                fname_stmt,
                ns["cidoc"]["P2_has_type"],
                URIRef(f"{get_skos_url()}/name/forename"),
            )
        )
        """replace with valid acdh.vocabs-URI and use namespace"""
        g.set(
            (
                fname_stmt,
                RDFS.label,
                Literal(f"Forename is {data['first_name']}", lang=lang),
            )
        )
        g.add((fname_stmt, RDF.value, Literal(data["first_name"])))
        g.set(
            (
                k_uri,
                RDFS.label,
                Literal(
                    f"Person known as {data['first_name']} {data['name']}", lang=lang
                ),
            )
        )
        # import alternative names: if data["alternate_name"] is not None:
        # g.setusw.
        if data["gender"] != "":
            """Statement for known gender"""
            g.set(((k_uri, ns["cidoc"]["P2_has_type"], gender_stmt)))
            g.add((gender_stmt, RDF.type, ns["cidoc"].E55_Type))
            g.add((gender_stmt, RDF.value, Literal(data["gender"])))
            g.add(
                (
                    gender_stmt,
                    RDFS.label,
                    Literal(
                        "Person was documented as {}".format(data["gender"]), lang=lang
                    ),
                )
            )
        if data["gender"] == "":
            """Statement for unknown gender"""
            g.add(
                (
                    (
                        k_uri,
                        ns["cidoc"]["P2_has_type"],
                        URIRef(f"{get_skos_url()}/gender/unknown"),
                    )
                )
            )
            g.add((gender_stmt, RDF.type, ns["cidoc"].E55_Type))
            g.add((gender_stmt, RDF.value, Literal("unknown")))
            g.add(
                (
                    gender_stmt,
                    RDFS.label,
                    Literal("No Gender was documented.", lang=lang),
                )
            )
        if data["start_date"] is not None:
            if len(data["start_date"]) > 0:
                b_birth = URIRef(f"{base_uri}/entity/{data['id']}/birth")
                """URI for person specific birth event"""
                g.set((b_birth, RDF.type, ns["cidoc"].E67_Birth))
                g.set(
                    (
                        b_birth,
                        RDFS.label,
                        Literal(
                            f"Birth of {data['first_name']} {data['name']}", lang="de"
                        ),
                    )
                )
                b_birth_time_span = URIRef(
                    f"{base_uri}/entity/timestamp/{data['start_date']}"
                )
                g.set((b_birth, ns["cidoc"]["P4_has_time-span"], b_birth_time_span))
                g.set((b_birth_time_span, RDF.type, ns["cidoc"]["E52_Time-Span"]))
                g.set(
                    (
                        b_birth_time_span,
                        ns["cidoc"].P82a_begin_of_the_begin,
                        Literal(data["start_date"], datatype=XSD.date),
                    )
                )
                g.set(
                    (
                        b_birth_time_span,
                        ns["cidoc"].P82b_end_of_the_end,
                        Literal(data["start_date"], datatype=XSD.date),
                    )
                )
                g.set((b_birth_time_span, RDF.value, Literal(f"{data['start_date']}")))
                g.set((b_birth, ns["cidoc"].P98_brought_into_life, k_uri))
        if data["end_date"] is not None:
            if len(data["end_date"]) > 0:
                b_death = URIRef(f"{base_uri}/entity/{data['id']}/death")
                g.set((b_death, RDF.type, ns["cidoc"].E69_Death))
                g.set(
                    (
                        b_death,
                        RDFS.label,
                        Literal(
                            f"Death of {data['first_name']} {data['name']}", lang="de"
                        ),
                    )
                )
                b_death_time_span = URIRef(
                    f"{base_uri}/entity/timestamp/{data['end_date']}"
                )
                g.set((b_death, ns["cidoc"]["P4_has_time-span"], b_death_time_span))
                g.set((b_death_time_span, RDF.type, ns["cidoc"]["E52_Time-Span"]))
                g.set(
                    (
                        b_death_time_span,
                        ns["cidoc"].P82a_begin_of_the_begin,
                        Literal(data["end_date"], datatype=XSD.date),
                    )
                )
                g.set(
                    (
                        b_death_time_span,
                        ns["cidoc"].P82b_end_of_the_end,
                        Literal(data["end_date"], datatype=XSD.date),
                    )
                )
                g.set((b_death_time_span, RDF.value, Literal(f"{data['end_date']}")))
                g.set((b_death, ns["cidoc"].P100_was_death_of, k_uri))
        if data["profession"] is not None:
            for prof in data["profession"]:
                prof_stmt = URIRef(
                    f"{get_skos_url()}/profession/{prof['name'].replace(' ', '_')}"
                )
                g.set((k_uri, ns["cidoc"].P14i_performed, prof_stmt))
                g.set((prof_stmt, RDF.type, ns["frbroo"].F51))
                pref_prof = prof["label"]
                g.set((prof_stmt, RDF.value, Literal(pref_prof)))
                """adress most specific value or profession e.g. Architekt, Schriftsteller, current datatype is List with Ordered Dict"""
        if drill_down:
            for ent_1 in data["relations"]:
                for p in data["relations"][ent_1]:
                    rel_map = m_h_find_map_function(p["relation_type"]["label"], ent_1)
                    if rel_map is not None:
                        g = rel_map(g, k_uri, ns, p)
    g = m_add_uris(g, ns, k_uri, data["uris"])
    return g, k_uri


def m_institution(g, ns, data, drill_down=False):
    inst_uri = URIRef(f"{base_uri}/entity/{data['id']}")
    if (inst_uri, RDF.type, ns["cidoc"].E74_Group) in g:
        return g, inst_uri
    else:
        g.set((inst_uri, RDF.type, ns["cidoc"].E74_Group))
        g.set((inst_uri, RDFS.label, Literal(data["name"], lang=lang)))
        if data["kind"] is not None:
            uri_type = URIRef(f"{get_skos_url()}/{data['kind']['id']}")
            g.set((uri_type, RDF.type, ns["cidoc"].E55_Type))
            g.set((inst_uri, ns["cidoc"].P2_has_type, uri_type))
            g.set((uri_type, RDFS.label, Literal(data["kind"]["label"])))
    return g, inst_uri
