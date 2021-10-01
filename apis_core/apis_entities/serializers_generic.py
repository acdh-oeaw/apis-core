import re

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models.query import QuerySet
from django.urls import reverse
from rest_framework import serializers
from reversion.models import Version

from apis_core.apis_labels.serializers import LabelSerializerLegacy as LabelSerializer

base_uri = getattr(settings, "APIS_BASE_URI", "http://apis.info")
if base_uri.endswith("/"):
    base_uri = base_uri[:-1]


class CollectionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class VocabsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    label = serializers.CharField()


class EntityUriSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    uri = serializers.URLField()


class TextSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    kind = VocabsSerializer()
    text = serializers.CharField()


class EntitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    url = serializers.SerializerMethodField(method_name="add_url")
    name = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    uris = EntityUriSerializer(source="uri_set", many=True)
    labels = LabelSerializer(source="label_set", many=True)
    revisions = serializers.SerializerMethodField(method_name="add_revisions")

    def add_revisions(self, obj):
        ver = Version.objects.get_for_object(obj)
        res = []
        for v in ver:
            usr_1 = getattr(v.revision, "user", None)
            if usr_1 is not None:
                usr_1 = usr_1.username
            else:
                usr_1 = "Not specified"
            res.append(
                {
                    "id": v.id,
                    "date_created": v.revision.date_created,
                    "user_created": usr_1,
                }
            )
        return res

    def add_relations(self, obj):
        res = {}
        mk = obj.__class__.__name__
        for rel in ContentType.objects.filter(
            app_label="apis_relations", model__icontains=mk.lower()
        ):
            mk2 = re.match(r"{}([A-Za-z]+)".format(mk.lower()), rel.model)
            reverse = False
            if not mk2:
                mk2 = re.match(r"([A-Za-z]+){}".format(mk.lower()), rel.model)
                reverse = True
            res["{}s".format(mk2.group(1))] = []
            if mk2.group(1).lower() != mk.lower():
                if self._only_published:
                    rel_qs = (
                        getattr(obj, "{}_set".format(rel.model)).all().filter_for_user()
                    )
                else:
                    rel_qs = getattr(obj, "{}_set".format(rel.model)).all()
                for rel2 in rel_qs:
                    res["{}s".format(mk2.group(1))].append(
                        RelationEntitySerializer(
                            rel2,
                            own_class=mk,
                            read_only=True,
                            context=self.context,
                            reverse=reverse,
                        ).data
                    )
            else:
                for t in ["A", "B"]:
                    for rel2 in (
                        getattr(obj, "related_{}{}".format(mk.lower(), t))
                        .all()
                        .filter_for_user()
                    ):
                        if t == "A":
                            ok = "{}B".format(mk.lower())
                            reverse = True
                        else:
                            ok = "{}A".format(mk.lower())
                            reverse = False
                        res["{}s".format(mk2.group(1))].append(
                            RelationEntitySerializer(
                                rel2,
                                own_class=ok,
                                read_only=True,
                                context=self.context,
                                reverse=reverse,
                            ).data
                        )
        return res

    def add_entity_type(self, obj):
        return str(obj.__class__.__name__)

    def add_url(self, obj):
        url = f"{base_uri}{reverse('GetEntityGenericRoot', kwargs={'pk': obj.pk})}"
        return url

    def __init__(
        self, *args, depth_ent=1, only_published=True, add_texts=False, **kwargs
    ):
        super(EntitySerializer, self).__init__(*args, **kwargs)
        self._only_published = only_published
        if type(self.instance) == QuerySet:
            inst = self.instance[0]
        else:
            inst = self.instance
        if inst is None:
            return
        for f in inst._meta.fields:
            field_name = re.search(r"([A-Za-z]+)\'>", str(f.__class__)).group(1)
            if field_name in [
                "CharField",
                "DateField",
                "DateTimeField",
                "IntegerField",
                "FloatField",
            ]:
                self.fields[f.name] = getattr(serializers, field_name)()
            elif field_name in ["ForeignKey", "ManyToMany"]:
                if str(f.related_model.__module__).endswith("apis_vocabularies.models"):
                    many = False
                    if f.many_to_many or f.one_to_many:
                        many = True
                    self.fields[f.name] = VocabsSerializer(many=many)
        for f in inst._meta.many_to_many:
            if f.name.endswith("relationtype_set"):
                continue
            elif f.name == "collection":
                self.fields["collection"] = CollectionSerializer(many=True)
            elif str(f.related_model.__module__).endswith("apis_vocabularies.models"):
                self.fields[f.name] = VocabsSerializer(many=True)
        self.fields["entity_type"] = serializers.SerializerMethodField(
            method_name="add_entity_type"
        )
        if depth_ent == 1:
            self.fields["relations"] = serializers.SerializerMethodField(
                method_name="add_relations"
            )
        if add_texts:
            self.fields["text"] = TextSerializer(many=True)


class RelationEntitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    start_date_written = serializers.DateField()
    end_date_written = serializers.DateField()
    relation_type = serializers.SerializerMethodField(method_name="add_relation_label")
    annotation = serializers.SerializerMethodField(method_name="add_annotations")
    revisions = serializers.SerializerMethodField(method_name="add_revisions")

    def add_revisions(self, obj):
        ver = Version.objects.get_for_object(obj)
        res = []
        for v in ver:
            usr_1 = getattr(v.revision, "user", None)
            if usr_1 is not None:
                usr_1 = usr_1.username
            else:
                usr_1 = "Not specified"
            res.append(
                {
                    "id": v.id,
                    "date_created": v.revision.date_created,
                    "user_created": usr_1,
                }
            )
        return res

    def add_annotations(self, obj):
        if "apis_highlighter" in settings.INSTALLED_APPS:
            res = []
            offs = 50
            for an in obj.annotation_set.all():
                r1 = dict()
                r1["id"] = an.pk
                r1["user"] = an.user_added.username
                text = an.text.text
                if offs < an.start:
                    s = an.start - offs
                else:
                    s = 0
                if offs + an.end < len(text):
                    e = an.end + offs
                else:
                    e = len(text)
                r1["annotation"] = text[an.start : an.end]
                r1["text"] = text[s:e]
                r1["text"] = "{}<annotation>{}</annotation>{}".format(
                    r1["text"][: an.start - s],
                    r1["text"][an.start - s : an.end - s],
                    r1["text"][an.end - s :],
                )
                r1["text"] = r1["text"].replace("\r\n", "<br/>")
                r1["text"] = r1["text"].replace("\r", "<br/>")
                r1["text"] = r1["text"].replace("\n", "<br/>")

                r1["string_offset"] = "{}-{}".format(an.start, an.end)
                # r1["text_url"] = self.context["request"].build_absolute_uri(
                #        reverse("apis_core:apis_api:text-detail", kwargs={"pk": an.text_id})
                # )
                r1[
                    "text_url"
                ] = f"{base_uri}{reverse('apis_core:apis_api:text-detail', kwargs={'pk': an.text_id})}"
                res.append(r1)
            return res

    def add_entity(self, obj):
        return EntitySerializer(
            getattr(obj, "related_{}".format(self.entity_type)), depth_ent=0
        ).data

    def add_relation_label(self, obj):
        cm = obj.__class__.__name__
        res_1 = dict()
        res_1["id"] = obj.relation_type.pk
        res_1[
            "url"
        ] = f"{base_uri}{reverse('apis_core:apis_api:{}relation-detail'.format(cm).lower(), kwargs={'pk': obj.relation_type.pk},)}"
        if self.reverse and len(obj.relation_type.label_reverse) > 0:
            res_1["label"] = obj.relation_type.label_reverse
        elif self.reverse:
            res_1["label"] = "({})".format(obj.relation_type.label)
        else:
            res_1["label"] = obj.relation_type.label
        return res_1

    def __init__(self, *args, own_class=None, reverse=False, **kwargs):
        super(RelationEntitySerializer, self).__init__(*args, **kwargs)
        self.own_class = own_class
        self.reverse = reverse
        if self.instance is not None:
            for f in self.instance._meta.fields:
                if f.name.startswith("related_"):
                    mk2 = f.name.replace("related_", "")

                    if mk2.lower() != own_class.lower():
                        self.entity_type = mk2
                        self.fields["target"] = serializers.SerializerMethodField(
                            method_name="add_entity"
                        )
