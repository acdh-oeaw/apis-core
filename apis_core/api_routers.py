import inspect
from functools import reduce

import django.db.models.fields as df_fields
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, routers, serializers, viewsets
from rest_framework.permissions import AllowAny, DjangoObjectPermissions


def deep_get(dictionary, keys, default=None):
    return reduce(
        lambda d, key: d.get(key, default) if isinstance(d, dict) else default,
        keys.split("."),
        dictionary,
    )


class LabelSerializer(serializers.Serializer):
    id = serializers.IntegerField()
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
    class GenericAPIViewSet(viewsets.ModelViewSet):
        entity_str = kwargs.get("entity")
        app_label = kwargs.get("app_label")
        entity = ContentType.objects.get(
            app_label=app_label, model=entity_str.lower()
        ).model_class()
        model = entity
        queryset = entity.objects.all()
        permission_classes = (DjangoObjectPermissions,)
        filter_backends = (DjangoFilterBackend, filters.SearchFilter)
        depth = 2
        test_search = getattr(settings, app_label.upper(), False)
        if test_search:
            search_fields = deep_get(test_search, "search", [])
            filter_fields = deep_get(test_search, "list_filters", [])
            search_fields = deep_get(test_search, "{}.search".format(entity_str), search_fields)
            filter_fields = deep_get(test_search, "{}.list_filters".format(entity_str), filter_fields)
            if filter_fields is not None:
                filterset_fields = [x[0] for x in filter_fields]

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
                                read_only=True,
                                many=True,
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
                                read_only=True,
                            )

            return CustomSerializer

    return GenericAPIViewSet


router = routers.DefaultRouter()
