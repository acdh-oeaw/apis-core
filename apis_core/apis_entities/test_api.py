from django.urls import reverse
from rest_framework.test import APIClient
from django.test import TestCase
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

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