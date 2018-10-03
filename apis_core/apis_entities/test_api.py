from rest_framework.test import APIClient
from django.test import TestCase
from rest_framework.authtoken.models import Token

from .models import Place, Person
from relations.models import PersonPlace
from vocabularies.models import PersonPlaceRelation


class PersonModelTestCase(TestCase):
    name = 'test name'
    first_name = 'test first name'
    place_name = 'test place name'
    start_date = '1.3.1930'
    end_date = '4.6.1960'

    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        cls.person = Person.objects.create(name=cls.name, first_name=cls.first_name)
        cls.place = Place.objects.create(name=cls.place_name)
        token = Token.objects.get(user__username='lauren')
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        cls.c = client

    def test_apiget(self):
        token = Token.objects.get(user__username='lauren')
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)