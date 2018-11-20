from django.test import TestCase

from .models import Text, Source
from apis_core.apis_vocabularies.models import TextType
from apis_highlighter.models import Annotation


class TextModelTestCase(TestCase):
    text = 'Hallo wir sind heute in Wien. Wie geht es euch?'
    source_name = 'testsource'
    ann_start = 5
    ann_stop = 10


    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        cls.source = Source.objects.create(pubinfo=cls.source_name)

    def test_init(self):
        Text()

    def test_add_to_text(self):
        txt = Text.objects.create(text=self.text, source=self.source)
        ann = Annotation.objects.create(start=self.ann_start, end=self.ann_stop, text=txt)
        anno_orig = txt.text[ann.start:ann.end]
        txt.text = txt.text[:self.ann_start-3]+ 'test....'+txt.text[self.ann_start-2:]
        txt.save()
        ann2 = Annotation.objects.get(pk=ann.pk)
        anno_change = txt.text[ann2.start:ann2.end]
        self.assertEqual(anno_orig, anno_change)

    def test_delete_text(self):
        txt = Text.objects.create(text=self.text, source=self.source)
        ann = Annotation.objects.create(start=self.ann_start, end=self.ann_stop, text=txt)
        anno_orig = txt.text[ann.start:ann.end]
        print('test2: '+txt.text)
        txt.text = txt.text[:self.ann_start-4]+ txt.text[self.ann_start-2:]
        txt.save()
        ann2 = Annotation.objects.get(pk=ann.pk)
        anno_change = txt.text[ann2.start:ann2.end]
        self.assertEqual(anno_orig, anno_change)

    def test_anno_in_delete(self):
        txt = Text.objects.create(text=self.text, source=self.source)
        ann = Annotation.objects.create(start=self.ann_start, end=self.ann_stop, text=txt)
        anno_orig = txt.text[ann.start:ann.end]
        txt.text = txt.text[:self.ann_start - 2] + txt.text[self.ann_stop - 2:]
        txt.save()
        with self.assertRaises(Annotation.DoesNotExist):
            Annotation.objects.get(pk=ann.pk)
