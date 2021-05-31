from functools import reduce
import copy
import importlib
import inspect

from django.conf import settings

# from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import pagination, serializers, viewsets
from rest_framework import renderers
from rest_framework.response import Response
from drf_spectacular.contrib.django_filters import (
    DjangoFilterBackend as DjangoFilterbackendSpectacular,
)
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_field,
    OpenApiParameter,
    extend_schema_serializer,
)
from drf_spectacular.types import OpenApiTypes
from django import forms
from django_filters import rest_framework as filters
from .apis_metainfo.models import TempEntityClass
from .api_renderers import NetJsonRenderer
from .apis_relations.models import AbstractRelation
from apis_core.helper_functions.ContentType import GetContentTypes


if "apis_highlighter" in getattr(settings, "INSTALLED_APPS"):
    from apis_highlighter.highlighter import highlight_text_new
    from apis_highlighter.serializer import annotationSerializer
    from apis_highlighter.models import Annotation


try:
    MAX_AGE = settings.MAX_AGE
except AttributeError:
    MAX_AGE = 0


def deep_get(dictionary, keys, default=None):
    return reduce(
        lambda d, key: d.get(key, default) if isinstance(d, dict) else default,
        keys.split("."),
        dictionary,
    )


def create_query_parameters(entity):
    print(entity)
    for f in entity._meta.fields:
        print(f.name, f.__class__.__name__)


class CustomPagination(pagination.LimitOffsetPagination):
    def get_paginated_response(self, data):
        return Response(
            {
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "count": self.count,
                "limit": self.limit,
                "offset": self.offset,
                "results": data,
            }
        )


class ApisBaseSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    label = serializers.SerializerMethodField(method_name="add_label")
    url = serializers.SerializerMethodField(method_name="add_uri")

    @extend_schema_field(OpenApiTypes.INT)
    def add_id(self, obj):
        return obj.pk

    @extend_schema_field(OpenApiTypes.STR)
    def add_label(self, obj):
        return str(obj)

    @extend_schema_field(OpenApiTypes.URI)
    def add_uri(self, obj):
        return self.context["view"].request.build_absolute_uri(
            reverse(
                "apis:apis_api:{}-detail".format(obj.__class__.__name__.lower()),
                kwargs={"pk": obj.pk},
            )
        )

    @extend_schema_field(OpenApiTypes.OBJECT)
    def add_type(self, obj):
        lst_type = ["kind", "type", "collection_type", "relation_type"]
        lst_kind = [
            x
            for x in obj._meta.fields
            if x.name in lst_type and "apis_vocabularies" in str(x.related_model)
        ]
        if len(lst_kind):
            pk_obj = getattr(obj, f"{lst_kind[0].name}_id")
            if pk_obj is not None:
                obj_type = getattr(obj, str(lst_kind[0].name))
                res = {
                    "id": pk_obj,
                    "url": self.context["view"].request.build_absolute_uri(
                        reverse(
                            f"apis:apis_api:{lst_kind[0].related_model.__name__.lower()}-detail",
                            kwargs={"pk": pk_obj},
                        )
                    ),
                    "type": obj_type.__class__.__name__,
                    "label": str(obj_type),
                    "parent_class": getattr(obj, "parent_class_id", None),
                }
                return res

    class Meta:
        model = TempEntityClass
        fields = ["id", "label", "url"]


class EntitySerializer(ApisBaseSerializer):
    type = serializers.SerializerMethodField(method_name="add_type")

    def add_type(self, instance):
        return instance.__class__.__name__

    class Meta(ApisBaseSerializer.Meta):
        fields = ApisBaseSerializer.Meta.fields + ["type"]


class LabelSerializer(ApisBaseSerializer):
    parent_id = serializers.PrimaryKeyRelatedField(
        many=False, source="parent_class_id", read_only=True
    )

    @extend_schema_field(OpenApiTypes.INT)
    def add_parent_id(self, obj):
        return obj.parent_class_id

    class Meta(ApisBaseSerializer.Meta):
        fields = ApisBaseSerializer.Meta.fields + [
            "parent_id",
        ]


class VocabsBaseSerializer(LabelSerializer, EntitySerializer):
    pass


class RelationObjectSerializer2(ApisBaseSerializer):
    relation_type = VocabsBaseSerializer(read_only=True)
    related_entity = serializers.SerializerMethodField(method_name="add_related_entity")

    @extend_schema_field(EntitySerializer)
    def add_related_entity(self, instance):
        for at in dir(instance):
            if (
                at.startswith("related_")
                and at.endswith("_id")
                and getattr(instance, at) != self._pk_instance
            ):
                return EntitySerializer(
                    getattr(instance, at[:-3]), context=self.context
                ).data

    class Meta(ApisBaseSerializer.Meta):
        fields = ApisBaseSerializer.Meta.fields + ["relation_type", "related_entity"]

    def __init__(self, *args, **kwargs):
        self._pk_instance = kwargs.pop("pk_instance")
        super(RelationObjectSerializer2, self).__init__(*args, **kwargs)


if "apis_highlighter" in getattr(settings, "INSTALLED_APPS"):

    class AnnotationSerializer(serializers.ModelSerializer):
        related_object = VocabsBaseSerializer(
            source="get_related_entity", read_only=True, many=False
        )

        class Meta:
            model = Annotation
            fields = ["id", "start", "end", "related_object"]


def generic_serializer_creation_factory():
    # lst_cont = [x.model_class() for x in ContentType.objects.filter(app_label__in=['apis_metainfo', 'apis_vocabularies', 'apis_entities', 'apis_relations']).exclude(model__in=["texttype_collections", "relationbaseclass"])]
    lst_cont = GetContentTypes().get_model_classes()
    not_allowed_filter_fields = [
        "useradded",
        "vocab_name",
        "parent_class",
        "vocab",
        "entity",
        "autofield",
    ]
    for cont in lst_cont:
        prefetch_rel = []
        select_related = []
        test_search = getattr(settings, cont.__module__.split(".")[1].upper(), False)
        entity_str = str(cont.__name__).replace(" ", "")
        entity = cont
        app_label = cont.__module__.split(".")[1].lower()
        exclude_lst = []
        if app_label == "apis_entities":
            exclude_lst = deep_get(test_search, "{}.api_exclude".format(entity_str), [])
        else:
            set_prem = getattr(settings, cont.__module__.split(".")[1].upper(), {})
            exclude_lst = deep_get(set_prem, "exclude", [])
            exclude_lst.extend(deep_get(set_prem, "{}.exclude".format(entity_str), []))
        exclude_lst_fin = [
            x for x in exclude_lst if x in [x.name for x in entity._meta.get_fields()]
        ]
        if entity_str.lower() == "text":
            exclude_lst_fin.extend(["kind", "source"])
        if app_label == "apis_relations":
            exclude_lst_fin.extend(["text", "collection"])
        for f in entity._meta.get_fields():
            if f.__class__.__name__ == "ManyToManyField":
                prefetch_rel.append(f.name)
            elif f.__class__.__name__ == "ForeignKey":
                select_related.append(f.name)

        class Meta:
            model = entity
            exclude = exclude_lst_fin

        def txt_serializer_add_text(self, instance):
            if self._inline_annotations:
                return self._txt_html
            else:
                return instance.text

        if "apis_highlighter" in getattr(settings, "INSTALLED_APPS"):

            @extend_schema_field(AnnotationSerializer(many=True))
            def txt_serializer_add_annotations(self, instance):
                if self._highlight:
                    return AnnotationSerializer(
                        self._annotations, context=self.context, many=True
                    ).data
                else:
                    return None

        def init_text_serializer(self, *args, **kwargs):
            super(self.__class__, self).__init__(*args, **kwargs)

            self._highlight = False
            self.fields["kind"] = LabelSerializer(many=False, read_only=True)

        def init_serializers(self, *args, **kwargs):
            super(self.__class__, self).__init__(*args, **kwargs)
            entity_str = self._entity.__name__
            app_label = self._app_label
            lst_labels_set = deep_get(
                getattr(settings, app_label.upper(), {}),
                "{}.labels".format(entity_str),
                [],
            )
            for f in self._entity._meta.get_fields():
                if getattr(settings, "APIS_API_EXCLUDE_SETS", False) and str(
                    f.name
                ).endswith("_set"):
                    if f.name in self.fields.keys():
                        self.fields.pop(f.name)
                    continue
                ck_many = f.__class__.__name__ == "ManyToManyField"
                if f.name in self._exclude_lst:
                    continue
                elif (
                    f.__class__.__name__
                    in [
                        "ManyToManyField",
                        "ForeignKey",
                    ]
                    and "apis_vocabularies" not in str(f.related_model)
                ):
                    self.fields[f.name] = ApisBaseSerializer(
                        many=ck_many, read_only=True
                    )
                elif f.__class__.__name__ in ["ManyToManyField", "ForeignKey"]:
                    self.fields[f.name] = LabelSerializer(many=ck_many, read_only=True)

        s_dict = {
            "id": serializers.ReadOnlyField(),
            "url": serializers.HyperlinkedIdentityField(
                view_name=f"apis:apis_api:{entity_str.lower()}-detail"
            ),
            "_entity": entity,
            "_exclude_lst": exclude_lst_fin,
            "_app_label": app_label,
            "Meta": Meta,
            "add_labels": lambda self, obj: {"id": obj.pk, "label": str(obj)},
            "__init__": init_serializers,
        }
        if entity_str.lower() == "text":
            s_dict["__init__"] = init_text_serializer

        s_dict_detail = copy.deepcopy(s_dict)

        serializer_class = type(
            f"{entity_str.title().replace(' ', '')}Serializer",
            (serializers.HyperlinkedModelSerializer,),
            s_dict,
        )

        def init_serializers_retrieve(self, *args, **kwargs):
            super(self.__class__, self).__init__(*args, **kwargs)
            entity_str = self._entity.__name__
            app_label = self._app_label
            lst_labels_set = deep_get(
                getattr(settings, app_label.upper(), {}),
                "{}.labels".format(entity_str),
                [],
            )
            for f in self._entity._meta.get_fields():
                if getattr(settings, "APIS_API_EXCLUDE_SETS", False) and str(
                    f.name
                ).endswith("_set"):
                    if f.name in self.fields.keys():
                        self.fields.pop(f.name)
                    continue
                ck_many = f.__class__.__name__ == "ManyToManyField"
                if f.name in self._exclude_lst:
                    continue
                elif (
                    f.__class__.__name__
                    in [
                        "ManyToManyField",
                        "ForeignKey",
                    ]
                    and "apis_vocabularies" not in str(f.related_model)
                ):
                    self.fields[f.name] = ApisBaseSerializer(
                        many=ck_many, read_only=True
                    )
                elif f.__class__.__name__ in ["ManyToManyField", "ForeignKey"]:
                    self.fields[f.name] = LabelSerializer(many=ck_many, read_only=True)
            # include = list(ContentType.objects.filter(app_label="apis_relations", model__icontains=entity_str).values_list('model', flat=True))
            include = [
                x
                for x in lst_cont
                if x.__module__ == "apis_core.apis_relations.models"
                and entity_str.lower() in x.__name__.lower()
            ]
            if len(include) > 0 and len(args) > 0:
                inst_pk2 = args[0].pk
                self.fields["relations"] = RelationObjectSerializer2(
                    read_only=True,
                    source="get_related_relation_instances",
                    many=True,
                    pk_instance=inst_pk2,
                )

        def init_text_serializer_retrieve(self, *args, **kwargs):
            super(self.__class__, self).__init__(*args, **kwargs)
            highlight = self.context.get("highlight", True)
            self._inline_annotations = False
            if highlight is not None and "apis_highlighter" in getattr(
                settings, "INSTALLED_APPS"
            ):
                self._highlight = highlight
                if self._highlight == "":
                    self._highlight = True
                if not isinstance(self._highlight, bool):
                    if self._highlight.lower() == "false":
                        self._highlight = False
                self._ann_proj_pk = self.context.get("ann_proj_pk", None)
                self._types = self.context.get("types", None)
                self._users_show = self.context.get("users_show", None)
                self._inline_annotations = self.context.get("inline_annotations", True)
                if not isinstance(self._inline_annotations, bool):
                    if self._inline_annotations.lower() == "false":
                        self._inline_annotations = False
                    elif self._inline_annotations.lower() == "true":
                        self._inline_annotations = True
                try:
                    self._txt_html, self._annotations = highlight_text_new(
                        self.instance,
                        set_ann_proj=self._ann_proj_pk,
                        types=self._types,
                        users_show=self._users_show,
                        inline_annotations=self._inline_annotations,
                    )
                    qs_an = {"text": self.instance}
                    if self._users_show is not None:
                        qs_an["users_added__in"] = self._users_show
                    if self._ann_proj_pk is not None:
                        qs_an["annotation_project_id"] = self._ann_proj_pk
                    #self._annotations = Annotation.objects.filter(
                    #    **qs_an
                    #)  # FIXME: Currently this QS is called twice (highlight_text_new)
                except Exception as e:
                    self._txt_html = ""
                    self._annotations = []
            else:
                self._highlight = False
            self.fields["kind"] = LabelSerializer(many=False, read_only=True)

        s_dict_detail["__init__"] = init_serializers_retrieve

        if entity_str.lower() == "text":
            s_dict_detail["__init__"] = init_text_serializer_retrieve
            s_dict_detail["txt_serializer_add_text"] = txt_serializer_add_text
            s_dict_detail["text"] = serializers.SerializerMethodField(
                method_name="txt_serializer_add_text"
            )
            if "apis_highlighter" in getattr(settings, "INSTALLED_APPS"):
                s_dict_detail[
                    "txt_serializer_add_annotations"
                ] = txt_serializer_add_annotations
                s_dict_detail["annotations"] = serializers.SerializerMethodField(
                    method_name="txt_serializer_add_annotations"
                )

        serializer_class_retrieve = type(
            f"{entity_str.title().replace(' ', '')}DetailSerializer",
            (serializers.HyperlinkedModelSerializer,),
            s_dict_detail,
        )

        allowed_fields_filter = {
            "IntegerField": ["in", "range", "exact"],
            "CharField": ["exact", "icontains", "iregex", "isnull"],
            "DateField": ["year", "lt", "gt", "year__lt", "year__gt", "exact"],
            "PositiveIntegerField": ["in", "range", "exact"],
            "AutoField": ["in", "exact"],
        }
        filterset_dict = {}
        filter_fields = {}

        for field in entity._meta.fields + entity._meta.many_to_many:
            if getattr(settings, "APIS_API_EXCLUDE_SETS", False) and "_set" in str(
                field.name.lower()
            ):
                continue
            if (
                field.name.lower() in not_allowed_filter_fields
                or field.name == "tempentityclass_ptr"
            ):
                continue
            elif field.__class__.__name__ in ["ForeignKey", "ManyToManyField"]:
                filter_fields[field.name] = ["exact"]
                if field.__class__.__name__ == "ForeignKey":
                    filter_fields[field.name].append("in")
                for f2 in field.related_model._meta.fields:
                    if f2.__class__.__name__ in [
                        "CharField",
                        "DateField",
                        "IntegerField",
                        "AutoField",
                    ]:
                        filter_fields[
                            f"{field.name}__{f2.name}"
                        ] = allowed_fields_filter[f2.__class__.__name__]
                continue
            if field.__class__.__name__ in allowed_fields_filter.keys():
                filter_fields[field.name] = allowed_fields_filter[
                    field.__class__.__name__
                ]
            else:
                filter_fields[field.name] = ["exact"]
        additional_filters = getattr(settings, "APIS_API_ADDITIONAL_FILTERS", False)
        if additional_filters:
            if entity_str in additional_filters.keys():
                for f1 in additional_filters[entity_str]:
                    if f1[0] not in filter_fields.keys():
                        filter_fields[f1[0]] = f1[1]

        class MetaFilter(object):
            model = entity
            fields = filter_fields

        filterset_dict["Meta"] = MetaFilter

        def get_queryset(self):
            if "apis_relations" in str(self.model):
                qs = self.model.objects.filter_for_user()
            else:
                qs = self.model.objects.all()
            if len(self._prefetch_rel) > 0:
                qs = qs.prefetch_related(*self._prefetch_rel)
            if len(self._select_related) > 0:
                qs = qs.select_related(*self._select_related)
            return qs

        @extend_schema(responses=serializer_class(many=True))
        def list_viewset(self, request):
            res = super(self.__class__, self).list(request)
            return res

        @extend_schema(
            parameters=[
                OpenApiParameter(
                    name="highlight",
                    description="Whether to add annotations or not, defaults to true",
                    type=OpenApiTypes.BOOL,
                ),
                OpenApiParameter(
                    name="inline_annotations",
                    description="Whether to add html5 mark tags for annotations to the text, defaults to false",
                    type=OpenApiTypes.BOOL,
                ),
                OpenApiParameter(
                    name="ann_proj_pk",
                    description="PK of the annotation project to use for annotations",
                    type=OpenApiTypes.INT,
                ),
                OpenApiParameter(
                    name="types",
                    description="Content type pks of annotation types to show. E.g. PersonPlace relations (comma sperated list)",
                    type=OpenApiTypes.STR,
                ),
                OpenApiParameter(
                    name="users_show",
                    description="Filter annotations for users. PKs of users, comma seperated list",
                    type=OpenApiTypes.STR,
                ),
            ],
            responses={200: serializer_class_retrieve},
        )
        def retrieve_view_txt(self, request, pk=None):
            res = super(self.__class__, self).retrieve(request, pk=pk)
            return res

        def get_serializer_context(self):
            context = super(self.__class__, self).get_serializer_context()
            if self.action == "retrieve" and self.model.__name__.lower() == "text":
                cont = {}
                cont["highlight"] = self.request.query_params.get("highlight", None)
                cont["ann_proj_pk"] = self.request.query_params.get("ann_proj_pk", None)
                cont["types"] = self.request.query_params.get("types", None)
                cont["users_show"] = self.request.query_params.get("users_show", None)
                cont["inline_annotations"] = self.request.query_params.get(
                    "inline_annotations", True
                )
                context.update(cont)
            return context

        def get_serializer_class_f(self, *arg, **kwargs):
            if self.action == "list":
                return self._serializer_class
            else:
                return self._serializer_class_retrieve

        viewset_dict = {
            "_select_related": select_related,
            "_prefetch_rel": prefetch_rel,
            "pagination_class": CustomPagination,
            "model": entity,
            "filter_backends": (DjangoFilterbackendSpectacular,),
            "filterset_fields": filter_fields,
            "depth": 2,
            "renderer_classes": (
                renderers.JSONRenderer,
                renderers.BrowsableAPIRenderer,
                NetJsonRenderer,
            ),
            "_serializer_class": serializer_class,
            "_serializer_class_retrieve": serializer_class_retrieve,
            "get_serializer_class": get_serializer_class_f,
            "get_serializer_context": get_serializer_context,
            "get_queryset": get_queryset,
            "dispatch": lambda self, request, *args, **kwargs: super(
                self.__class__, self
            ).dispatch(request, *args, **kwargs),
        }
        if entity_str.lower() == "text":
            viewset_dict["retrieve"] = retrieve_view_txt
        serializers_dict[serializer_class.__name__] = serializer_class
        views[f"{entity_str.lower().replace(' ', '')}"] = type(
            f"Generic{entity_str.title().replace(' ', '')}ViewSet",
            (viewsets.ModelViewSet,),
            viewset_dict,
        )


serializers_dict = dict()
views = dict()
filter_classes = dict()
lst_filter_classes_check = []
generic_serializer_creation_factory()
