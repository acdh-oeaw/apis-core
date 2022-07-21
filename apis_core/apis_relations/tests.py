# Create your tests here.
from django.test import TestCase
from apis_core.apis_entities.models import Person, Place
from .models import PersonPlace
from apis_core.apis_vocabularies.models import PersonPlaceRelation


class RelationsTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls): 
        cls.pers1 = Person.objects.create(
            name="Smith",
            first_name="John",
            start_date_written="1880<1880-02-01>",
            end_date_written="1890<1890-05-01>",
        )
        cls.place1 = Place.objects.create(name="place1")
        cls.reltype = PersonPlaceRelation.objects.create(name="Rel1", name_reverse="Rel1 reverse")
        cls.rel = PersonPlace.objects.create(
            related_person=cls.pers1, 
            related_place=cls.place1, relation_type=cls.reltype)
        cls.id_rel = cls.rel.id

    def test_delete_entity(self):
        # test that relation is deleted when entity is deleted
        self.assertIsInstance(self.rel, PersonPlace)
        self.place1.delete()
        self.assertIs(PersonPlace.objects.filter(id=self.id_rel).count(), 0)

    def test_delete_relation_type(self):
        # test that relation_type is set to some default when existing relation type is deleted
        self.assertIsInstance(self.rel, PersonPlace)
        self.reltype.delete()
        self.assertIs(PersonPlace.objects.filter(id=self.id_rel).count(), 1)