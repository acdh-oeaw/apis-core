import lxml.etree as ET
from django.core.management.base import BaseCommand
from tqdm import tqdm

from apis_core.apis_entities.models import Person
from apis_core.apis_tei.tei_utils import get_node_from_template, tei_header

class Command(BaseCommand):
    help = 'Command to serialize APIS Persons to XML/TEI persons.xml'

    def add_arguments(self, parser):
        parser.add_argument(
            '-l',
            '--limit',
            action='store_true',
            help='number of entities should be limited',
        )
        parser.add_argument(
            '-f',
            '--full',
            action='store_true',
            help='should related entities e.g. birth-places be fully serialized',
        )
        parser.add_argument(
            '--collection',
            help='which collection?',
        )
    
    def handle(self, *args, **kwargs):

        tei_doc = tei_header()
        listperson = tei_doc.xpath("//*[local-name() = 'listPerson']")[0] 

        if kwargs['full']:
            print("full is set")
            full = True
        else:
            print("simple")
            full = False
        
        if kwargs['collection']:
            try:
                col_id = int(kwargs['collection'])
            except ValueError:
                print(f"collection needs to be an integer and not: {kwargs['collection']}")
                return False
        
            items = Person.objects.filter(collection=col_id)
        else:
            items = Person.objects.all()
        if kwargs['limit']:
            items = items[:25]
        print(f"serialize {items.count()} Persons")
        for res in tqdm(items, total=len(items)):
            item_node = get_node_from_template(
                'apis_tei/person.xml', res, full=full
            )
            listperson.append(item_node)
        
        with open('listperson.xml', 'w') as f:
            print(ET.tostring(tei_doc).decode('utf-8'), file=f)
        print("done")
