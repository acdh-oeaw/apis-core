import time

from django.test import TestCase

from apis_core.apis_relations.models import PersonPlace, InstitutionPlace
from apis_core.helper_functions.RDFParser import RDFParser


class RDFPlaceParserNewTestCase(TestCase):

    def test_parse_place(self):
        plc = [("http://www.geonames.org/6951114/bad-zell.html", "Bad Zell", 48.34906, "http://sws.geonames.org/2782113/", "https://www.geonames.org/ontology#P.PPL"),
               ("http://sws.geonames.org/2779275/", "Freistadt", 48.51103, "http://sws.geonames.org/2782113/", "https://www.geonames.org/ontology#P.PPL"),
               ("http://sws.geonames.org/2761369", "Vienna", 48.20849, "http://sws.geonames.org/2782113/", "https://www.geonames.org/ontology#P.PPLC")
               ]
        for p in plc:
            print(p)
            o = RDFParser(p[0], 'Place')
            o.create_objct()
            o2 = o.save()
            print(type(o2.lat))
            self.assertEqual(o2.lat, float(p[2]))
            self.assertEqual(o2.name, p[1])
            self.assertEqual(o2.kind.name, p[4])



    #def test_parse_person(self):
     #   o = RDFParser('http://d-nb.info/gnd/118650130', 'Person', uri_check=False)
      #  o.create_objct()
       # print(o._foreign_keys)
        #print(o.objct)
       # print(o._attributes)
       # print(o.objct.name)
       # print(o._foreign_keys)
       # self.assertEqual(o.objct.name, 'Aristoteles')
       # o2 = o.save()
       # print(o2)
       # o3 = RDFParser('http://d-nb.info/gnd/118566512', 'Person', uri_check=False)
       # o3.create_objct()
       # print(o3._foreign_keys)
       # print(o3.objct)
       # print(o3._attributes)
       # print(f"name: {o3.objct.name}, {o3.objct.first_name}")
       # print(o3._foreign_keys)
       # self.assertEqual(o3.objct.name, 'Kreisky')
       # self.assertEqual(o3.objct.start_date_written, '1911-01-22')
       # o4 = o3.save()
       # print(o4)
       # print(o4.profession.all())
       # print(o4.start_date)

    def test_merge(self):
        o = RDFParser('http://d-nb.info/gnd/118566512', 'Person', uri_check=False)
        o.create_objct()
        o.save()
        o2 = RDFParser('http://d-nb.info/gnd/170686299', 'Person', uri_check=False).get_or_create()
        o.merge(o2)
        print(o.objct.uri_set.all())

    def test_place_of_birth(self):
        o = RDFParser('http://d-nb.info/gnd/118566512', 'Person', uri_check=False)
        o.create_objct()
        o.save()
        for p in PersonPlace.objects.all():
            print(p.related_place.name, p.related_place.uri_set.all(), p.related_place.lat)

    def test_institution(self):
        o = RDFParser('http://d-nb.info/gnd/1001454-8', 'Institution', uri_check=False)
        o.create_objct()
        o2 = o.save()
        print(o2.pk, o2.start_date, o2.start_date_written)
        print(InstitutionPlace.objects.filter(related_institution_id=o2.pk))
        print(o2.label_set.all().values_list('label'))
        
    def test_use_uri_twice(self):
        self.assertRaises(ValueError, RDFParser, "http://www.geonames.org/6951114/bad-zell.html", "Place")

    def test_uri_twice_later(self):
        o = RDFParser('https://sws.geonames.org/2778843', 'Place', preserve_uri_minutes=0.5)
        self.assertRaises(ValueError, RDFParser, 'https://sws.geonames.org/2778843', "Place", preserve_uri_minutes=0.5)
        time.sleep(35)
        o2 = RDFParser('https://sws.geonames.org/2778843', 'Place', preserve_uri_minutes=0.5).get_or_create()

    def test_institution_government(self):
        o = RDFParser('https://d-nb.info/gnd/2029534-0', 'Institution').get_or_create()
        self.assertEqual(o.name, 'Österreich. Bundesregierung')
        #self.assertEqual(o.start_date_written, '1945')

    def test_uni_koeln(self):
        o = RDFParser('https://d-nb.info/gnd/2024231-1', 'Institution')
        o.create_objct()
        print(o._foreign_keys)
        o2 = o.save()
        for p in InstitutionPlace.objects.filter(related_institution_id=o2.pk):
            print(p.related_place, p.related_place.kind)
