from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.generics import ListAPIView

from apis_core.apis_relations.models import AbstractRelation
from .serializers import *


class GetVisJson(ListAPIView):
    schema = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    depth = 2
    # TODO: add a generic filter thing

    def get_serializer(self, instance=None, data=None, many=False, partial=False):
        vis = self.request.query_params.get('vis', None)
        if vis == 'av-age':
            return VisAgeSerializer(self.get_queryset(), many=False)
        elif vis == 'avg-relations':
            return AvRelations(self.get_queryset(), many=False)
        else:
            return None

    def get_queryset(self, **kwargs):
        relation = self.kwargs['relation'].lower()
        relation_model = AbstractRelation.get_relation_class_of_name(relation)
        print("from get_queryset {}".format(relation))
        queryset = relation_model.objects.all()
        return queryset
