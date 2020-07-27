from rest_framework import serializers

from apis_core.apis_entities.serializers import (
    PersonSerializer,
    PlaceSerializer
)
from apis_core.apis_vocabularies.serializers import (
    PersonPlaceRelationSerializer,
)
from .models import (InstitutionInstitution, PersonInstitution, PersonPlace, PersonPerson,
                     PersonEvent, PersonWork, InstitutionPlace, InstitutionEvent, InstitutionWork,
                     PlaceEvent, PlaceWork, PlacePlace, EventWork, EventEvent, WorkWork)


class InstitutionInstitutionSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = InstitutionInstitution


class PersonInstitutionSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PersonInstitution


class PersonPlaceSerializer(serializers.HyperlinkedModelSerializer):

    # url = serializers.HyperlinkedIdentityField(
    #     view_name="apis:apis_api:personplace-detail",
    #     lookup_field="pk"
    # )
    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:personplace-detail",
        lookup_field="pk"
    )
    related_person = PersonSerializer()
    related_place = PlaceSerializer()
    relation_type = PersonPlaceRelationSerializer()
    # related_place__name = serializers.CharField()

    class Meta:
        fields = [
            'url',
            'id',
            'related_person',
            'related_place',
            'start_date',
            'start_date_written',
            'end_date',
            'end_date_written',
            'relation_type',
        ]
        model = PersonPlace


class PersonPersonSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PersonPerson


class PersonEventSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PersonEvent


class PersonWorkSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PersonWork


class InstitutionPlaceSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:institutionplace-detail",
        lookup_field="pk"
    )

    class Meta:
        fields = '__all__'
        model = InstitutionPlace


class InstitutionEventSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = InstitutionEvent


class InstitutionWorkSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = InstitutionWork


class PlaceEventSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PlaceEvent


class PlaceWorkSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PlaceWork


class PlacePlaceSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PlacePlace


class EventWorkSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = EventWork


class EventEventSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = EventEvent


class WorkWorkSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = WorkWork
