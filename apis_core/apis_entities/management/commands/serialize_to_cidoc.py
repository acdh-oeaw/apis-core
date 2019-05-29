from django.core.management.base import BaseCommand, CommandError
from apis_core.apis_entities.models import Person


class Command(BaseCommand):
    help = 'Command to serialize APIS data to cidoc and update a triple store.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--filter',
            action='store',
            dest='filter',
            default=False,
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

    def handle(self, *args, **options):

