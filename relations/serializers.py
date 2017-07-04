from rest_framework import serializers
from .models import (InstitutionInstitution, PersonInstitution, PersonPlace, PersonPerson,
                     PersonEvent, PersonWork, InstitutionPlace, InstitutionEvent, InstitutionWork,
                     PlaceEvent, PlaceWork,PlacePlace, EventWork, EventEvent, WorkWork)


class InstitutionInstitutionSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = InstitutionInstitution


class PersonInstitutionSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PersonInstitution


class PersonPlaceSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
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
