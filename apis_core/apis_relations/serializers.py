from rest_framework import serializers
from .models import (InstitutionInstitution, PersonInstitution, PersonPlace, PersonPerson,
                     PersonEvent, PersonPassage, InstitutionPlace, InstitutionEvent, InstitutionPassage,
                     PlaceEvent, PlacePassage,PlacePlace, EventPassage, EventEvent, PassagePassage)


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


class PersonPassageSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PersonPassage


class InstitutionPlaceSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = InstitutionPlace


class InstitutionEventSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = InstitutionEvent


class InstitutionPassageSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = InstitutionPassage


class PlaceEventSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PlaceEvent


class PlacePassageSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PlacePassage


class PlacePlaceSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PlacePlace


class EventPassageSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = EventPassage


class EventEventSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = EventEvent


class PassagePassageSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PassagePassage
