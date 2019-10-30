from django.test import TestCase
from django.contrib.auth.models import User, Group

from .models import Person, Place, Institution, Passage, Event
from apis_core.apis_metainfo.models import Text, Collection, Source, Uri, UriCandidate
from apis_core.apis_vocabularies.models import PersonPlaceRelation
from apis_core.apis_labels.models import Label
from apis_core.apis_relations.models import PersonPlace, PlacePlace, InstitutionPlace
from reversion.models import Version
from reversion import revisions as reversion
from apis_core.helper_functions.RDFparsers import GenericRDFParser
from apis_core.helper_functions.RDFParserNew import RDFParserNew

from datetime import datetime
from guardian.shortcuts import assign_perm, remove_perm, get_objects_for_user
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from django.contrib.auth.models import Permission
from django.db.models import Q


class RDFPersonParerTestCase(TestCase):
    #fixtures = ['fixtures_3_5_17.json']
    uriP = 'http://d-nb.info/gnd/11868499X'
    kindP = 'Person'
    uriGeon = 'http://sws.geonames.org/2761369/'

    def test_parse_person(self):
        print('Number of Persons: {}'.format(Person.objects.all().count()))
        o = GenericRDFParser(self.uriP, self.kindP)
        o2 = o.save()
        print('got following person: {}'.format(o2))
        self.assertEqual(o.objct.name, 'Eosander')
        self.assertEqual(o.objct.first_name, 'Johann Friedrich')

    def test_place_of_birth_death(self):
        o = GenericRDFParser(self.uriP, self.kindP)
        p2 = o.save()
        print(p2.start_date)
        print(p2.end_date)
        rel_type_birth = PersonPlaceRelation.objects.get(name='place of birth')
        rel_type_death = PersonPlaceRelation.objects.get(name='place of death')
        rel_birth = PersonPlace.objects.get(related_person=o.objct, relation_type=rel_type_birth)
        rel_death = PersonPlace.objects.get(related_person=o.objct, relation_type=rel_type_death)
        self.assertEqual(rel_birth.related_place.name, 'Stralsund')
        self.assertEqual(rel_death.related_place.name, 'Dresden')
        plc_list = Label.objects.filter(temp_entity=rel_death.related_place).values_list('label',flat=True)
        print(plc_list)
        self.assertTrue('Dressden' in plc_list)
        self.assertEqual(rel_death.related_place.lat, 13.738319)
        print('lat: {}, lng: {}'.format(rel_death.related_place.lat, rel_death.related_place.lng))

    def test_merge_places(self):
        txt = Passage.objects.create(text='test text')
        src = Source.objects.create(orig_id=24, pubinfo='test pub')
        pp = Place(name="Wien")
        pp.source = src
        pp.save()
        pp.text.add(txt)
        rel_type_birth = PersonPlaceRelation.objects.create(name='place of birth')
        pers = Person.objects.create(name="tesdt", first_name="test3")
        rel_1 = PersonPlace.objects.create(related_person=pers, relation_type=rel_type_birth, related_place=pp)
        ow = GenericRDFParser(self.uriGeon, 'Place')
        print('name: {}, lat: {}, long: {}, labels: {}'.format(ow.objct.name, ow.objct.lat, ow.objct.lng, ' / '.join(
            Label.objects.filter(temp_entity=ow.objct).values_list('label', flat=True))))
        if ow.created:
            print('created triggered')
            ow.save()
        ow2 = ow.merge(pp)
        print(ow)
        print(ow2)
        self.assertEqual(pp.source.pubinfo, ow.objct.source.pubinfo)
        self.assertEqual(txt.text, ow.objct.text.all()[0].text)
        for x in PersonPlace.objects.all():
            self.assertEqual(x.related_place.pk, ow.objct.pk)


class RDFPlaceParserTestCase(TestCase):
    #fixtures = ['fixtures_3_5_17.json']
    kindP = 'Place'
    uriGeon = 'http://sws.geonames.org/2761369/'
    uri_gnd_geo = 'http://d-nb.info/gnd/4023118-5'

    def test_parse_place(self):
        o = GenericRDFParser(self.uriGeon, self.kindP)
        o2 = o.save()
        print('name: {}, lat: {}, long: {}, labels: {}, kind: {}'.format(o2.place.name,
                                                               o2.place.lat, o2.place.lng,
                                                               ' / '.join(Label.objects.filter(temp_entity=o2.place).values_list('label', flat=True)),
                                                                o2.kind.name))
        t = GenericRDFParser(self.uri_gnd_geo, self.kindP)
        t2 = t.save()
        print('name: {}, lat: {}, long: {}, labels: {}'.format(t2.name, t2.lat, t2.lng, ' / '.join(
            Label.objects.filter(temp_entity=t2).values_list('label', flat=True))))
        self.assertEqual(o2.lat, '48.20849')
        self.assertEqual(t2.lat, '053.583329')

    def test_merge_place(self):
        col = Collection.objects.create(name='test coll one')
        col2 = Collection.objects.create(name='test coll 2')
        w1 = Place.objects.create(name='Wien 21 test')
        w1.collection.add(col)
        w1.collection.add(col2)
        w1_label = Label.objects.create(label='Wien label 1', temp_entity=w1)
        w1_uri = Uri.objects.create(uri='http://test.uri.ac.at/orig:id', entity=w1)
        o = GenericRDFParser(self.uriGeon, self.kindP)
        o2 = o.save()
        o.merge(w1)
        for col in o2.collection.all():
            print('collection: {}'.format(col.name))
        self.assertEqual(Label.objects.filter(temp_entity=o2, label='Wien label 1').count(), 1)
        self.assertEqual(Uri.objects.filter(entity=o2, uri='http://test.uri.ac.at/orig:id').count(), 1)
        self.assertEqual(
            Label.objects.filter(label='Wien 21 test', temp_entity=o2, label_type__name='legacy name').count(), 1)
        self.assertEqual(o2.collection.all().count(), 3)

    def test_related_places(self):
        o = GenericRDFParser(self.uriGeon, self.kindP)
        o2 = o.save()
        print(o2)
        print('related_objects: {}'.format(o.related_objcts))
        print('number of placeplace: {}'.format(PlacePlace.objects.all().count()))
        pp = PlacePlace.objects.filter(Q(related_placeA=o2)|Q(related_placeB=o2))
        self.assertEqual(pp.count(), 2)

    def test_existing_place(self):
        c = GenericRDFParser('http://sws.geonames.org/2782113/', self.kindP)
        c.save()
        o = GenericRDFParser(self.uriGeon, self.kindP)
        o2 = o.save()
        Uri.objects.create(uri='http://test.at', entity=o2)
        pp = PlacePlace.objects.filter(Q(related_placeA=o2) | Q(related_placeB=o2))
        self.assertEqual(pp.count(), 2)
        for p in Place.objects.all():
            print('name: {}, uri: {}'.format(p.name, ' / '.join(p.uri_set.all().values_list('uri', flat=True))))
        cc = Place.objects.filter(uri__uri__icontains='http://sws.geonames.org/2782113').distinct()
        self.assertEqual(cc.count(), 1)
        i = GenericRDFParser(self.uriGeon, self.kindP)
        i2 = i.save()
        print(' / '.join(i.objct.uri_set.all().values_list('uri', flat=True)))
        print(i.objct)
        cc = Place.objects.filter(uri__uri=self.uriGeon).distinct()
        self.assertEqual(cc.count(), 1)



class RDFPlaceParserNewTestCase(TestCase):

    def test_parse_place(self):
        plc = [("http://www.geonames.org/6951114/bad-zell.html", "Bad Zell", 48.34906, "http://sws.geonames.org/2782113/", "http://www.geonames.org/ontology#P.PPL"),
               ("http://sws.geonames.org/2779275/", "Freistadt", 48.51103, "http://sws.geonames.org/2782113/", "http://www.geonames.org/ontology#P.PPL"),
               ("http://sws.geonames.org/2761369", "Vienna", 48.20849, "http://sws.geonames.org/2782113/", "http://www.geonames.org/ontology#P.PPLC")
               ]
        for p in plc:
            o = RDFParserNew(p[0], 'Place')
            o.create_objct()
            o2 = o.save()
            print(type(o2.lat))
            self.assertEqual(o2.lat, float(p[2]))
            self.assertEqual(o2.name, p[1])
            self.assertEqual(o2.kind.name, p[4])



    def test_parse_person(self):
        o = RDFParserNew('http://d-nb.info/gnd/118650130', 'Person')
        o.create_objct()
        print(o._foreign_keys)
        print(o.objct)
        print(o._attributes)
        print(o.objct.name)
        print(o._foreign_keys)
        self.assertEqual(o.objct.name, 'Aristoteles')
        o2 = o.save()
        print(o2)
        o3 = RDFParserNew('http://d-nb.info/gnd/118566512', 'Person')
        o3.create_objct()
        print(o3._foreign_keys)
        print(o3.objct)
        print(o3._attributes)
        print(f"name: {o3.objct.name}, {o3.objct.first_name}")
        print(o3._foreign_keys)
        self.assertEqual(o3.objct.name, 'Kreisky')
        self.assertEqual(o3.objct.start_date_written, '1911-01-22')
        o4 = o3.save()
        print(o4)
        print(o4.profession.all())
        print(o4.start_date)

    def test_merge(self):
        o = RDFParserNew('http://d-nb.info/gnd/118566512', 'Person')
        o.create_objct()
        o.save()
        o2 = RDFParserNew('http://d-nb.info/gnd/170686299', 'Person').get_or_create()
        o.merge(o2)
        print(o.objct.uri_set.all())

    def test_place_of_birth(self):
        o = RDFParserNew('http://d-nb.info/gnd/118566512', 'Person')
        o.create_objct()
        o.save()
        for p in PersonPlace.objects.all():
            print(p.related_place.name, p.related_place.uri_set.all(), p.related_place.lat)

    def test_institution(self):
        o = RDFParserNew('http://d-nb.info/gnd/1001454-8', 'Institution')
        o.create_objct()
        o2 = o.save()
        print(o2.pk, o2.start_date, o2.start_date_written)
        print(InstitutionPlace.objects.filter(related_institution_id=o2.pk))
        print(o2.label_set.all().values_list('label'))
        
    def test_use_uri_twice(self):
        o = RDFParserNew("http://www.geonames.org/6951114/bad-zell.html", "Place")
        self.assertRaises(ValueError, RDFParserNew, "http://www.geonames.org/6951114/bad-zell.html", "Place")
