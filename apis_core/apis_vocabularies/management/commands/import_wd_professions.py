import requests
from django.core.management.base import BaseCommand

from apis_core.apis_vocabularies.models import ProfessionType


class Command(BaseCommand):
    # Show this when the user types help
    help = "fetches profession entities from wiki data and imports them as apis ProfessionType"

    def add_arguments(self, parser):
        parser.add_argument(
            '--lang',
            default="en",
            help='A two digit language code. Defaults to en',
        )

    def handle(self, *args, **options):
        url = 'https://query.wikidata.org/sparql'
        query = """
        SELECT ?item ?itemLabel ?description
        WHERE
        {
          ?item wdt:P31 wd:Q28640.
          ?item schema:description ?description FILTER(lang(?description) = "%s")  .
          SERVICE wikibase:label { bd:serviceParam wikibase:language "%s". }
        }
        """
        lang = options['lang']
        r = requests.get(url, params={'format': 'json', 'query': query % (lang, lang)})
        data = r.json()
        data = [
            [
                x['item']['value'],
                x['itemLabel']['value'],
                x['description']['value']
            ] for x in data['results']['bindings']
        ]
        for x in data:
            if x[1].startswith('Q') or x[1].startswith('L'):
                pass
            else:
                label = f"{x[1]} ({x[0].split('/')[-1]})"
                item, _ = ProfessionType.objects.get_or_create(
                    name=label
                )
                item.description = x[2]
                print(item)
