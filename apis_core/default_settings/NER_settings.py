#!/usr/bin/python
# -*- coding: utf-8 -*-

gn = "http://www.geonames.org/ontology#"
stb_base = 'https://enrich.acdh.oeaw.ac.at/entityhub/site/'
URL_geonames = stb_base + "geoNames_%s/query"
wgs84_pos = "http://www.w3.org/2003/01/geo/wgs84_pos#"
gnd_geo = "http://www.opengis.net/ont/geosparql#"
stb_find = stb_base + u'{}/find'
GenderMappingGND = {'male': 'http://d-nb.info/standards/vocab/gnd/Gender#male',
                    'männlich': 'http://d-nb.info/standards/vocab/gnd/Gender#male',
                    'Mann': 'http://d-nb.info/standards/vocab/gnd/Gender#male',
                    'female': 'http://d-nb.info/standards/vocab/gnd/Gender#female',
                    'weiblich': 'http://d-nb.info/standards/vocab/gnd/Gender#female',
                    'Frau': 'http://d-nb.info/standards/vocab/gnd/Gender#female'}

def date_conversion(date):
    return "{}T00:00:00.000Z".format(date)

autocomp_settings = {
    'score': u'http://stanbol.apache.org/ontology/entityhub/query#score',
    'uri': 'id',
    'label': u'http://www.w3.org/2000/01/rdf-schema#label',
    'Place': [
        {'source': 'Geonames',
        'type': False,
        'url': stb_find.format('geoNames_S_P_A'),
        'fields': {
            'descr': (gn + 'featureCode', 'String'),
            'name': (gn + 'name','String'),
            'long': (wgs84_pos + 'long', 'String'),
            'lat': (wgs84_pos + 'lat', 'String')
        }},
        {'source': 'GeonamesRGN',
        'type': False,
        'url': stb_find.format('geoNames_RGN'),
        'fields': {
            'descr': (gn + 'featureCode','String'),
            'name': (gn + 'name','String'),
            'long': (wgs84_pos + 'long','String'),
            'lat': (wgs84_pos + 'lat','String')
        }},
        {'source': 'GeonamesVAL',
        'type': False,
        'url': stb_find.format('geoNames_VAL'),
        'fields': {
            'descr': (gn + 'featureCode','String'),
            'name': (gn + 'name','String'),
            'long': (wgs84_pos + 'long','String'),
            'lat': (wgs84_pos + 'lat','String')
        }},
        {'source': 'GND',
        'type': u'http://d-nb.info/standards/elementset/gnd#TerritorialCorporateBodyOrAdministrativeUnit',
        'url': stb_find.format('gndTerritorialCorporateBodyOrAdministrativeUnits'),
        'fields': {
            'name': (u'http://d-nb.info/standards/elementset/gnd#preferredNameForThePlaceOrGeographicName','String'),
            'descr': (u'http://d-nb.info/standards/elementset/gnd#definition','String'),
            'long': (gnd_geo + 'asWKT', 'gndLong'),
            'lat': (wgs84_pos + 'lat','String')
        }},
        ],
    'Institution': [{
        'source': 'GND',
        'type': u'http://d-nb.info/standards/elementset/gnd#CorporateBody',
        'url': stb_find.format('gndCorporateBodyAndOrganOfCorporateBody'),
        'fields': {
            'descr': (u'http://d-nb.info/standards/elementset/gnd#definition','String'),
            'name': (u'http://d-nb.info/standards/elementset/gnd#preferredNameForTheCorporateBody','String')}},
            {
        'source': 'GND',
        'type': u'http://d-nb.info/standards/elementset/gnd#OrganOfCorporateBody',
        'url': stb_find.format('gndCorporateBodyAndOrganOfCorporateBody'),
        'fields': {
            'descr': (u'http://d-nb.info/standards/elementset/gnd#definition','String'),
            'name': (u'http://d-nb.info/standards/elementset/gnd#preferredNameForTheCorporateBody','String')}}],
    'Person': [{
        'source': 'GND',
        'type': u'http://d-nb.info/standards/elementset/gnd#DifferentiatedPerson',
        'url': stb_find.format('gndPersons'),
        'search fields': {'gender': ('http://d-nb.info/standards/elementset/gnd#gender',
                                     GenderMappingGND, 'reference'),
                          'start_date': ('http://d-nb.info/standards/elementset/gnd#dateOfBirth',
                                         date_conversion, 'date_exact'),
                          'end_date': ('http://d-nb.info/standards/elementset/gnd#dateOfDeath',
                                         date_conversion, 'date_exact'),
                          'start_date__gt': ('http://d-nb.info/standards/elementset/gnd#dateOfBirth',
                                         date_conversion, 'date_gt'),
                          'start_date__lt': ('http://d-nb.info/standards/elementset/gnd#dateOfBirth',
                                         date_conversion, 'date_lt'),
                          'end_date__gt': ('http://d-nb.info/standards/elementset/gnd#dateOfBirth',
                                         date_conversion, 'date_gt'),
                          'end_date__lt': ('http://d-nb.info/standards/elementset/gnd#dateOfDeath',
                                         date_conversion, 'date_lt')},
        'fields': {
            'descr': (u'http://d-nb.info/standards/elementset/gnd#biographicalOrHistoricalInformation','String'),
            'name': (u'http://d-nb.info/standards/elementset/gnd#preferredNameForThePerson','String'),
            'dateOfBirth': (u'http://d-nb.info/standards/elementset/gnd#dateOfBirth', 'GNDDate'),
            'dateOfDeath': (u'http://d-nb.info/standards/elementset/gnd#dateOfDeath', 'GNDDate')}},
{
        'source': 'GND',
        'type': u'http://enrich.acdh.oeaw.ac.at/stanbol/entityhub/site/gndRoyalOrMemberOfARoyalHouse/',
        'url': stb_find.format('gndRoyalOrMemberOfARoyalHouse'),
        'search fields': {'gender': ('http://d-nb.info/standards/elementset/gnd#gender',
                                     GenderMappingGND, 'reference'),
                          'start_date': ('http://d-nb.info/standards/elementset/gnd#dateOfBirth',
                                         date_conversion, 'date_exact'),
                          'end_date': ('http://d-nb.info/standards/elementset/gnd#dateOfDeath',
                                         date_conversion, 'date_exact'),
                          'start_date__gt': ('http://d-nb.info/standards/elementset/gnd#dateOfBirth',
                                         date_conversion, 'date_gt'),
                          'start_date__lt': ('http://d-nb.info/standards/elementset/gnd#dateOfBirth',
                                         date_conversion, 'date_lt'),
                          'end_date__gt': ('http://d-nb.info/standards/elementset/gnd#dateOfBirth',
                                         date_conversion, 'date_gt'),
                          'end_date__lt': ('http://d-nb.info/standards/elementset/gnd#dateOfDeath',
                                         date_conversion, 'date_lt')},
        'fields': {
            'descr': (u'http://d-nb.info/standards/elementset/gnd#biographicalOrHistoricalInformation','String'),
            'name': (u'http://d-nb.info/standards/elementset/gnd#preferredNameForThePerson','String'),
            'dateOfBirth': (u'http://d-nb.info/standards/elementset/gnd#dateOfBirth', 'GNDDate'),
            'dateOfDeath': (u'http://d-nb.info/standards/elementset/gnd#dateOfDeath', 'GNDDate')}}
    ],
    'Event': [{
        'source': 'GND',
        'type': u'http://d-nb.info/standards/elementset/gnd#HistoricSingleEventOrEra',
        'url': stb_find.format('gndHistoricEvent'),
        'fields': {
            'descr': (u'http://d-nb.info/standards/elementset/gnd#definition','String'),
            'name': (u'http://d-nb.info/standards/elementset/gnd#preferredNameForTheSubjectHeading','String')}}],
    'Work': []
}

geonames_feature_codes = {
    "ADM1": (
        "first-order administrative division",
        "a primary administrative division of a country, such as a state in the United States"),
    "ADM1H": (
        "historical first-order administrative division",
        "a former first-order administrative division"),
    "ADM2": (
        "second-order administrative division",
        "a subdivision of a first-order administrative division"),
    "ADM2H": (
        "historical second-order administrative division",
        "a former second-order administrative division"),
    "ADM3": (
        "third-order administrative division",
        "a subdivision of a second-order administrative division"),
    "ADM3H": (
        "historical third-order administrative division",
        "a former third-order administrative division"),
    "ADM4": (
        "fourth-order administrative division",
        "a subdivision of a third-order administrative division"),
    "ADM4H": (
        "historical fourth-order administrative division",
        "a former fourth-order administrative division"),
    "ADM5": (
        "fifth-order administrative division",
        "a subdivision of a fourth-order administrative division"),
    "ADMD": (
        "administrative division",
        "an administrative division of a country, undifferentiated as to administrative level"),
    "ADMDH": (
        "historical administrative division",
        "a former administrative division of a political entity, \
        undifferentiated as to administrative level"),
    "LTER": (
        "leased area",
        "a tract of land leased to another country, usually for military installations"),
    "PCL": ("political entity", ""),
    "PCLD": ("dependent political entity", ""),
    "PCLF": ("freely associated state", ""),
    "PCLH": ("historical political entity", "a former political entity"),
    "PCLI": ("independent political entity", ""),
    "PCLIX": ("section of independent political entity", ""),
    "PCLS": ("semi-independent political entity", ""),
    "PRSH": ("parish", "an ecclesiastical district"),
    "TERR": ("territory", ""),
    "ZN": ("zone", ""),
    "ZNB": (
        "buffer zone",
        "a zone recognized as a buffer between two nations in which \
        military presence is minimal or absent"),
    "PPL": (
        "populated place",
        "a city, town, village, or other agglomeration of buildings where people live and work"),
    "PPLA": (
        "seat of a first-order administrative division",
        "seat of a first-order administrative division (PPLC takes precedence over PPLA),"),
    "PPLA2": ("seat of a second-order administrative division", ""),
    "PPLA3": ("seat of a third-order administrative division", ""),
    "PPLA4": ("seat of a fourth-order administrative division", ""),
    "PPLC": ("capital of a political entity", ""),
    "PPLCH": (
        "historical capital of a political entity",
        "a former capital of a political entity"),
    "PPLF": (
        "farm village",
        "a populated place where the population is largely engaged in agricultural activities"),
    "PPLG": ("seat of government of a political entity", ""),
    "PPLH": (
        "historical populated place",
        "a populated place that no longer exists"),
    "PPLL": (
        "populated locality",
        "an area similar to a locality but with a small group of dwellings or other buildings"),
    "PPLQ": ("abandoned populated place", ""),
    "PPLR": (
        "religious populated place",
        "a populated place whose population is largely engaged in religious occupations"),
    "PPLS": (
        "populated places",
        "cities, towns, villages, or other agglomerations of buildings where people live and work"),
    "PPLW": (
        "destroyed populated place",
        "a village, town or city destroyed by a natural disaster, or by war"),
    "PPLX": ("section of populated place", ""),
    "STLMT": ("israeli settlement", ""),
    "RGN": ("region", "an area distinguished by one or more observable physical or cultural characteristics")}


class StbGeoQuerySettings:

    def __init__(self, kind='place'):
        self.kind = kind
        self.score = u'http://stanbol.apache.org/ontology/entityhub/query#score'
        self.uri = 'id'
        self.label = u'http://www.w3.org/2000/01/rdf-schema#label'
        self.kind = kind
        self.last_selected = 0

        if kind == 'place':
            self.selected = [gn+'name', gn+'parentPCLI', gn+'parentCountry',
                                gn+'parentADM1', gn+'parentADM2', gn+'parentADM3',
                                gn+'population', gn+'featureCode', wgs84_pos+'lat',
                                wgs84_pos+'long', gn+'alternateName', gn+'officialName',
                                gn+'shortName', gn+'countryCode', gn+'parentFeature']
            self.stored_feature = {
                    'feature': gn+'PPLC',
                    'URL': URL_geonames % 'PPLC'
            }
            self.features = [{
                    'feature': gn+'PPLC',
                    'URL': URL_geonames % 'PPLC'
            },
             {
                    'feature': gn+'PPLA',
                    'URL': URL_geonames % 'PPLA'
            },
                {
                    'feature': gn+'PPLA2',
                    'URL': URL_geonames % 'PPLA2'
            },
                {
                    'feature': gn+'PPLA3',
                    'URL': URL_geonames % 'PPLA3'
            },
                {
                    'feature': gn+'PPLA4',
                    'URL': URL_geonames % 'PPLA4'
            },
                {
                    'feature': gn+'PPL',
                    'URL': URL_geonames % 'PPL'
            }]
        elif kind == 'admin':
            self.selected = [gn+'featureCode']
            self.stored_feature = {
                    'feature': gn+'PCLI',
                    'URL': URL_geonames % 'PCLI'
            }
            self.features = [{
                    'feature': gn+'PCLI',
                    'URL': URL_geonames % 'PCLI'
            },
                {
                    'feature': gn+'ADM1',
                    'URL': URL_geonames % 'ADM1'
            },
                {
                    'feature': gn+'ADM2',
                    'URL': URL_geonames % 'ADM2'
            },
                {
                    'feature': gn+'ADM3',
                    'URL': URL_geonames % 'ADM3'
            }
            ]

    def get_next_feature(self, ft=False):
        if self.last_selected > len(self.features)-1:
            self.stored_feature = False
            return False
        if not ft:
            ft = self.features[self.last_selected]['feature']
        for idnx, x in enumerate(self.features):
            if x['feature'] == ft:
                try:
                    self.last_selected = idnx+1
                    self.stored_feature = self.features[idnx+1]
                    return self.features[idnx+1]
                except:
                    return None
        return self.features[0]

    def get_data(self, query, adm=False):
        if self.kind == 'place' and adm:
            data = {
                'limit': 20, 'constraints': [{
                    'type': 'text',
                    'field': 'http://www.w3.org/2000/01/rdf-schema#label',
                    'text': query},
                    {'type': 'reference', 'field': adm[1], 'value': adm[0]}
                                    ],
                'selected': self.selected
            }
        else:
            data = {
                'limit': 20, 'constraints': [{
                    'type': 'text',
                    'field': 'http://www.w3.org/2000/01/rdf-schema#label',
                    'text': query},
                                    ],
                'selected': self.selected}

        return data
