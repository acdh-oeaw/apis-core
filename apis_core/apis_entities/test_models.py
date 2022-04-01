from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.urls import reverse

from .models import Person, Event
from apis_core.apis_metainfo.models import Text, Collection
from apis_core.apis_vocabularies.models import ProfessionType
from reversion import revisions as reversion

from datetime import datetime
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from django.contrib.auth.models import Permission


class PersonModelTestCase(TestCase):
    name = "test name"
    first_name = "test first name"
    text = "kjhkjsdhaslkdhadh lasdjalsk alsjdhaksjdh"
    col_name = "Test collection"
    col_name2 = "Test collection2"
    start_date = "1.3.1930"
    end_date = "4.6.1960"
    prof1 = "Lehrer"
    prof2 = "Politiker"

    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        cls.txt = Text.objects.create(text=cls.text)
        cls.col = Collection.objects.create(name=cls.col_name)
        cls.col2 = Collection.objects.create(name=cls.col_name2)
        cls.prof1 = ProfessionType.objects.create(name=cls.prof1)
        cls.prof2 = ProfessionType.objects.create(name=cls.prof2)
        cls.pers1 = Person.objects.create(
            name=cls.name,
            first_name=cls.first_name,
            start_date_written="1880<1880-02-01>",
            end_date_written="1890<1890-05-01>",
        )

    def test_init(self):
        Person()

    def test_create_object(self):
        p = Person.objects.create(
            name=self.name,
            first_name=self.first_name,
            start_date_written=self.start_date,
            end_date_written=self.end_date,
        )

    def test_object_connections(self):
        p = Person.objects.create(
            name=self.name,
            first_name=self.first_name,
            start_date_written=self.start_date,
            end_date_written=self.end_date,
        )
        p.collection.add(self.col)
        p.text.add(self.txt)

    def test_object_validity(self):
        p = Person.objects.create(
            name=self.name,
            first_name=self.first_name,
            start_date_written=self.start_date,
            end_date_written=self.end_date,
        )
        p.collection.add(self.col)
        p.text.add(self.txt)
        self.assertEqual(p.name, self.name)
        self.assertEqual(p.first_name, self.first_name)
        self.assertEqual(p.start_date_written, self.start_date)
        self.assertEqual(p.start_date, datetime.strptime(self.start_date, "%d.%m.%Y"))

    def test_date_parsing_year(self):
        p = Person.objects.create(
            name=self.name,
            first_name=self.first_name,
            start_date_written="1880",
            end_date_written="1890",
        )
        self.assertEqual(p.start_start_date, datetime.strptime("1.1.1880", "%d.%m.%Y"))
        self.assertEqual(p.start_end_date, datetime.strptime("31.12.1880", "%d.%m.%Y"))
        self.assertEqual(p.end_start_date, datetime.strptime("1.1.1890", "%d.%m.%Y"))
        self.assertEqual(p.end_end_date, datetime.strptime("31.12.1890", "%d.%m.%Y"))
        self.assertEqual(p.start_date, datetime.strptime("1.7.1880", "%d.%m.%Y"))

    def test_date_parsing_override(self):
        p = Person.objects.create(
            name=self.name,
            first_name=self.first_name,
            start_date_written="1880<1880-02-01>",
            end_date_written="1890<1890-05-01>",
        )
        self.assertEqual(p.start_date, datetime.strptime("1.2.1880", "%d.%m.%Y"))
        self.assertEqual(p.end_date, datetime.strptime("1.5.1890", "%d.%m.%Y"))

    def test_date_parsing_override_range(self):
        p = Person.objects.create(
            name=self.name,
            first_name=self.first_name,
            start_date_written="1880<1880-05-01,1880-01-01,1880-12-31>",
            end_date_written="1890<1890-05-01>",
        )
        self.assertEqual(p.start_start_date, datetime.strptime("1.1.1880", "%d.%m.%Y"))
        self.assertEqual(p.start_date, datetime.strptime("1.5.1880", "%d.%m.%Y"))
        self.assertEqual(p.start_end_date, datetime.strptime("31.12.1880", "%d.%m.%Y"))

    def test_merge_entities(self):
        p1 = Person.objects.create(name="person1")
        p2 = Person.objects.create(name="person2")
        p1.collection.add(self.col)
        p1.profession.add(self.prof1)
        p2.collection.add(self.col2)
        p2.profession.add(self.prof2)
        p1.merge_with(p2)
        self.assertEqual(p1.collection.all().count(), 2)
        self.assertEqual(p1.profession.all().count(), 2)

    def test_merge_entities_no_selfself(self):
        p1 = Person.objects.first()
        self.assertRaises(ValueError, p1.merge_with, [p1,])
 
"""
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
"""  # TODO: solve the reversion datetime error


class PermissionsModelTestCase(TestCase):
    name = "test name"
    first_name = "test first name"
    text = "kjhkjsdhaslkdhadh lasdjalsk alsjdhaksjdh"
    col_name = "Test collection"
    start_date = "1.3.1930"
    end_date = "4.6.1960"

    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        cls.txt = Text.objects.create(text=cls.text)
        cls.col = Collection.objects.create(name=cls.col_name)
        cls.pers = Person.objects.create(
            name=cls.name,
            first_name=cls.first_name,
            # start_date_written=cls.start_date,  TODO: serializer throwing error on date
            # end_date_written=cls.end_date
        )
        cls.user = User.objects.create_user("testuser", "apisdev16")
        pe = Permission.objects.get(name="Can change person")
        cls.user.user_permissions.add(pe)
        cls.token = Token.objects.create(user=cls.user).key
        cls.group = Group.objects.create(name="testgroup")
        cls.col.groups_allowed.add(cls.group)
        cls.user.groups.add(cls.group)
        cls.c = APIClient()
        cls.c.credentials(HTTP_AUTHORIZATION="Token " + cls.token)

    def test_no_perm(self):
        res = self.c.patch(
            reverse("apis:apis_core:person-detail", kwargs={"pk": self.pers.pk}),
            data={"name": "changed name"},
            # format='json'
        )
        print(f"no permissions, patch: {res.status_code}")
        self.assertEqual(res.status_code, 403)

    def test_no_perm_view(self):
        res = self.c.get(
            reverse("apis:apis_core:person-detail", kwargs={"pk": self.pers.pk}),
        )
        print(f"no permissions, get: {res.status_code}")
        self.assertEqual(res.status_code, 200)

    def test_perm(self):
        self.pers.collection.add(self.col)
        res = self.c.patch(
            reverse("apis:apis_core:person-detail", kwargs={"pk": self.pers.pk}),
            data={"name": "changed name"},
            # format='json'
        )
        print(f"permissions granted, patch: {res.status_code}")
        self.assertEqual(res.status_code, 200)

    def test_perm_removed(self):
        self.pers.collection.remove(self.col)
        res = self.c.patch(
            reverse("apis:apis_core:person-detail", kwargs={"pk": self.pers.pk}),
            data={"name": "changed name"},
            # format='json'
        )
        print(f"permissions revoked, patch: {res.status_code}")
        self.assertEqual(res.status_code, 403)
 