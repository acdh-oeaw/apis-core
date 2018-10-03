from django.test import TestCase

from entities.forms import PersonHighlighterForm
from metainfo.models import Text


class PersonHighlighterFormTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        txt = Text.objects.create(text='hgjhg kjgjhgj')
        cls.form = PersonHighlighterForm({
            'person': 'test',
            'person_uri': 'http://d-nb.info/gnd/118566512',
            'HL_start': 4,
            'HL_end': 6,
            'HL_text_id': 'htxt_' + str(txt.pk)
            })
        cls.form.is_valid()

    def test_init(self):
        PersonHighlighterForm()

    def test_valid_data(self):
        f = PersonHighlighterForm()
        print(f)
        self.assertTrue(self.form.is_valid())

    def test_save_form(self):
        x = self.form.save()
        self.assertEqual(x.name, 'Kreisky')
        self.assertEqual(x.first_name, 'Bruno')
        self.assertEqual(x.start_date_written, '22.01.1911')
        print(x)
