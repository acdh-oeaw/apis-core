gno = 'http://www.geonames.org/ontology#'
wgs84 = "http://www.w3.org/2003/01/geo/wgs84_pos#"
gndo = 'http://d-nb.info/standards/elementset/gnd#'
owl = "http://www.w3.org/2002/07/owl#"
geo = "http://www.opengis.net/ont/geosparql#"

sett_RDF_generic = {
    'Place': {
        'data': [
            {
                'base_url': 'http://sws.geonames.org/',
                'url_appendix': 'about.rdf',
                'kind': (
                    (gno + 'featureCode', None),
                    ),
                'attributes': [
                    {
                        'name': 'name',
                        'identifiers': (
                            (('objects', 'prefName', gno + 'officialName', ('language', 'de')),),
                            (('objects', 'prefName', gno + 'officialName', ('language', 'en')),),
                            (('objects', 'prefName', gno + 'name', None),),
                            (('objects', 'prefName', gno + 'alternateName', ('language', 'de')),),
                            (('objects', 'prefName', gno + 'alternateName', ('language', 'en')),)
                        )
                    },
                    {
                        'name': 'label',
                        'identifiers': (
                            (('objects', 'label', gno + 'alternateName', ('language', 'de')),),
                            (('objects', 'label', gno + 'alternateName', ('language', 'en')),)
                        )
                    },
                    {
                        'name': 'lat',
                        'identifiers': (
                            (('objects', 'lat', wgs84 + 'lat', None),),
                        )
                    },
                    {
                        'name': 'long',
                        'identifiers': (
                            (('objects', 'lng', wgs84 + 'long', None),),
                        )
                    },
                    {
                        'name': 'parentFeature',
                        'identifiers': (
                            (('objects', 'parentFeature', gno + 'parentFeature', None),),
                        )
                    },
                    {
                        'name': 'parentCountry',
                        'identifiers': (
                            (('objects', 'parentCountry', gno + 'parentCountry', None),),
                        )
                    },
                ]
            },
            {
                'base_url': 'http://d-nb.info/gnd/',
                'url_appendix': 'about/rdf',
                'attributes': [
                    {
                        'name': 'name',
                        'identifiers': (
                            (('objects', 'prefName', gndo + 'preferredNameForThePlaceOrGeographicName', None),),
                        )
                    },
                    {
                        'name': 'label',
                        'identifiers': (
                            (
                                ('objects', 'label', gndo + 'variantNameForThePlaceOrGeographicName', None),
                            ),
                        ),
                    },
                    {
                        'name': 'latlong',
                        'identifiers': (
                            (('objects', 'latlong_base', geo + 'hasGeometry', None), '>',
                             ('objects', 'latlong_geonode', geo + 'asWKT', None)
                             ),
                        )
                    },
                ]
            }
        ],
        'matching': {
            'attributes': {
                'name': (
                    (('prefName', None),),
                ),
                'lat': (
                    (('lat', None),),
                    (('latlong_geonode', ('Point \( [+-]([0-9\.]+) [+-]([0-9\.]+)', 2)),)
                ),
                'lng': (
                    (('lng', None),),
                    (('latlong_geonode', ('Point \( [+-]([0-9\.]+) [+-]([0-9\.]+)', 1)),)
                ),
            },
            'labels': {
                'alternative name': (
                    ('label', None),
                ),
                },
            'linked objects':
            [
            {
                'type': 'Place',
                'kind': 'located in',
                'object': (
                    ('parentFeature', None),
            )
            },
            {
                'type': 'Place',
                'kind': 'located in',
                'object': (
                    ('parentCountry', None),
            )
            },
            ],
        }
    },
    'Person': {
        'data': [
            {
                'base_url': 'http://d-nb.info/gnd/',
                'url_appendix': 'about/rdf',
                'attributes': [
                    {
                        'name': 'name',
                        'identifiers': (
                            (
                             ('objects', 'prefNameNode', gndo + 'preferredNameEntityForThePerson', None),'>',
                             ('objects', 'forename', gndo + 'forename', None), '=',
                             ('objects', 'surname', gndo + 'surname', None)
                        ),
                            (
                              ('objects', 'prefNameNode', gndo + 'preferredNameEntityForThePerson', None), '>',
                                ('objects', 'descriptionNode', gndo + 'Description', None), '>',
                                ('objects', 'personalNameAddition', gndo + 'nameAddition', None), '=',
                                ('objects', 'personalNameCounting', gndo + 'counting', None), '=',
                                ('objects', 'personalName', gndo + 'personalName', None),
                            ),

                        )
                    },
                    {
                        'name': 'label',
                        'identifiers': (
                            (

                                ('objects', 'label', gndo + 'variantNameForThePerson', None),

                            ),
                        ),
                    },
                    {
                        'name': 'place of birth',
                        'identifiers': (
                        (
                            ('objects', 'place of birth', gndo + 'placeOfBirth', None),
                        ),
                    ),
                    },
                    {
                        'name': 'place of death',
                        'identifiers': (
                        (
                            ('objects', 'place of death', gndo + 'placeOfDeath', None),
                        ),
                    ),
                    },
                    {
                        'name': 'date of birth',
                        'identifiers': (
                        (
                            ('objects', 'date of birth', gndo + 'dateOfBirth', None),
                        ),
                    ),
                    },
                    {
                        'name': 'date of death',
                        'identifiers': (
                        (
                            ('objects', 'date of death', gndo + 'dateOfDeath', None),
                        ),
                    ),
                    },
                ]
            },
            {
                'base_url': 'https://www.wikidata.org/wiki/Special:EntityData/',
                'url_appendix': '.rdf',
                'attributes': [
                    {
                        'name': 'name',
                        'identifiers': (
                            (
                                ('objects', '')
                            )
                        )
                    },
                ]
            }
        ],
        'matching': {
            'attributes': {
                'name': (
                    (('surname', None),
                    ),
                    (('personalNameAddition', None),
                    )
                ),
                'first_name': (
                    (('forename', None),),
                    (('personalName', None),
                    ' ',
                     ('personalNameCounting', None)
                    ),
                ),
                'start_date_written': (
                    (('date of birth', None),),
                ),
                'end_date_written': (
                    (('date of death', None),),
                ),
            },
            'labels': {
                'alternative name': (
                    ('label', None),
                ),
            },
            'linked objects':
            [
            {
                'type': 'Place',
                'kind': 'born in',
                'object': (
                    ('place of birth', None),
            )
            },
            {
                'type': 'Place',
                'kind': 'died in',
                'object': (
                    ('place of death', None),
            )
            },
            ]
        }
    },
    'Event': {
        'data': [
            {
                'base_url': 'http://d-nb.info/gnd/',
                'url_appendix': 'about/rdf',
                'attributes': [
                    {
                        'name': 'name',
                        'identifiers': (
                            (('objects', 'prefName', gndo + 'preferredNameForTheSubjectHeading', None),),
                        )
                    },
                    {
                        'name': 'start',
                        'identifiers': (
                            (('objects', 'start_date', gndo + 'dateOfEstablishment', None),),
                        )
                    },
                    {
                        'name': 'end',
                        'identifiers': (
                            (('objects', 'end_date', gndo + 'dateOfTermination', None),),
                        )
                    },
                    {
                        'name': 'label',
                        'identifiers': (
                            (('objects', 'label', gndo + 'variantNameForTheSubjectHeading', None),),
                        )
                    },
                    {
                        'name': 'place of event',
                        'identifiers': (
                            (('objects', 'place of event', gndo + 'place', None),),
                        )
                    }
                ],
            }
        ],
        'matching': {
            'attributes': {
                'name': (
                    (('prefName', None),),
                ),
                'start_date_written': (
                    (('start_date', None),),
                ),
                'end_date_written': (
                    (('end_date', None),),
                )
            },
            'labels': {
                'alternative name': (
                    ('label', None),
                )
            },
            'linked objects': [
            {
                'type': 'Place',
                'kind': 'place of event',
                'object': (
                    ('place of event', None),
            )
            },
            ],
        }
    },
    'Institution': {
        'data': [
            {
                'base_url': 'http://d-nb.info/gnd/',
                'url_appendix': 'about/rdf',
                'attributes': [
                    {
                        'name': 'name',
                        'identifiers': (
                            (('objects', 'prefName', gndo + 'preferredNameForTheCorporateBody', None),),
                            (('objects', 'prefName', gndo + 'variantNameForTheCorporateBody', None),),
                        )
                    },
                    {
                        'name': 'alternativeName',
                        'identifiers': (
                            (('objects', 'alternativeName', gndo + 'variantNameForTheCorporateBody', None),),
                        )
                    },
                    {
                        'name': 'start',
                        'identifiers': (
                            (('objects', 'start', gndo + 'dateOfEstablishment', None),),
                        )
                    },
                    {
                        'name': 'end',
                        'identifiers': (
                            (('objects', 'end', gndo + 'dateOfTermination', None),),
                        )
                    },
                    {
                        'name': 'placeOfBusiness',
                        'identifiers': (
                            (('objects', 'placeOfBusiness', gndo + 'placeOfBusiness', None),),
                        )
                    },
                    {
                        'name': 'succeeding',
                        'identifiers': (
                            (('objects', 'succeeding', gndo + 'succeedingCorporateBody', None),),
                        )
                    },
                    {
                        'name': 'preceding',
                        'identifiers': (
                            (('objects', 'preceding', gndo + 'precedingCorporateBody', None),),
                        )
                    }
                ]
            }
        ],
        'matching': {
            'attributes': {
                'name': (
                    (('prefName', None),),
                ),
                'start_date_written': (
                    (('start', None),),
                ),
                'end_date_written': (
                    (('end', None),),
                )
            },
            'labels': {
                'alternative name': (
                    ('alternativeName', None),
                )
            },
            'linked objects': [
            {
                'type': 'Place',
                'kind': 'located in',
                'object': (
                    ('placeOfBusiness', None),
            )
            },
            {
                'type': 'Institution',
                'kind': 'preceding',
                'object': (
                    ('preceding', None),
            )
            },
            {
                'type': 'Institution',
                'kind': 'succeeding',
                'object': (
                    ('succeeding', None),
            )
            },
            ]
        }
    }
}
