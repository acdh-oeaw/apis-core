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
    uri = serializers.SerializerMethodField(method_name="add_uri")

    def add_uri(self, obj):
        return reverse(
            "apis:apis_api:{}-detail".format(obj.__class__.__name__.lower()),
            kwargs={"pk": obj.pk},
        )

    def add_label(self, obj):
        return str(obj)


def create_generic_api_viewset(**kwargs):

    class GenericFilterSet(ModelFilterSet):
        class Meta(object):
            model = ContentType.objects.get(app_label=kwargs.get("app_label"), model=kwargs.get("entity")).model_class()

    class GenericAPIViewSet(viewsets.ModelViewSet):
        pagination_class = CustomPagination
        entity_str = kwargs.get("entity")
        app_label = kwargs.get("app_label")
        entity = ContentType.objects.get(
            app_label=app_label, model=entity_str.lower()
        ).model_class()
        model = entity
        queryset = entity.objects.all()
        filter_backends = (DjangoFilterBackend, )
        depth = 2
        test_search = getattr(settings, app_label.upper(), False)
        renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer, NetJsonRenderer)
        filter_class = GenericFilterSet

        @method_decorator(cache_control(max_age=MAX_AGE))
        def dispatch(self, request, *args, **kwargs):
            return super(GenericAPIViewSet, self).dispatch(request, *args, **kwargs)

        def get_serializer_class(self):
            entity_str = self.entity_str
            entity = self.entity
            test_search = self.test_search
            app_label = self.app_label
            exclude_lst = []
            if app_label == "apis_entities":
                exclude_lst = deep_get(
                    test_search, "{}.api_exclude".format(entity_str), []
                )
            elif app_label == "apis_relations":
                set_prem = getattr(settings, "APIS_RELATIONS", {})
                exclude_lst = deep_get(set_prem, "exclude", [])
                exclude_lst.extend(
                    deep_get(set_prem, "{}.exclude".format(entity_str), [])
                )
            elif app_label == "apis_vocabularies":
                set_prem = getattr(settings, "APIS_VOCABULARIES", {})
                exclude_lst = deep_get(set_prem, "exclude", [])
                exclude_lst.extend(
                    deep_get(set_prem, "{}.exclude".format(entity_str), [])
                )
            elif app_label == "apis_metainfo":
                set_prem = getattr(settings, "APIS_METAINFO", {})
                exclude_lst = deep_get(set_prem, "exclude", [])
                exclude_lst.extend(
                    deep_get(set_prem, "{}.exclude".format(entity_str), [])
                )

            class CustomSerializer(serializers.HyperlinkedModelSerializer):
                id = serializers.ReadOnlyField()
                url = serializers.HyperlinkedIdentityField(
                    view_name="apis:apis_api:{}-detail".format(entity_str.lower())
                )

                def add_labels(self, obj):
                    return {"id": obj.pk, "label": str(obj)}

                class Meta:
                    model = entity
                    exclude = exclude_lst

                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    for f in entity._meta.get_fields():
                        if f.name in exclude_lst:
                            continue
                        elif (
                            f.__class__.__name__ == "ManyToManyField"
                            and f.name
                            in deep_get(
                                getattr(settings, app_label.upper(), {}),
                                "{}.labels".format(entity_str),
                                [],
                            )
                        ):
                            self.fields[f.name] = LabelSerializer(
                                many=True, read_only=True
                            )
                        elif f.__class__.__name__ == "ManyToManyField":
                            self.fields[f.name] = serializers.HyperlinkedRelatedField(
                                view_name="apis:apis_api:{}-detail".format(
                                    f.related_model.__name__.lower()
                                ),
                                queryset=f.related_model.objects.all(),
                                many=True,
                                allow_null=True,
                            )
                        elif (
                            f.__class__.__name__ == "ForeignKey"
                            and f.name
                            in deep_get(
                                getattr(settings, app_label.upper(), {}),
                                "{}.labels".format(entity_str),
                                [],
                            )
                        ):
                            self.fields[f.name] = LabelSerializer(read_only=True)

                        elif f.__class__.__name__ == "ForeignKey":
                            self.fields[f.name] = serializers.HyperlinkedRelatedField(
                                view_name="apis:apis_api:{}-detail".format(
                                    f.related_model.__name__.lower()
                                ),
                                queryset=f.related_model.objects.all(),
                                allow_null=True
                            )

            return CustomSerializer

    return GenericAPIViewSet
