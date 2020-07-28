import ast
import logging

import reversion
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from entities.models import Person
from helper_functions.abbreviation_solver import ResolveAbbreviations
from metainfo.models import Text
from vocabularies.models import TextType


class Command(BaseCommand):
    help = 'Command to resolve abbreviations in APIS biographies.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--person',
            action='store',
            dest='person',
            default=False,
            help='Give a dictionary of query arguments for the persons.',
        )

        parser.add_argument(
            '--includeall',
            action='store_true',
            dest='includeall',
            default=False,
            help='Use "includeaall" to include all persons (overides the person argument).',
        )

        parser.add_argument(
            '--texts',
            action='append',
            dest='texts',
            default=[],
            help='Use to give texttypes to resolve.',
        )

        parser.add_argument(
            '--alltexts',
            action='store_true',
            dest='alltexts',
            default=False,
            help='Use to give process all texts associated with the specified person (overrides texts attribute).',
        )

        parser.add_argument(
            '--appendtexttype',
            action='store',
            dest='appendtexttype',
            default=False,
            help='Term to append to the actual texttype\
             to store the resolved text. Original texttypes are used if not given.',
        )

        parser.add_argument(
            '--username',
            action='store',
            dest='username',
            default=False,
            help='Sketch engine username.',
        )

        parser.add_argument(
            '--password',
            action='store',
            dest='password',
            default=False,
            help='Sketch engine password.',
        )

    def handle(self, *args, **options):
        #print(options)
        user = User.objects.get(username='management_bot')
        user_sketch = options['username']
        password_sketch = options['password']
        txt_type_new = False
        if options['includeall']:
            pq = Person.objects.all()
        else:
            if options['person']:
                q_dict = ast.literal_eval(options['person'].strip())
                pq = Person.objects.filter(**q_dict)
            else:
                raise CommandError('You need to specify either a queryset for Persons or use --includeall')
        if options['alltexts']:
            tq = Text.objects.filter(tempentityclass__in=pq)
        else:
            if options['texts']:
                t_type = TextType.objects.filter(name__in=options['texts'])
                tq = Text.objects.filter(tempentityclass__in=pq, kind=t_type)
            else:
                tq = Text.objects.filter(tempentityclass__in=pq)
        with reversion.create_revision():
            for txt in tq[:2]:
                if options['appendtexttype']:
                    txt_type_new, created = TextType.objects.get_or_create(
                        name='{}_{}'.format(options['text'], options['appendtexttype']))
                if not txt_type_new:
                    txt_type_new, created = TextType.objects.get_or_create(name='default type resolved text')
                pers = txt.tempentityclass_set.all().values_list('pk', flat=True)
                pers = Person.objects.filter(pk__in=pers)
                if len(pers) != 1:
                    logging.warning('Could not identify a persons name. Resolving without person names.')
                    pers_name = None
                else:
                    pers_name = [pers[0].first_name, pers[0].name]
                res = ResolveAbbreviations(text=txt.text, person=pers_name, user=user_sketch, password=password_sketch)
                txt_resolved = res.resolve()
                t1 = Text.objects.create(text=txt_resolved, kind=txt_type_new)
                for pers2 in pers:
                    pers2.text.add(t1)
