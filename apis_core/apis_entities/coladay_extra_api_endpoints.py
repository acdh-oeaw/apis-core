from apis_core.apis_metainfo.models import TempEntityClass
from apis_core.apis_relations.models import PassagePublication, PersonPublication
from rest_framework import mixins, viewsets
from rest_framework import filters
from django_filters import rest_framework as filters2
from apis_core.apis_entities.models import Passage
from apis_core.apis_vocabularies.models import PassageTopics
from .coladay_serializers import MinimalPassageSerializer, MinimalEntitySerializer
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db.models import Subquery, OuterRef
from django.db.models.functions import JSONObject
from django.db.models import Q
from django.db.models import Count
from django.db.models import JSONField
from django.db.models import Q, Subquery, OuterRef
from apis_core.apis_metainfo.models import TempEntityClass
from apis_core.apis_vocabularies.models import PassageTopics
from .coladay_serializers import MinimalEntitySerializer


search_fields = {
    "person": ["personpassage_set__related_person__name"],
    "place": ["placepassage_set__related_place__name", "placepassage_set__related_place__name_english",],
    "event": ["eventpassage_set__related_event__name", "eventpassage_set__related_event__name_english",],
    "publication": ["passagepublication_set__related_publication__name",],
    "institution": ["institutionpassage_set__related_institution__name", "institutionpassage_set__related_institution__name_english",],
    "text": ["text__text"],
    "topic": ["topic__name"],
    "type": ["kind__name"]
}

class SelectSearchFilter(filters.SearchFilter):
    def get_search_fields(self, view, request):
        qp = request.query_params.get("exclude", [])
        search_filters = []
        if isinstance(qp, str):
            qp = [qp,]
        for k, v in search_fields.items():
            if k not in qp:
                search_filters.extend(v)
        return search_filters

@extend_schema_view(
    list=extend_schema(
        description='Endpoint for searching related objects for Passages',
        parameters=[
          OpenApiParameter(
              name="exclude",
              type={'type': 'array',
              'items': {'type': 'string', 'enum': ["person", "place", "event", "publication", "institution", "text", "topic", "type"]}},
              location=OpenApiParameter.QUERY,
              description="Use to exclude certain related objects from the search",
              ),  # serializer object is converted to a parameter
        ]
        )
)
class ColadaySearchViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Passage.objects.all()
    filter_backends = [SelectSearchFilter,]
    serializer_class = MinimalPassageSerializer

search_fields_v2 = {
    "person": ["personpassage__related_person__name"],
    "place": ["placepassage__related_place__name", "placepassage__related_place__name_english",],
    "event": ["eventpassage__related_event__name", "eventpassage__related_event__name_english",],
    "publication": ["passagepublication__related_publication__name",],
    "institution": ["institutionpassage__related_institution__name", "institutionpassage__related_institution__name_english",],
    "text": ["text__text"],
    # "topic": ["topic__name"],
    # "type": ["kind__name"]
}

class SearchFilterV2(filters2.FilterSet):
    search = filters2.CharFilter(method="search_filter")
    name__icontains = filters2.CharFilter(field_name="name", lookup_expr="icontains")
    kind__id__in = filters2.CharFilter(method="id_in_filter", field_name="passage__kind__id")
    topic__id__in = filters2.CharFilter(method="id_in_filter", field_name="passage__topic__id")
    publication_set__id__in = filters2.CharFilter(method="id_in_filter", field_name="passage__publication_set")
    publication_set__person_set__id__in = filters2.CharFilter(method="author_filter")

    def search_filter(self, queryset, name, value):
        q_objects = Q() # Create an empty Q object to start with
        q_objects |= Q(**{"name__icontains": value})
        for filter in search_fields_v2.values():
            for f in filter:
                q_objects |= Q(**{f + "__icontains": value})
        q_objects |= Q(**{"id__in": Subquery(Passage.objects.filter(Q(topic__name__icontains=value)|Q(kind__name__icontains=value)).values("id"))})
        return queryset.filter(q_objects)
    
    def id_in_filter(self, queryset, name, value):
        filter = {name + "__in": [int(x) for x in value.split(",")]}
        return queryset.filter(**filter)

    def author_filter(self, queryset, name, value):
        author_query = PersonPublication.objects.filter(related_person_id__in=[int(x) for x in value.split(",")], relation_type_id=187).values_list('related_publication_id', flat=True)
        filter = {"passage__publication_set__in": list(author_query)}
        return queryset.filter(**filter)

class ColadayEntityListViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = TempEntityClass.objects_inheritance.select_subclasses("place", "person", "passage", "institution", "event", "publication").filter(
        Q(passage__isnull=False) | Q(person__isnull=False) | Q(place__isnull=False) | Q(institution__isnull=False) | Q(event__isnull=False) | Q(publication__isnull=False)
    )
    filter_backends = (filters2.DjangoFilterBackend,)
    serializer_class = MinimalEntitySerializer
    filterset_class = SearchFilterV2