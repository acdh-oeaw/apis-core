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


class VocabsBaseSerializer(serializers.HyperlinkedModelSerializer):
    userAdded = serializers.HyperlinkedRelatedField(
        view_name="apis:apis_api:user-detail",
        lookup_field="pk",
        read_only=True
    )
    parent_class = serializers.HyperlinkedRelatedField(
        view_name="apis:apis_api:vocabsbaseclass-detail",
        lookup_field="pk",
        read_only=True
    )
    vocab_name = serializers.HyperlinkedRelatedField(
        view_name="apis:apis_api:vocabnames-detail",
        lookup_field="pk",
        read_only=True
    )


class CollectionTypeSerializer(VocabsBaseSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:collectiontype-detail",
        lookup_field="pk"
    )

    class Meta:
        fields = '__all__'
        model = CollectionType


class VocabsBaseClassSerializer(VocabsBaseSerializer): 
    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:vocabsbaseclass-detail",
        lookup_field="pk"
    )

    class Meta:
        fields = '__all__'
        model = VocabsBaseClass


class VocabNamesSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = VocabNames


############################################################
#
# Entity Types
#
###########################################################


class TextTypeSerializer(VocabsBaseSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:texttype-detail",
        lookup_field="pk"
    )
    collections = serializers.HyperlinkedRelatedField(
        view_name="apis:apis_api:collection-detail",
        lookup_field="pk",
        many=True,
        read_only=True
    )

    class Meta:
        fields = '__all__'
        model = TextType


class InstitutionTypeSerializer(VocabsBaseSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:institutiontype-detail",
        lookup_field="pk"
    )

    class Meta:
        fields = '__all__'
        model = InstitutionType


class ProfessionTypeSerializer(VocabsBaseSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:professiontype-detail",
        lookup_field="pk"
    )

    class Meta:
        fields = '__all__'
        model = ProfessionType


class PlaceTypeSerializer(VocabsBaseSerializer): 
    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:placetype-detail",
        lookup_field="pk"
    )

    class Meta:
        fields = '__all__'
        model = PlaceType


class EventTypeSerializer(VocabsBaseSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:eventtype-detail",
        lookup_field="pk"
    )

    class Meta:
        fields = '__all__'
        model = EventType


class WorkTypeSerializer(VocabsBaseSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:worktype-detail",
        lookup_field="pk"
    )

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


class InstitutionInstitutionRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = InstitutionInstitutionRelation


class PersonPersonRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = PersonPersonRelation


class PersonInstitutionRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = PersonInstitutionRelation


class PersonPlaceRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = PersonPlaceRelation


class PersonEventRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = PersonEventRelation


class PersonWorkRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = PersonWorkRelation


class InstitutionPlaceRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = InstitutionPlaceRelation


class InstitutionEventRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = InstitutionEventRelation


class InstitutionWorkRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = InstitutionWorkRelation


class PlaceEventRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = PlaceEventRelation


class PlaceWorkRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = PlaceWorkRelation


class PlacePlaceRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = PlacePlaceRelation


class EventWorkRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = EventWorkRelation


class EventEventRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = EventEventRelation


class WorkWorkRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = WorkWorkRelation
