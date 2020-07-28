import json
import os
import pickle

from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder

from apis_core.apis_entities.models import AbstractEntity
from apis_core.apis_entities.serializers_generic import EntitySerializer


class Command(BaseCommand):
    help = 'Command to serialize APIS data to json and store the data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--entity',
            action='store',
            dest='entity',
            default='Person',
            help='Specify the named entity to serialize.',
        )

        parser.add_argument(
            '--output',
            action='store',
            dest='output',
            default=False,
            help='Path of file to store JSON in.',
        )

        parser.add_argument(
            '--only-published',
            action='store_true',
            dest='only-published',
            default=False,
            help='Set if you want to include published relations only. (Boolean, Default: False).',
        )

        parser.add_argument(
            '--filter',
            action='store',
            dest='filter',
            default="{}",
            help='Specify a dictionary of filter arguments for the Entity queryset.',
        )

        parser.add_argument(
            '--use-cache',
            action='store_true',
            dest='use-cache',
            default=False,
            help='Set if you want to use the cached files instead of serializing them egain (Boolean, Default: False).',
        )

        parser.add_argument(
            '--add-texts',
            action='store_true',
            dest='add-texts',
            default=False,
            help='Set if you want to add the texts attached to the entities (Boolean, Default: False).',
        )

    def handle(self, *args, **options):
        ent = AbstractEntity.get_entity_class_of_name(options['entity'])
        res = []
        objcts = ent.objects.filter(**json.loads(options['filter']))
        if objcts.filter(uri__uri__icontains=' ').count() > 0:
            self.stdout.write(self.style.ERROR('URIs found that contain whitespaces'))
            return
        if objcts.count() > 1000 and not options['use-cache']:
            self.stdout.write(self.style.NOTICE('More than 1000 objects, caching'))
            cnt = 0
            while (cnt * 1000) < objcts.count():
                r = []
                for e in objcts[1000*cnt:(1000*cnt+1000)]:
                    r.append(EntitySerializer(e, only_published=options['only-published'], add_texts=options['add-texts']).data)
                with open(f'serializer_cache/{cnt}.pkl', 'wb') as out:
                    pickle.dump(r, out)
                    self.stdout.write(self.style.NOTICE(f'Pickle written to: serializer_cache/{cnt}.pkl'))
                cnt += 1
            res = '/home/sennierer/projects/apis-webpage-base/serializer_cache'
        elif not options['use-cache']:
            for e in objcts:
                res.append(EntitySerializer(e, only_published=options['only-published'], add_texts=options['add-texts']).data)
        elif options['use-cache']:
            self.stdout.write(self.style.NOTICE('using cache for serializing'))
            res = '/home/sennierer/projects/apis-webpage-base/serializer_cache'
        self.stdout.write(self.style.SUCCESS(f'serialized {len(res)} objects'))
        self.stdout.write(self.style.NOTICE('Starting to create the json file'))
        with open(options['output'], 'w+') as outp:
            if isinstance(res, str):
                directory = os.fsencode(res)
                data_lst = []
                for fn in os.listdir(directory):
                    with open(os.path.join(directory, fn), 'rb') as inf:
                        data_lst.extend(pickle.load(inf))
                json.dump(data_lst, outp, cls=DjangoJSONEncoder)
            elif isinstance(res, list):
                json.dump(res, out, pcls=DjangoJSONEncoder)