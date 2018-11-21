from rest_framework import serializers
from django.contrib.auth.models import User

from .models import (
    InstitutionInstitutionRelation, TextType, CollectionType, VocabsBaseClass,
    InstitutionType, ProfessionType, PlaceType, PersonInstitutionRelation, InstitutionPlaceRelation,
    PersonPlaceRelation, VocabNames, PersonPersonRelation, PersonEventRelation, PersonWorkRelation,
    InstitutionEventRelation, InstitutionWorkRelation, PlaceEventRelation, PlaceWorkRelation, PlacePlaceRelation,
    EventWorkRelation, EventEventRelation, WorkWorkRelation, EventType, WorkType, LabelType)


###########################################################
#
# Meta- Serializers
#
##########################################################


class UserAccSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['username', 'email']


class CollectionTypeSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = CollectionType


class VocabsBaseClassSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = VocabsBaseClass


class VocabNamesSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = VocabNames


############################################################
#
# Entity Types
#
###########################################################


class TextTypeSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = TextType


class InstitutionTypeSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = InstitutionType


class ProfessionTypeSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = ProfessionType


class PlaceTypeSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PlaceType


class EventTypeSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = EventType


class WorkTypeSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = WorkType


class LabelTypeSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'name')
        model = LabelType

#####################################################################
#
# Relations
#
####################################################################


class InstitutionInstitutionRelationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = InstitutionInstitutionRelation


class PersonPersonRelationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PersonPersonRelation


class PersonInstitutionRelationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PersonInstitutionRelation


class PersonPlaceRelationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PersonPlaceRelation


class PersonEventRelationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PersonEventRelation


class PersonWorkRelationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PersonWorkRelation


class InstitutionPlaceRelationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = InstitutionPlaceRelation


class InstitutionEventRelationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = InstitutionEventRelation


class InstitutionWorkRelationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = InstitutionWorkRelation


class PlaceEventRelationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PlaceEventRelation


class PlaceWorkRelationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PlaceWorkRelation


class PlacePlaceRelationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = PlacePlaceRelation


class EventWorkRelationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = EventWorkRelation


class EventEventRelationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = EventEventRelation


class WorkWorkRelationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = '__all__'
        model = WorkWorkRelation
