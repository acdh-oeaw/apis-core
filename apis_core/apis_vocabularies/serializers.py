from rest_framework import serializers
from django.contrib.auth.models import User

from .models import (
    InstitutionInstitutionRelation, TextType, CollectionType, VocabsBaseClass,
    InstitutionType, ProfessionType, PlaceType, PersonInstitutionRelation, InstitutionPlaceRelation,
    PersonPlaceRelation, VocabNames, PersonPersonRelation, PersonEventRelation, PersonPassageRelation,
    InstitutionEventRelation, InstitutionPassageRelation, PlaceEventRelation, PlacePassageRelation, PlacePlaceRelation,
    EventPassageRelation, EventEventRelation, PassagePassageRelation, EventType, PassageType, LabelType)


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


class PassageTypeSerializer(VocabsBaseSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:passagetype-detail",
        lookup_field="pk"
    )

    class Meta:
        fields = '__all__'
        model = PassageType


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


class PersonPassageRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = PersonPassageRelation


class InstitutionPlaceRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = InstitutionPlaceRelation


class InstitutionEventRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = InstitutionEventRelation


class InstitutionPassageRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = InstitutionPassageRelation


class PlaceEventRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = PlaceEventRelation


class PlacePassageRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = PlacePassageRelation


class PlacePlaceRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = PlacePlaceRelation


class EventPassageRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = EventPassageRelation


class EventEventRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = EventEventRelation


class PassagePassageRelationSerializer(VocabsBaseSerializer):

    class Meta:
        fields = '__all__'
        model = PassagePassageRelation
