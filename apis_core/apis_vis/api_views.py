from rest_framework.generics import ListAPIView
from .serializers import VisAgeSerializer
from apis_core.apis_relations.models import PersonInstitution
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import  filters


class GetVisJson(ListAPIView):

    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    depth = 2
    filter_fields = ('related_institution__name', 'related_person__name', 'relation_type__name', 'related_person__collection__name', 'related_institution_id')
    search_fields = ('related_institution__name', 'related_person__name' )
    def get_serializer(self, instance=None, data=None, many=False, partial=False):
        vis = self.request.query_params.get('vis', None)
        if vis == 'average_age':
            return VisAgeSerializer(self.get_queryset(), many=False)
        else:
            return None

    def get_queryset(self):
        queryset = PersonInstitution.objects.all()
        start_date = self.request.query_params.get('end_date', None)
        end_date = self.request.query_params.get('start_date', None)
        if start_date is not None:
            queryset = queryset.filter(start_date__lt=start_date)
        if end_date is not None:
            queryset = queryset.filter(end_date__gt=end_date)
        return queryset
