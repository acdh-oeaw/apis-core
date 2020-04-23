from rest_framework import viewsets
from .serializers import (
    InstitutionInstitutionSerializer, PersonInstitutionSerializer,
    PersonPlaceSerializer, PersonPersonSerializer, PersonEventSerializer, PersonPassageSerializer,
    InstitutionPlaceSerializer, InstitutionEventSerializer, InstitutionPassageSerializer, PlaceEventSerializer,
    PlacePassageSerializer, PlacePlaceSerializer, EventPassageSerializer, EventEventSerializer, PassagePassageSerializer)
from .models import (InstitutionInstitution, PersonInstitution, PersonPlace, PersonPerson, PersonEvent, PersonPassage,
                     InstitutionPlace, InstitutionEvent, InstitutionPassage, EventPassage, EventEvent, PlaceEvent, PlacePassage,
                     PlacePlace, PassagePassage)
from apis_core.apis_entities.api_views import StandardResultsSetPagination

# TODO __sresch__ : implement Publication related Viewsets

class InstitutionInstitutionViewSet(viewsets.ModelViewSet):
    queryset = InstitutionInstitution.objects.all()
    serializer_class = InstitutionInstitutionSerializer
    depth = 2
    filter_fields = ('related_institutionA__name', 'related_institutionB__name')


class PersonInstitutionViewSet(viewsets.ModelViewSet):
    queryset = PersonInstitution.objects.all()
    serializer_class = PersonInstitutionSerializer
    depth = 2
    filter_fields = ('related_person__name', 'related_institution__name')


class PersonPlaceViewSet(viewsets.ModelViewSet):
    queryset = PersonPlace.objects.all()
    serializer_class = PersonPlaceSerializer
    depth = 2
    filter_fields = ('related_place__name', 'related_person__name')


class PersonPersonViewSet(viewsets.ModelViewSet):
    queryset = PersonPerson.objects.all()
    serializer_class = PersonPersonSerializer
    depth = 2
    filter_fields = ('related_personA__name', 'related_personB__name')


class PersonEventViewSet(viewsets.ModelViewSet):
    queryset = PersonEvent.objects.all()
    serializer_class = PersonEventSerializer
    depth = 2
    filter_fields = ('related_person__name', 'related_event__name')


class PersonPassageViewSet(viewsets.ModelViewSet):
    queryset = PersonPassage.objects.all()
    serializer_class = PersonPassageSerializer
    pagination_class = StandardResultsSetPagination
    depth = 2
    filter_fields = ('related_person__name', 'related_passage__name')


class InstitutionPlaceViewSet(viewsets.ModelViewSet):
    queryset = InstitutionPlace.objects.all()
    serializer_class = InstitutionPlaceSerializer
    depth = 2
    filter_fields = ('related_institution__name', 'related_place__name')


class InstitutionEventViewSet(viewsets.ModelViewSet):
    queryset = InstitutionEvent.objects.all()
    serializer_class = InstitutionEventSerializer
    depth = 2
    filter_fields = ('related_institution__name', 'related_event__name')


class InstitutionPassageViewSet(viewsets.ModelViewSet):
    queryset = InstitutionPassage.objects.all()
    serializer_class = InstitutionPassageSerializer
    pagination_class = StandardResultsSetPagination
    depth = 2
    filter_fields = ('related_institution__name', 'related_passage__name')


class EventPassageViewSet(viewsets.ModelViewSet):
    queryset = EventPassage.objects.all()
    serializer_class = EventPassageSerializer
    pagination_class = StandardResultsSetPagination
    depth = 2
    filter_fields = ('related_event__name', 'related_passage__name')


class EventEventViewSet(viewsets.ModelViewSet):
    queryset = EventEvent.objects.all()
    serializer_class = EventEventSerializer
    depth = 2
    filter_fields = ('related_eventA__name', 'related_eventB__name')


class PlaceEventViewSet(viewsets.ModelViewSet):
    queryset = PlaceEvent.objects.all()
    serializer_class = PlaceEventSerializer
    depth = 2
    filter_fields = ('related_place__name', 'related_event__name')


class PlacePassageViewSet(viewsets.ModelViewSet):
    queryset = PlacePassage.objects.all()
    serializer_class = PlacePassageSerializer
    pagination_class = StandardResultsSetPagination
    depth = 2
    filter_fields = ('related_place__name', 'related_passage__name')


class PlacePlaceViewSet(viewsets.ModelViewSet):
    queryset = PlacePlace.objects.all()
    serializer_class = PlacePlaceSerializer
    depth = 2
    filter_fields = ('related_placeA__name', 'related_placeB__name')


class PassagePassageViewSet(viewsets.ModelViewSet):
    queryset = PassagePassage.objects.all()
    serializer_class = PassagePassageSerializer
    pagination_class = StandardResultsSetPagination
    depth = 2
    filter_fields = ('related_passageA__name', 'related_passageB__name')
