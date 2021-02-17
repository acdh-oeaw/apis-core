import re
import unicodedata
from difflib import SequenceMatcher

import requests

# from reversion import revisions as reversion
import reversion
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils.functional import cached_property
from model_utils.managers import InheritanceManager

from apis_core.apis_entities.serializers_generic import EntitySerializer
from apis_core.apis_labels.models import Label
from apis_core.apis_vocabularies.models import CollectionType, LabelType, TextType

# from helper_functions.highlighter import highlight_text
from apis_core.default_settings.NER_settings import autocomp_settings
from apis_core.helper_functions import DateParser

NEXT_PREV = getattr(settings, "APIS_NEXT_PREV", True)


if "apis_highlighter" in settings.INSTALLED_APPS:
    from apis_highlighter.models import Annotation


@reversion.register()
class TempEntityClass(models.Model):
    """Base class to bind common attributes to many classes.

    The common attributes are:
    written start and enddates
    recognized start and enddates which are derived by RegEx
    from the written dates.
    A review boolean field to mark an object as reviewed
    """

    name = models.CharField(max_length=255, blank=True)
    review = models.BooleanField(
        default=False,
        help_text="Should be set to True, if the data record holds up quality standards.",
    )
    start_date = models.DateField(blank=True, null=True)
    start_start_date = models.DateField(blank=True, null=True)
    start_end_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    end_start_date = models.DateField(blank=True, null=True)
    end_end_date = models.DateField(blank=True, null=True)
    start_date_written = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Start",
    )
    end_date_written = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="End",
    )
    text = models.ManyToManyField("Text", blank=True)
    collection = models.ManyToManyField("Collection")
    status = models.CharField(max_length=100)
    source = models.ForeignKey(
        "Source", blank=True, null=True, on_delete=models.SET_NULL
    )
    references = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    published = models.BooleanField(default=False)
    objects = models.Manager()
    objects_inheritance = InheritanceManager()

    def __str__(self):
        if self.name != "" and hasattr(
            self, "first_name"
        ):  # relation usually don´t have names
            return "{}, {} (ID: {})".format(self.name, self.first_name, self.id)
        elif self.name != "":
            return "{} (ID: {})".format(self.name, self.id)
        else:
            return "(ID: {})".format(self.id)

    def save(self, parse_dates=True, *args, **kwargs):
        """Adaption of the save() method of the class to automatically parse string-dates into date objects"""

        if parse_dates:

            # overwrite every field with None as default
            start_date = None
            start_start_date = None
            start_end_date = None
            end_date = None
            end_start_date = None
            end_end_date = None

            if self.start_date_written:
                # If some textual user input of a start date is there, then parse it

                start_date, start_start_date, start_end_date = DateParser.parse_date(
                    self.start_date_written
                )

            if self.end_date_written:
                # If some textual user input of an end date is there, then parse it

                end_date, end_start_date, end_end_date = DateParser.parse_date(
                    self.end_date_written
                )

            self.start_date = start_date
            self.start_start_date = start_start_date
            self.start_end_date = start_end_date
            self.end_date = end_date
            self.end_start_date = end_start_date
            self.end_end_date = end_end_date

        if self.name:
            self.name = unicodedata.normalize("NFC", self.name)

        super(TempEntityClass, self).save(*args, **kwargs)

        return self

    def get_child_entity(self):
        for x in [x for x in apps.all_models["apis_entities"].values()]:
            if x.__name__ in list(settings.APIS_ENTITIES.keys()):
                try:
                    my_ent = x.objects.get(id=self.id)
                    return my_ent
                    break
                except ObjectDoesNotExist:
                    pass
        return None

    @classmethod
    def get_listview_url(self):
        entity = self.__name__.lower()
        if entity == "institution" or len(entity) < 10:
            return reverse(
                "apis_core:apis_entities:generic_entities_list",
                kwargs={"entity": entity},
            )
        else:
            return reverse(
                "apis_core:apis_relations:generic_relations_list",
                kwargs={"entity": entity},
            )

    @classmethod
    def get_createview_url(self):
        entity = self.__name__.lower()
        if entity == "institution" or len(entity) < 10:
            return reverse(
                "apis_core:apis_entities:generic_entities_create_view",
                kwargs={"entity": entity},
            )
        else:
            return None

    def get_edit_url(self):
        entity = self.__class__.__name__.lower()
        if entity == "institution" or len(entity) < 10:
            return reverse(
                "apis_core:apis_entities:generic_entities_edit_view",
                kwargs={"entity": entity, "pk": self.id},
            )
        else:
            return None

    def get_child_class(self):
        child = self.get_child_entity()
        if child:
            return "{}".format(child.__class__.__name__)
        else:
            return "{}".format(child.__class__.__name__)

    def get_absolute_url(self):
        entity = self.__class__.__name__.lower()
        if entity == "institution" or len(entity) < 10:
            return reverse(
                "apis_core:apis_entities:generic_entities_detail_view",
                kwargs={"entity": entity, "pk": self.id},
            )
        elif entity == "tempentityclass":
            return self.get_child_entity().get_absolute_url()
        else:
            return reverse(
                "apis_core:apis_relations:generic_relations_detail_view",
                kwargs={"entity": entity, "pk": self.id},
            )

    def get_prev_url(self):
        entity = self.__class__.__name__.lower()
        if NEXT_PREV:
            prev = self.__class__.objects.filter(id__lt=self.id).order_by("-id")
        else:
            return False
        if prev:
            if entity == "institution" or len(entity) < 10:
                return reverse(
                    "apis_core:apis_entities:generic_entities_detail_view",
                    kwargs={"entity": entity, "pk": prev.first().id},
                )
            else:
                return reverse(
                    "apis_core:apis_relations:generic_relations_detail_view",
                    kwargs={"entity": entity, "pk": prev.first().id},
                )
        else:
            return False

    def get_next_url(self):
        entity = self.__class__.__name__.lower()
        if NEXT_PREV:
            next = self.__class__.objects.filter(id__gt=self.id)
        else:
            return False
        if next:
            if entity == "institution" or len(entity) < 10:
                return reverse(
                    "apis_core:apis_entities:generic_entities_detail_view",
                    kwargs={"entity": entity, "pk": next.first().id},
                )
            else:
                return reverse(
                    "apis_core:apis_relations:generic_relations_detail_view",
                    kwargs={"entity": entity, "pk": next.first().id},
                )
        else:
            return False

    def get_delete_url(self):
        entity = self.__class__.__name__.lower()
        if entity == "institution" or len(entity) < 10:
            return reverse(
                "apis_core:apis_entities:generic_entities_delete_view",
                kwargs={"entity": entity, "pk": self.id},
            )
        else:
            return None

    def merge_with(self, entities):
        e_a = type(self).__name__
        self_model_class = ContentType.objects.get(
            app_label="apis_entities", model__iexact=e_a
        ).model_class()
        if isinstance(entities, int):
            entities = self_model_class.objects.get(pk=entities)
        if not isinstance(entities, list) and not isinstance(entities, QuerySet):
            entities = [entities]
            entities = [
                self_model_class.objects.get(pk=ent) if type(ent) == int else ent
                for ent in entities
            ]
        rels = ContentType.objects.filter(
            app_label="apis_relations", model__icontains=e_a
        )
        for ent in entities:
            e_b = type(ent).__name__
            if e_a != e_b:
                continue
            lt, created = LabelType.objects.get_or_create(name="Legacy name (merge)")
            col_list = list(self.collection.all())
            for col2 in ent.collection.all():
                if col2 not in col_list:
                    self.collection.add(col2)
            for f in ent._meta.local_many_to_many:
                if not f.name.endswith("_set"):
                    sl = list(getattr(self, f.name).all())
                    for s in getattr(ent, f.name).all():
                        if s not in sl:
                            getattr(self, f.name).add(s)
            Label.objects.create(label=str(ent), label_type=lt, temp_entity=self)
            for u in Uri.objects.filter(entity=ent):
                u.entity = self
                u.save()
            for l in Label.objects.filter(temp_entity=ent):
                l.temp_entity = self
                l.save()
            for r in rels.filter(model__icontains=e_b):
                lst_ents_rel = str(r).split()
                if lst_ents_rel[0] == lst_ents_rel[1]:
                    q_d = {"related_{}A".format(e_b.lower()): ent}
                    k = r.model_class().objects.filter(**q_d)
                    for t in k:
                        setattr(t, "related_{}A".format(e_a.lower()), self)
                        t.save()
                    q_d = {"related_{}B".format(e_b.lower()): ent}
                    k = r.model_class().objects.filter(**q_d)
                    for t in k:
                        setattr(t, "related_{}B".format(e_a.lower()), self)
                        t.save()
                else:
                    q_d = {"related_{}".format(e_b.lower()): ent}
                    k = r.model_class().objects.filter(**q_d)
                    for t in k:
                        setattr(t, "related_{}".format(e_a.lower()), self)
                        t.save()
            ent.delete()

    def get_serialization(self):
        return EntitySerializer(self).data


@reversion.register()
class Source(models.Model):
    """ Holds information about entities and their relations"""

    orig_filename = models.CharField(max_length=255, blank=True)
    indexed = models.BooleanField(default=False)
    pubinfo = models.CharField(max_length=400, blank=True)
    author = models.CharField(max_length=255, blank=True)
    orig_id = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        if self.author != "" and self.orig_filename != "":
            return "{}, stored by {}".format(self.orig_filename, self.author)
        else:
            return "(ID: {})".format(self.id)


@reversion.register()
class Collection(models.Model):
    """ Allows to group entities and relation. """

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    collection_type = models.ForeignKey(
        CollectionType, blank=True, null=True, on_delete=models.SET_NULL
    )
    groups_allowed = models.ManyToManyField(Group)
    parent_class = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.CASCADE
    )
    published = models.BooleanField(default=False)

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._loaded_values = dict(zip(field_names, values))
        return instance

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if hasattr(self, "_loaded_values"):
            if self.published != self._loaded_values["published"]:
                for ent in self.tempentityclass_set.all():
                    ent.published = self.published
                    ent.save()
        super().save(*args, **kwargs)


@reversion.register()
class Text(models.Model):
    """Holds unstructured text associeted with
    one ore many entities/relations."""

    kind = models.ForeignKey(TextType, blank=True, null=True, on_delete=models.SET_NULL)
    text = models.TextField(blank=True)
    source = models.ForeignKey(Source, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        if self.text != "":
            return "ID: {} - {}".format(self.id, self.text[:25])
        else:
            return "ID: {}".format(self.id)

    def save(self, *args, **kwargs):
        if self.pk is not None:
            orig = Text.objects.get(pk=self.pk)
            if orig.text != self.text and "apis_highlighter" in settings.INSTALLED_APPS:
                ann = Annotation.objects.filter(text_id=self.pk).order_by("start")
                seq = SequenceMatcher(None, orig.text, self.text)
                for a in ann:
                    changed = False
                    count = 0
                    for s in seq.get_matching_blocks():
                        count += 1
                        if s.a <= a.start and (s.a + s.size) >= a.end:
                            cor = 0
                            if s.a < s.b:
                                nl = re.findall(r"\n", self.text[s.a : s.b])
                                cor -= len("".join(nl)) + len(nl)
                            elif s.a > s.b:
                                nl = re.findall(r"\n", orig.text[s.b : s.a])
                                cor += len("".join(nl)) + len(nl)
                            a.start += s.b - s.a + cor
                            a.end += s.b - s.a + cor
                            a.save()
                            changed = True
                    if not changed:
                        a.delete()  # TODO: we might want to delete relations as well.
        super().save(*args, **kwargs)


@reversion.register()
class Uri(models.Model):
    uri = models.URLField(blank=True, null=True, unique=True, max_length=255)
    domain = models.CharField(max_length=255, blank=True)
    rdf_link = models.URLField(blank=True)
    entity = models.ForeignKey(
        TempEntityClass, blank=True, null=True, on_delete=models.CASCADE
    )
    # loaded set to True when RDF was loaded and parsed into the data model
    loaded = models.BooleanField(default=False)
    # Timestamp when file was loaded and parsed
    loaded_time = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return str(self.uri)

    def get_web_object(self):
        result = {
            "relation_pk": self.pk,
            "relation_type": "uri",
            "related_entity": self.entity.name,
            "related_entity_url": self.entity.get_absolute_url(),
            "related_entity_class_name": self.entity.__class__.__name__.lower(),
            "uri": self.uri,
        }
        return result

    @classmethod
    def get_listview_url(self):
        return reverse("apis_core:apis_metainfo:uri_browse")

    @classmethod
    def get_createview_url(self):
        return reverse("apis_core:apis_metainfo:uri_create")

    def get_absolute_url(self):
        return reverse("apis_core:apis_metainfo:uri_detail", kwargs={"pk": self.id})

    def get_delete_url(self):
        return reverse("apis_core:apis_metainfo:uri_delete", kwargs={"pk": self.id})

    def get_edit_url(self):
        return reverse("apis_core:apis_metainfo:uri_edit", kwargs={"pk": self.id})


@reversion.register()
class UriCandidate(models.Model):
    """Used to store the URI candidates for automatically generated entities."""

    uri = models.URLField()
    confidence = models.FloatField(blank=True, null=True)
    responsible = models.CharField(max_length=255)
    entity = models.ForeignKey(
        TempEntityClass, blank=True, null=True, on_delete=models.CASCADE
    )

    @cached_property
    def description(self):
        headers = {"accept": "application/json"}
        cn = TempEntityClass.objects_inheritance.get_subclass(
            id=self.entity_id
        ).__class__.__name__
        for endp in autocomp_settings[cn.title()]:
            url = re.sub(r"/[a-z]+$", "/entity", endp["url"])
            params = {"id": self.uri}
            res = requests.get(url, params=params, headers=headers)
            if res.status_code == 200:
                if endp["fields"]["descr"][0] in res.json()["representation"].keys():
                    desc = res.json()["representation"][endp["fields"]["descr"][0]][0][
                        "value"
                    ]
                else:
                    desc = "undefined"
                label = res.json()["representation"][endp["fields"]["name"][0]][0][
                    "value"
                ]
                return (label, desc)


# @receiver(post_save, sender=Uri, dispatch_uid="remove_default_uri")
# def remove_default_uri(sender, instance, **kwargs):
#    if Uri.objects.filter(entity=instance.entity).count() > 1:
#        Uri.objects.filter(entity=instance.entity, domain="apis default").delete()
