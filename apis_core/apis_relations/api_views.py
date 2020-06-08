from rest_framework import viewsets
from .serializers import (
    InstitutionInstitutionSerializer, PersonInstitutionSerializer,
    PersonPlaceSerializer, PersonPersonSerializer, PersonEventSerializer, PersonWorkSerializer,
    InstitutionPlaceSerializer, InstitutionEventSerializer, InstitutionWorkSerializer, PlaceEventSerializer,
    PlaceWorkSerializer, PlacePlaceSerializer, EventWorkSerializer, EventEventSerializer, WorkWorkSerializer)
from .models import (InstitutionInstitution, PersonInstitution, PersonPlace, PersonPerson, PersonEvent, PersonWork,
                     InstitutionPlace, InstitutionEvent, InstitutionWork, EventWork, EventEvent, PlaceEvent, PlaceWork,
                     PlacePlace, WorkWork)
from apis_core.apis_entities.api_views import StandardResultsSetPagination


