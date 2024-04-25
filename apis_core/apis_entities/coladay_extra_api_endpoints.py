from apis_core.apis_relations.models import PassagePublication
from rest_framework import mixins, viewsets
from rest_framework import filters
from apis_core.apis_entities.models import Passage
from .coladay_serializers import MinimalPassageSerializer
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db.models import Subquery, OuterRef
from django.db.models.functions import JSONObject


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
    queryset = Passage.objects.all().annotate(publication_json=Subquery(PassagePublication.objects.filter(related_passage_id=OuterRef('pk'), relation_type_id=189).values(json=JSONObject(name='related_publication__name', id="related_publication_id"))[:1]))
    filter_backends = [SelectSearchFilter,]
    serializer_class = MinimalPassageSerializer
