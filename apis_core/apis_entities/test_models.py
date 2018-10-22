from django.test import TestCase
from django.contrib.auth.models import User, Group

from .models import Person, Place, Institution, Work, Event
from apis_core.apis_metainfo.models import Text, Collection, Source, Uri, UriCandidate
from apis_core.apis_vocabularies.models import PersonPlaceRelation
from apis_core.apis_labels.models import Label
from apis_core.apis_relations.models import PersonPlace
from reversion.models import Version
from reversion import revisions as reversion
from apis_core.helper_functions.RDFparsers import GenericRDFParser

from datetime import datetime
from guardian.shortcuts import assign_perm, remove_perm, get_objects_for_user
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from django.contrib.auth.models import Permission


class PersonModelTestCase(TestCase):
    name = 'test name'
    first_name = 'test first name'
    text = 'kjhkjsdhaslkdhadh lasdjalsk alsjdhaksjdh'
    col_name = 'Test collection'
    start_date = '1.3.1930'
    end_date = '4.6.1960'

    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        cls.txt = Text.objects.create(text=cls.text)
        cls.col = Collection.objects.create(name=cls.col_name)

    def test_init(self):
        Person()

    def test_create_object(self):
        p = Person.objects.create(
            name=self.name,
            first_name=self.first_name,
            start_date_written=self.start_date,
            end_date_written=self.end_date)

    def test_object_connections(self):
        p = Person.objects.create(
            name=self.name,
            first_name=self.first_name,
            start_date_written=self.start_date,
            end_date_written=self.end_date)
        p.collection.add(self.col)
        p.text.add(self.txt)

    def test_object_validity(self):
        p = Person.objects.create(
            name=self.name,
            first_name=self.first_name,
            start_date_written=self.start_date,
            end_date_written=self.end_date)
        p.collection.add(self.col)
        p.text.add(self.txt)
        self.assertEqual(p.name, self.name)
        self.assertEqual(p.first_name, self.first_name)
        self.assertEqual(p.start_date_written, self.start_date)
        self.assertEqual(p.start_date, datetime.strptime(self.start_date, '%d.%m.%Y'))

    def test_object_reversion(self):
        with reversion.create_revision():
            p = Person.objects.create(
                name=self.name,
                first_name=self.first_name,
                start_date_written=self.start_date,
                end_date_written=self.end_date)
            p.collection.add(self.col)
            p.text.add(self.txt)
        with reversion.create_revision():
            p2 = Person.objects.get(name=self.name)
            p2.name = 'testname 2'
            p2.save()
        self.assertEqual(p2.name, 'testname 2')
        versions = Version.objects.get_for_object(p2)
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0].field_dict['name'], 'testname 2')
        self.assertEqual(versions[1].field_dict['name'], self.name)


class PermissionsModelTestCase(TestCase):
    name = 'test name'
    first_name = 'test first name'
    text = 'kjhkjsdhaslkdhadh lasdjalsk alsjdhaksjdh'
    col_name = 'Test collection'
    start_date = '1.3.1930'
    end_date = '4.6.1960'

    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        cls.txt = Text.objects.create(text=cls.text)
        cls.col = Collection.objects.create(name=cls.col_name)
        cls.pers = Person.objects.create(
            name=cls.name,
            first_name=cls.first_name,
            start_date_written=cls.start_date,
            end_date_written=cls.end_date)
        cls.user = User.objects.create_user(
            'testuser',
            'apisdev16')
        pe = Permission.objects.get(name="Can change person")
        cls.user.user_permissions.add(pe)
        cls.token = Token.objects.create(user=cls.user).key
        cls.group = Group.objects.create(name='testgroup')
        cls.col.groups_allowed.add(cls.group)
        cls.user.groups.add(cls.group)
        cls.c = APIClient()
        cls.c.credentials(HTTP_AUTHORIZATION='Token ' + cls.token)

    def test_no_perm(self):
        res = self.c.patch(
            '/api/person/'+str(self.pers.pk)+'/',
            data={
            'name': 'changed name'
            },
            #format='json'
            )
        print(res.content)
        self.assertEqual(res.status_code, 403)

    def test_perm(self):
        self.pers.collection.add(self.col)
        res = self.c.patch(
            '/api/person/'+str(self.pers.pk)+'/',
            data={
            'name': 'changed name'
            },
            #format='json'
            )
        self.assertEqual(res.status_code, 200)

    def test_perm_removed(self):
        self.pers.collection.remove(self.col)
        res = self.c.patch(
            '/api/person/'+str(self.pers.pk)+'/',
            data={
            'name': 'changed name'
            },
            #format='json'
            )
        self.assertEqual(res.status_code, 403)


