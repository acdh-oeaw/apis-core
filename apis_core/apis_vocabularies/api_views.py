from django.contrib.auth.models import User
from rest_framework import viewsets

from .serializers import (
    InstitutionInstitutionRelationSerializer, TextTypeSerializer,
    CollectionTypeSerializer, VocabsBaseClassSerializer,
    InstitutionTypeSerializer, InstitutionPlaceRelationSerializer,
    PlaceTypeSerializer, PersonInstitutionRelationSerializer,
    PersonPlaceRelationSerializer, UserAccSerializer, VocabNamesSerializer,
    PersonPersonRelationSerializer, PersonEventRelationSerializer, PersonPassageRelationSerializer,
    InstitutionEventRelationSerializer, InstitutionPassageRelationSerializer, PlaceEventRelationSerializer,
    PlacePassageRelationSerializer, PlacePlaceRelationSerializer, EventPassageRelationSerializer,
    EventEventRelationSerializer, PassagePassageRelationSerializer, EventTypeSerializer, PassageTypeSerializer)
from .models import (
    InstitutionInstitutionRelation, TextType, CollectionType, VocabsBaseClass,
    InstitutionType, PlaceType, PersonInstitutionRelation, InstitutionPlaceRelation,
    PersonPlaceRelation, PersonPersonRelation, VocabNames, InstitutionPlaceRelation, PersonEventRelation,
    PersonPassageRelation, InstitutionEventRelation, InstitutionPassageRelation, PlacePassageRelation, PlaceEventRelation,
    PlacePlaceRelation, EventPassageRelation, EventEventRelation, PassagePassageRelation, EventType, PassageType)

# TODO __sresch__ : implement Publication related Viewsets

###########################################################
#
# Meta - ViewSets
#
##########################################################


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserAccSerializer


class VocabNamesViewSet(viewsets.ModelViewSet):
    queryset = VocabNames.objects.all()
    serializer_class = VocabNamesSerializer


class CollectionTypeViewSet(viewsets.ModelViewSet):
    queryset = CollectionType.objects.all()
    serializer_class = CollectionTypeSerializer


class VocabsBaseClassViewSet(viewsets.ModelViewSet):
    queryset = VocabsBaseClass.objects.all()
    serializer_class = VocabsBaseClassSerializer


########################################################
#
# Entity Types
#
#######################################################


class TextTypeViewSet(viewsets.ModelViewSet):
    queryset = TextType.objects.all()
    serializer_class = TextTypeSerializer


class InstitutionTypeViewSet(viewsets.ModelViewSet):
    queryset = InstitutionType.objects.all()
    serializer_class = InstitutionTypeSerializer


class PlaceTypeViewSet(viewsets.ModelViewSet):
    queryset = PlaceType.objects.all()
    serializer_class = PlaceTypeSerializer


class EventTypeViewSet(viewsets.ModelViewSet):
    queryset = EventType.objects.all()
    serializer_class = EventTypeSerializer


class PassageTypeViewSet(viewsets.ModelViewSet):
    queryset = PassageType.objects.all()
    serializer_class = PassageTypeSerializer


######################################################
#
# Relation Types
#
#####################################################


class PersonInstitutionRelationViewSet(viewsets.ModelViewSet):
    queryset = PersonInstitutionRelation.objects.all()
    serializer_class = PersonInstitutionRelationSerializer


class PersonPlaceRelationViewSet(viewsets.ModelViewSet):
    queryset = PersonPlaceRelation.objects.all()
    serializer_class = PersonPlaceRelationSerializer


class PersonEventRelationViewSet(viewsets.ModelViewSet):
    queryset = PersonEventRelation.objects.all()
    serializer_class = PersonEventRelationSerializer


class PersonPassageRelationViewSet(viewsets.ModelViewSet):
    queryset = PersonPassageRelation.objects.all()
    serializer_class = PersonPassageRelationSerializer


class PersonPersonRelationViewSet(viewsets.ModelViewSet):
    queryset = PersonPersonRelation.objects.all()
    serializer_class = PersonPersonRelationSerializer


class InstitutionInstitutionRelationViewSet(viewsets.ModelViewSet):
    queryset = InstitutionInstitutionRelation.objects.all()
    serializer_class = InstitutionInstitutionRelationSerializer


class InstitutionPlaceRelationViewSet(viewsets.ModelViewSet):
    queryset = InstitutionPlaceRelation.objects.all()
    serializer_class = InstitutionPlaceRelationSerializer


class InstitutionEventRelationViewSet(viewsets.ModelViewSet):
    queryset = InstitutionEventRelation.objects.all()
    serializer_class = InstitutionEventRelationSerializer


class InstitutionPassageRelationViewSet(viewsets.ModelViewSet):
    queryset = InstitutionPassageRelation.objects.all()
    serializer_class = InstitutionPassageRelationSerializer


class PlaceEventRelationViewSet(viewsets.ModelViewSet):
    queryset = PlaceEventRelation.objects.all()
    serializer_class = PlaceEventRelationSerializer


class PlacePassageRelationViewSet(viewsets.ModelViewSet):
    queryset = PlacePassageRelation.objects.all()
    serializer_class = PlacePassageRelationSerializer


class PlacePlaceRelationViewSet(viewsets.ModelViewSet):
    queryset = PlacePlaceRelation.objects.all()
    serializer_class = PlacePlaceRelationSerializer


class EventPassageRelationViewSet(viewsets.ModelViewSet):
    queryset = EventPassageRelation.objects.all()
    serializer_class = EventPassageRelationSerializer


class EventEventRelationViewSet(viewsets.ModelViewSet):
    queryset = EventEventRelation.objects.all()
    serializer_class = EventEventRelationSerializer


class PassagePassageRelationViewSet(viewsets.ModelViewSet):
    queryset = PassagePassageRelation.objects.all()
    serializer_class = PassagePassageRelationSerializer



