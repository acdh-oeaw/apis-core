from rest_framework import serializers
from apis_core.apis_vocabularies.serializers import TextTypeSerializer
from .models import Collection, Text, Source, Uri, TempEntityClass


class CollectionSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name="apis:text-detail",
        lookup_field="pk"
    )

    parent_class = serializers.HyperlinkedIdentityField(
        view_name="apis:collection-detail",
        lookup_field="pk"
    )

    class Meta:
        fields = [
            'url',
            'name', 'description', 'collection_type',
            'parent_class'
        ]
        model = Collection


class TextSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="apis:text-detail",
        lookup_field="pk"
    )

    kind = serializers.HyperlinkedIdentityField(
        view_name="apis:texttype-detail",
        lookup_field="pk"
    )
    source = serializers.HyperlinkedIdentityField(
        view_name="apis:source-detail",
        lookup_field="pk"
    )

    class Meta:
        fields = [
            'kind', 'text', 'source', 'url'
        ]
        model = Text


class SourceSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="apis:source-detail",
        lookup_field="pk"
    )

    class Meta:
        fields = '__all__'
        model = Source


class UriSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="apis:uri-detail",
        lookup_field="pk"
    )
    entity = serializers.HyperlinkedIdentityField(
        view_name="apis:tempentityclass-detail",
        lookup_field="pk"
    )

    class Meta:
        fields = '__all__'
        model = Uri


class TempEntityClassSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="apis:tempentityclass-detail",
        lookup_field="pk"
    )
    collection = serializers.HyperlinkedIdentityField(
        view_name="apis:collection-detail",
        lookup_field="pk"
    )
    text = serializers.HyperlinkedIdentityField(
        view_name="apis:text-detail",
        lookup_field="pk"
    )
    source = serializers.HyperlinkedIdentityField(
        view_name="apis:source-detail",
        lookup_field="pk"
    )

    class Meta:
        fields = '__all__'
        model = TempEntityClass
