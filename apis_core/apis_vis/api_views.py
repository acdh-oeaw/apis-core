from django.contrib.contenttypes.models import ContentType
from rest_framework.generics import ListAPIView
from .serializers import *
from apis_core.apis_relations.models import PersonInstitution
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters


class GetVisJson(ListAPIView):

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
        relation_model = ContentType.objects.get(
            app_label='apis_relations', model=relation).model_class()
        print("from get_queryset {}".format(relation))
        queryset = relation_model.objects.all()
        return queryset
