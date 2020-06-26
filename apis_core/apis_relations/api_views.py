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


