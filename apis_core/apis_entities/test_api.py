from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from django.contrib.contenttypes.models import ContentType
from rest_framework import status

from .models import Place, Person


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
        user = User.objects.create_user(username="lauren", password="pas_1234$")
        token = Token.objects.create(user=user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        cls.c = client

    def test_apiget(self):
        token = Token.objects.get(user__username='lauren')
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        res = client.get(reverse('apis:apis_core:person-detail', kwargs={'pk': self.person.pk}))
        print(res)


class GetTestCase(TestCase):

    def test_get(self):
        client = APIClient()
        for ent in ContentType.objects.filter(app_label__in=["apis_entities", "apis_relations", "apis_metainfo", "apis_vocabularies"]).exclude(model__in=['tempentityclass', 'relationbaseclass']):
            print(f"Testing GET for: {ent.model.lower().replace(' ', '')}")
            url = reverse(f'apis:apis_core:{ent.model.lower().replace(" ", "")}-list')+'?format=json'
            res = client.get(url)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            d = res.json()
            if len(d['results']) > 0:
                print(f"Result of {ent.model.lower().replace(' ', '')} > 0, testing get of first element")
                res2 = client.get(d['results'][0]['url'])
                self.assertEqual(res2.status_code, status.HTTP_200_OK)
            