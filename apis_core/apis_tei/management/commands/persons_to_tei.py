import lxml.etree as ET
from django.core.management.base import BaseCommand

from apis_core.apis_tei.tei_utils import get_node_from_template, Person, TEMPLATE_PATH, tei_header

class Command(BaseCommand):
    help = 'Command to serialize APIS Persons to XML/TEI persons.xml'

    def add_arguments(self, parser):
        parser.add_argument(
            '--full',
            help='should related entities e.g. birth-places be fully serialized',
        )
        parser.add_argument(
            '--collection',
            help='which collection?',
        )
    
    def handle(self, *args, **options):

        tei_doc = tei_header()
        listperson = tei_doc.xpath("//*[local-name() = 'listPerson']")[0] 

        if options['full']:
            print("full is set")
            full = True
        else:
            print("simple")
            full = False
        
        if options['collection']:
            try:
                col_id = int(options['collection'])
            except ValueError:
                print(f"collection needs to be an integer and not: {options['collection']}")
                return False
        
            items = Person.objects.filter(collection=col_id)
        else:
            items = Person.objects.all()
        print(f"serialize {items.count()} Persons")
        for res in items:
            item_node = get_node_from_template(
                TEMPLATE_PATH, res, full=full
            )
            listperson.append(item_node)
        
        with open('listperson.xml', 'w') as f:
            print(ET.tostring(tei_doc).decode('utf-8'), file=f)
        print("done")
