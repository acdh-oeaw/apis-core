import inspect
from functools import reduce

import django.db.models.fields as df_fields
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control

from url_filter.integrations.drf import DjangoFilterBackend
from rest_framework import filters, generics, pagination, routers, serializers, viewsets
from rest_framework.permissions import AllowAny, DjangoObjectPermissions
from rest_framework.response import Response
from rest_framework import renderers
from .api_renderers import NetJsonRenderer
from url_filter.filtersets import ModelFilterSet


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


class LabelSerializer(serializers.Serializer):
    id = serializers.ReadOnlyField()
    label = serializers.SerializerMethodField(method_name="add_label")
    url = serializers.SerializerMethodField(method_name="add_uri")

    def add_uri(self, obj):
        return self.context['view'].request.build_absolute_uri(reverse(
            "apis:apis_api:{}-detail".format(obj.__class__.__name__.lower()),
            kwargs={"pk": obj.pk},
        ))

    def add_label(self, obj):
        return str(obj)
    

class RelatedObjectSerializer(serializers.Serializer):
    id = serializers.ReadOnlyField()
    url = serializers.SerializerMethodField(method_name="add_uri")
    type = serializers.SerializerMethodField(method_name="add_type")
    label = serializers.SerializerMethodField(method_name="add_label")

    def add_uri(self, obj):
        return self.context['view'].request.build_absolute_uri(reverse(
            "apis:apis_api:{}-detail".format(obj.__class__.__name__.lower()),
            kwargs={"pk": obj.pk},
        ))

    def add_label(self, obj):
        return str(obj)

    def add_type(self, obj):
        lst_type = ['kind', 'type', 'collection_type']
        lst_kind = [x for x in obj._meta.fields if x.name in lst_type and "apis_vocabularies" in str(x.related_model)]
        if len(lst_kind):
            pk_obj = getattr(obj, f"{lst_kind[0].name}_id")
            if pk_obj is not None:
                return self.context['view'].request.build_absolute_uri(reverse(f"apis:apis_api:{lst_kind[0].related_model.__name__.lower()}-detail", kwargs={"pk": pk_obj}))
            

def generic_serializer_creation_factory():
    for cont in ContentType.objects.filter(app_label__in=['apis_vocabularies', 'apis_metainfo', 'apis_entities', 'apis_relations', ]):
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
        serializer_class = type(f"{entity_str.title().replace(' ', '')}Serializer", (serializers.HyperlinkedModelSerializer,), s_dict)
        
        class Meta_filter(object):
            model = entity
        
        def get_queryset(self):
            if "apis_relations" in str(self.model):
                return self.model.objects.filter_for_user()
            return self.model.objects.all()

        filter_class = type(f"Generic{entity_str.title().replace(' ', '')}FilterClass", (ModelFilterSet,), {'Meta': Meta_filter})
        viewset_dict = {
            'pagination_class': CustomPagination,
            'model': entity,
            #'queryset': entity.objects.all(),
            'filter_backends': (DjangoFilterBackend, ),
            'depth': 2,
            'renderer_classes': (renderers.JSONRenderer, renderers.BrowsableAPIRenderer, NetJsonRenderer),
            'filter_class': filter_class,
            'serializer_class': serializer_class,
            "get_queryset": get_queryset,
            'dispatch': lambda self, request, *args, **kwargs: super(self.__class__, self).dispatch(request, *args, **kwargs)
            }
        views[f"{entity_str.lower().replace(' ', '')}"] = type(f"Generic{entity_str.title().replace(' ', '')}ViewSet", (viewsets.ModelViewSet, ), viewset_dict)


views = dict()
generic_serializer_creation_factory()
