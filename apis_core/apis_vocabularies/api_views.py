from django.contrib.auth.models import User
from rest_framework import viewsets

from .models import (
    InstitutionInstitutionRelation, TextType, CollectionType, VocabsBaseClass,
    InstitutionType, ProfessionType, PlaceType, PersonInstitutionRelation, PersonPlaceRelation, PersonPersonRelation,
    VocabNames, InstitutionPlaceRelation, PersonEventRelation,
    PersonWorkRelation, InstitutionEventRelation, InstitutionWorkRelation, PlaceWorkRelation, PlaceEventRelation,
    PlacePlaceRelation, EventWorkRelation, EventEventRelation, WorkWorkRelation, EventType, WorkType)
from .serializers import (
    InstitutionInstitutionRelationSerializer, TextTypeSerializer,
    CollectionTypeSerializer, VocabsBaseClassSerializer,
    InstitutionTypeSerializer, ProfessionTypeSerializer, InstitutionPlaceRelationSerializer,
    PlaceTypeSerializer, PersonInstitutionRelationSerializer,
    PersonPlaceRelationSerializer, UserAccSerializer, VocabNamesSerializer,
    PersonPersonRelationSerializer, PersonEventRelationSerializer, PersonWorkRelationSerializer,
    InstitutionEventRelationSerializer, InstitutionWorkRelationSerializer, PlaceEventRelationSerializer,
    PlaceWorkRelationSerializer, PlacePlaceRelationSerializer, EventWorkRelationSerializer,
    EventEventRelationSerializer, WorkWorkRelationSerializer, EventTypeSerializer, WorkTypeSerializer)


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


class ProfessionTypeViewSet(viewsets.ModelViewSet):
    queryset = ProfessionType.objects.all()
    serializer_class = ProfessionTypeSerializer


class PlaceTypeViewSet(viewsets.ModelViewSet):
    queryset = PlaceType.objects.all()
    serializer_class = PlaceTypeSerializer


class EventTypeViewSet(viewsets.ModelViewSet):
    queryset = EventType.objects.all()
    serializer_class = EventTypeSerializer


class WorkTypeViewSet(viewsets.ModelViewSet):
    queryset = WorkType.objects.all()
    serializer_class = WorkTypeSerializer


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


class PersonWorkRelationViewSet(viewsets.ModelViewSet):
    queryset = PersonWorkRelation.objects.all()
    serializer_class = PersonWorkRelationSerializer


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


class InstitutionWorkRelationViewSet(viewsets.ModelViewSet):
    queryset = InstitutionWorkRelation.objects.all()
    serializer_class = InstitutionWorkRelationSerializer


class PlaceEventRelationViewSet(viewsets.ModelViewSet):
    queryset = PlaceEventRelation.objects.all()
    serializer_class = PlaceEventRelationSerializer


class PlaceWorkRelationViewSet(viewsets.ModelViewSet):
    queryset = PlaceWorkRelation.objects.all()
    serializer_class = PlaceWorkRelationSerializer


class PlacePlaceRelationViewSet(viewsets.ModelViewSet):
    queryset = PlacePlaceRelation.objects.all()
    serializer_class = PlacePlaceRelationSerializer


class EventWorkRelationViewSet(viewsets.ModelViewSet):
    queryset = EventWorkRelation.objects.all()
    serializer_class = EventWorkRelationSerializer


class EventEventRelationViewSet(viewsets.ModelViewSet):
    queryset = EventEventRelation.objects.all()
    serializer_class = EventEventRelationSerializer


class WorkWorkRelationViewSet(viewsets.ModelViewSet):
    queryset = WorkWorkRelation.objects.all()
    serializer_class = WorkWorkRelationSerializer



