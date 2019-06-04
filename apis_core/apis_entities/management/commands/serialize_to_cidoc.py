from django.core.management.base import BaseCommand, CommandError
from apis_core.apis_entities.models import Person
from django.contrib.contenttypes.models import ContentType
from apis_core.apis_entities.serializers_generic import EntitySerializer
from apis_core.apis_entities.api_renderers import EntityToCIDOC
import json
from django.conf import settings
import requests
from rdflib import Graph
from rdflib.plugins.memory import IOMemory


map_ct = {
    'trig': ('application/x-trig', 'trig'),
    'trix': ('application/trix', 'trix'),
    'xml': ('application/rdf+xml', 'xml'),
    'turtle': ('application/x-turtle', 'ttl'),
    'n3': ('text/rdf+n3', 'n3')
}

base_uri = getattr(settings, 'APIS_BASE_URI', 'http://apis.info')
if base_uri.endswith('/'):
    base_uri = base_uri[:-1]


class Command(BaseCommand):
    help = 'Command to serialize APIS data to cidoc and update a triple store.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--filter',
            action='store',
            dest='filter',
            default="{}",
            help='Specify a dictionary of filter arguments for the Entity queryset.',
        )

        parser.add_argument(
            '--entity',
            action='store',
            dest='entity',
            default='Person',
            help='Specify a dictionary of filter arguments for the Person queryset.',
        )

        parser.add_argument(
            '--update',
            action='store_true',
            dest='update',
            default=False,
            help='Use to update triple store (needs credentials).',
        )

        parser.add_argument(
            '--triple-store',
            action='store',
            dest='triplestore',
            default=False,
            help='Specify a tuple of URL, username, password to access triple-store.',
        )

        parser.add_argument(
            '--delete',
            action='store_true',
            dest='delete',
            default=True,
            help='Use to delete the named graph before inserting (defaults to True).',
        )

        parser.add_argument(
            '--named-graph',
            action='store',
            dest='namedgraph',
            default=False,
            help='Uri of named graph to use.',
        )

        parser.add_argument(
            '--output',
            action='store',
            dest='output',
            default=False,
            help='Path of file to store RDF in.',
        )

        parser.add_argument(
            '--format',
            action='store',
            dest='format',
            default='xml',
            help='Format to use (xml, trig, n3, turtle, nquads, trix).',
        )

    def handle(self, *args, **options):
        ent = ContentType.objects.get(app_label="apis_entities", model=options['entity']).model_class()
        res = []
        for e in ent.objects.filter(**json.loads(options['filter'])):
            res.append(EntitySerializer(e).data)
        self.stdout.write(self.style.SUCCESS(f'serialized {len(res)} objects'))
        self.stdout.write(self.style.NOTICE('Starting to create the graph'))
        store = IOMemory()
        fin, store = EntityToCIDOC().render(res, format_1=options['format'], store=store)
        if options['output']:
            with open(options['output'], 'wb') as out:
                out.write(fin)
            self.stdout.write(self.style.SUCCESS(f'Wrote file to {options["output"]}'))
        if options['update']:
            if not options['triplestore']:
                url, username, password = getattr(settings, 'APIS_BLAZEGRAPH', (False, False, False))
                if not url:
                    self.stdout.write(self.style.ERROR('When asking for update you need to either specify settings in APIS_BLAZEGRAPH or in the management command (--triple-store)'))
                    return
            else:
                url, username, password = options['triplestore']
                if not url or not username or not password:
                    self.stdout.write(self.style.ERROR('Missing some settings for Triplestore update'))
                    return
            if options['delete']:
                if not options['namedgraph']:
                    params = {'c': f'<{base_uri}/entities#>'}
                    res3 = requests.delete(url, auth=(username, password), headers={'Accept': 'application/xml'}, params=params)
                    self.stdout.write(self.style.NOTICE(f'Deleted the graph: {res3.text} {res3.status_code}'))
            header = {'Content-Type': map_ct[options['format']][0]}
            res2 = requests.post(url, headers=header, data=fin, auth=(username, password))
            if res2.status_code != 200:
                self.stdout.write(self.style.ERROR(f'Something went wrong when updating: {res2.text}'))
            else:
                self.stdout.write(self.style.SUCCESS('Updated the triplestore.'))
