from functools import reduce

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from drf_yasg import openapi
from drf_yasg.inspectors import CoreAPICompatInspector, NotHandled
from drf_yasg.utils import swagger_auto_schema
from rest_framework import pagination, serializers, viewsets
from rest_framework import renderers
from rest_framework.response import Response
from url_filter.filtersets import ModelFilterSet
from url_filter.integrations.drf_coreapi import CoreAPIURLFilterBackend as DjangoFilterBackend
from django import forms
from url_filter.filters import Filter

#from django_filters.rest_framework import DjangoFilterBackend


if 'apis_highlighter' in getattr(settings, 'INSTALLED_APPS'):
    from apis_core.helper_functions.highlighter import highlight_text_new

from .api_renderers import NetJsonRenderer

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

lst_parameters_retrieve_txt = [
    openapi.Parameter('types', openapi.IN_QUERY, description="Comma separated list of content type ids to show in annotations", type=openapi.TYPE_STRING),
    openapi.Parameter('ann_proj_pk', openapi.IN_QUERY, description="ID of the annotation project to use", type=openapi.TYPE_NUMBER),
    openapi.Parameter('users_show', openapi.IN_QUERY, description="Comma separated list of users. Limits the annotations to those created by the users specified.", type=openapi.TYPE_STRING),
    openapi.Parameter('inline_annotations', openapi.IN_QUERY, description="[Boolean] add annotations with html mark tags to the text variable.", type=openapi.TYPE_BOOLEAN, default=True),
    openapi.Parameter('highlight', openapi.IN_QUERY, description="[Boolean] add annotations; if False only the blank text object will be returned.", type=openapi.TYPE_BOOLEAN, default=True)
]

def create_query_parameters(entity):
    print(entity)
    for f in entity._meta.fields:
        print(f.name, f.__class__.__name__)


class DjangoFilterDescriptionInspector(CoreAPICompatInspector):
   def get_filter_parameters(self, filter_backend):
      if isinstance(filter_backend, DjangoFilterBackend):
         result = super(DjangoFilterDescriptionInspector, self).get_filter_parameters(filter_backend)
         for param in result:
            if not param.get('description', ''):
               param.description = "Filter the returned list by {field_name}".format(field_name=param.name)

         return result

      return NotHandled



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


class ApisBaseSerializer(serializers.Serializer):
    id = serializers.ReadOnlyField()
    label = serializers.SerializerMethodField(method_name="add_label")
    url = serializers.SerializerMethodField(method_name="add_uri")

    def add_label(self, obj):
        return str(obj)

    def add_uri(self, obj):
        return self.context['view'].request.build_absolute_uri(reverse(
            "apis:apis_api:{}-detail".format(obj.__class__.__name__.lower()),
            kwargs={"pk": obj.pk},
        ))

    def add_type(self, obj):
        lst_type = ['kind', 'type', 'collection_type', 'relation_type']
        lst_kind = [x for x in obj._meta.fields if x.name in lst_type and "apis_vocabularies" in str(x.related_model)]
        if len(lst_kind):
            pk_obj = getattr(obj, f"{lst_kind[0].name}_id")
            if pk_obj is not None:
                obj_type = getattr(obj, str(lst_kind[0].name))
                res = {
                    'id': pk_obj,
                    'url': self.context['view'].request.build_absolute_uri(reverse(f"apis:apis_api:{lst_kind[0].related_model.__name__.lower()}-detail", kwargs={"pk": pk_obj})),
                    'type': obj_type.__class__.__name__,
                    'label': str(obj_type),
                    'parent_class': getattr(obj, 'parent_class_id', None)
                }
                return res


class RelationObjectSerializer(ApisBaseSerializer):

    def add_related_entity(self, rel, instance):
        for attr, value in rel.__dict__.items():
            if attr.startswith('related_') and attr.endswith('_id') and value != instance.id:
                rel_obj = getattr(rel, attr[:-3])
                res = {
                    'id': value,
                    'url': self.add_uri(rel_obj),
                    'type': rel_obj.__class__.__name__,
                    'label': str(rel_obj),
                }
                return res


    def add_whole_relation(self, rel, instance):
        res = {
            'id': rel.id,
            'url': self.add_uri(rel),
            'label': str(rel),
            'type': rel.__class__.__name__,
            'relation_type': self.add_type(rel),
            'related_entity': self.add_related_entity(rel, instance)
        }
        return res

    def to_representation(self, instance):
        res = []
        for rel in self._include:
            if hasattr(instance, f"{rel}_set"):
                for rel_inst in getattr(instance, f"{rel}_set").all().select_related():
                    res.append(self.add_whole_relation(rel_inst, instance))
        for t in ['A', 'B']:
            for rel_inst in getattr(instance, f"related_{instance.__class__.__name__.lower()}{t}").all().select_related():
                res.append(self.add_whole_relation(rel_inst, instance))
        return res

    def __init__(self, *args, **kwargs):
        include = kwargs.pop('include')
        super(RelationObjectSerializer, self).__init__(*args, **kwargs)
        self._include = include


class LabelSerializer(ApisBaseSerializer):
    parent_id = serializers.PrimaryKeyRelatedField(many=False, source='parent_class_id', read_only=True)


class RelatedObjectSerializer(ApisBaseSerializer):
    parent_id = serializers.ReadOnlyField(source='parent_class_id')


def generic_serializer_creation_factory():
    for cont in ContentType.objects.filter(app_label__in=['apis_entities', 'apis_metainfo', 'apis_relations', 'apis_vocabularies']):


        print(cont)
        if cont.name != "passagelanguage":

            test_search = getattr(settings, cont.app_label.upper(), False)
            entity_str = str(cont).replace(' ', '')
            entity = cont.model_class()
            app_label = cont.app_label.replace(' ', '_')
            exclude_lst = []
            if app_label == "apis_entities":
                exclude_lst = deep_get(
                    test_search, "{}.api_exclude".format(entity_str), []
                )
            else:
                set_prem = getattr(settings, f"{cont.app_label.upper()}", {})
                exclude_lst = deep_get(set_prem, "exclude", [])
                exclude_lst.extend(
                    deep_get(set_prem, "{}.exclude".format(entity_str), [])
                )
            exclude_lst_fin = [x for x in exclude_lst if x in [x.name for x in entity._meta.get_fields()]]

            class Meta:
                model = entity
                exclude = exclude_lst_fin

            def to_representation_txt(self, instance):
                res = {
                    'id': instance.pk,
                    'url': self.context['view'].request.build_absolute_uri(reverse(
                            "apis:apis_api:{}-detail".format(instance.__class__.__name__.lower()),
                            kwargs={"pk": instance.pk},
                            )),
                    'text': instance.text
                }
                if self._highlight:
                    txt_html, annotations = highlight_text_new(instance,
                        set_ann_proj=self._ann_proj_pk, types=self._types, users_show=self._users_show,
                        inline_annotations=self._inline_annotations)
                    res['text'] = txt_html
                    res['annotations'] = annotations
                return res

            def init_text_serializer(self, *args, **kwargs):
                super(self.__class__, self).__init__(*args, **kwargs)
                action = self.context['view'].action
                highlight = self.context['request'].query_params.get('highlight', None)
                if action == 'retrieve' and highlight is not None and 'apis_highlighter' in getattr(settings,'INSTALLED_APPS'):
                    self._highlight = True
                    self._ann_proj_pk = self.context['request'].query_params.get('ann_proj_pk', None)
                    self._types = self.context['request'].query_params.get('types', None)
                    self._users_show = self.context['request'].query_params.get('users_show', None)
                    self._inline_annotations = self.context['request'].query_params.get('inline_annotations', True)
                    if self._inline_annotations.lower() == 'false':
                        self._inline_annotations = False
                else:
                    self._highlight = False


            def init_serializers(self, *args, **kwargs):
                super(self.__class__, self).__init__(*args, **kwargs)
                entity_str = self._entity.__name__
                action = self.context['view'].action
                include = self.context['request'].query_params.get('include', None)
                if include is not None and action == 'retrieve':
                    include = include.split(',')
                    if 'relations' in include:
                        include = list(ContentType.objects.filter(app_label="apis_relations", model__icontains=entity_str).values_list('model', flat=True))
                        print(include)
                    if len(include) > 0:
                        self.fields['relations'] = RelationObjectSerializer(read_only=True, source='*', include=include)
                app_label = self._app_label
                lst_labels_set = deep_get(
                        getattr(settings, app_label.upper(), {}),
                        "{}.labels".format(entity_str),
                        [],
                    )
                for f in self._entity._meta.get_fields():
                    if getattr(settings, "APIS_API_EXCLUDE_SETS", False) and str(f.name).endswith('_set'):
                        if f.name in self.fields.keys():
                            self.fields.pop(f.name)
                        continue
                    ck_many = f.__class__.__name__ == 'ManyToManyField'
                    if f.name in self._exclude_lst:
                        continue
                    elif f.__class__.__name__ in ["ManyToManyField", "ForeignKey"] and "apis_vocabularies" not in str(f.related_model):
                        self.fields[f.name] = RelatedObjectSerializer(many=ck_many, read_only=True)
                    elif f.__class__.__name__ in ["ManyToManyField", "ForeignKey"]:
                        self.fields[f.name] = LabelSerializer(many=ck_many, read_only=True)

            s_dict = {
                "id": serializers.ReadOnlyField(),
                "url": serializers.HyperlinkedIdentityField(
                    view_name=f"apis:apis_api:{entity_str.lower()}-detail"),
                "_entity": entity,
                "_exclude_lst": exclude_lst_fin,
                "_app_label": app_label,
                "Meta": Meta,
                "add_labels": lambda self, obj: {"id": obj.pk, "label": str(obj)},
                "__init__": init_serializers
            }
            if entity_str.lower() == 'text':
                s_dict['__init__'] = init_text_serializer
                s_dict['to_representation'] = to_representation_txt
            serializer_class = type(f"{entity_str.title().replace(' ', '')}Serializer", (serializers.HyperlinkedModelSerializer,), s_dict)
            allowed_fields_filter = {'IntegerField': ['in', 'range'],
                                     'CharField': ['exact', 'icontains', 'iregex', 'isnull'],
                                     'BooleanField': ['exact'],
                                     'DateField': ['year', 'lte', 'gte', 'day', 'month']}
            filterset_dict = {}
            filter_fields = []

            for field in entity._meta.fields:
                if field.__class__.__name__ == 'AutoField':
                    f_class = 'IntegerField'
                else:
                    f_class = field.__class__.__name__
                if f_class not in allowed_fields_filter.keys():
                    continue
                filterset_dict[field.name] = Filter(form_field=getattr(forms, f_class)(),
                                                    lookups=allowed_fields_filter[f_class])
                filter_fields.append(field.name)

            class MetaFilter(object):
                model = entity
                fields = filter_fields

            filterset_dict['Meta'] = MetaFilter

            filter_class = type(f"Generic{entity_str.title().replace(' ', '')}FilterClass", (ModelFilterSet,), filterset_dict)

            def get_queryset(self):
                if "apis_relations" in str(self.model):
                    return self.model.objects.filter_for_user()
                return self.model.objects.all()

            @swagger_auto_schema(filter_inspectors=[DjangoFilterDescriptionInspector,])
            def list_viewset(self, request):
                res = super(self.__class__, self).list(request)
                return res

            @swagger_auto_schema(manual_parameters=lst_parameters_retrieve_txt)
            def retrieve_view_txt(self, request, pk=None):
                res = super(self.__class__, self).retrieve(request, pk=pk)
                return res

            viewset_dict = {
                'pagination_class': CustomPagination,
                'model': entity,
                #'queryset': entity.objects.all(),
                'filter_backends': (DjangoFilterBackend, ),
                #'filter_fields': ['']
                'depth': 2,
                'renderer_classes': (renderers.JSONRenderer, renderers.BrowsableAPIRenderer, NetJsonRenderer),
                'filter_class': filter_class,
                'serializer_class': serializer_class,
                "get_queryset": get_queryset,
                #'list': list_viewset,
                'dispatch': lambda self, request, *args, **kwargs: super(self.__class__, self).dispatch(request, *args, **kwargs)
                }
            if entity_str.lower() == 'text':
                viewset_dict['retrieve'] = retrieve_view_txt
            views[f"{entity_str.lower().replace(' ', '')}"] = type(f"Generic{entity_str.title().replace(' ', '')}ViewSet", (viewsets.ModelViewSet, ), viewset_dict)


views = dict()
generic_serializer_creation_factory()
