import re
import requests
from django.core.management.base import BaseCommand, CommandError

import pandas as pd
from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef
from rdflib.namespace import DC, FOAF

from apis_vocabularies.models import ProfessionType


def get_professions():
    """ helper function to fetch all profession entities from wikidata
        :return: pandas dataframe with wikidata-id|label
    url = 'https://query.wikidata.org/sparql'
    """

    query = """
    SELECT ?item ?itemLabel
    WHERE
    {
      ?item wdt:P31 wd:Q28640.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    """
    r = requests.get(url, params={'format': 'json', 'query': query})
    data = r.json()
    df = pd.DataFrame(
        [[x['item']['value'], x['itemLabel']['value']] for x in data['results']['bindings']]
    )
    df.drop(df.loc[df[1].str.startswith("Q")].index, inplace=True)
    df.drop(df.loc[df[1].str.startswith("L")].index, inplace=True)
    return df


class Command(BaseCommand):
    # Show this when the user types help
    help = "fetches profession entities from wiki data and imports them as apis ProfessionType"

    def handle(self, *args, **kwargs):
        for i, row in get_professions().iterrows():
            wd_id = row[0].split('/')[-1]
            name = f"{row[1]} ({wd_id})"
            item, _ = ProfessionType.objects.get_or_create(
                name=name
            )
            g = rdflib.Graph()
            my_graph = g.parse(row[0])
            description = row[0]
            for s, p, o in g.triples((URIRef(row[0]), ns_schema.description, None)):
                if o.language == "en":
                    description = o._value
            # TODO: fetch parent class
            item.description = description
            item.save()
