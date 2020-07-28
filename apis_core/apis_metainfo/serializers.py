from rest_framework import serializers

from .models import Collection, Source, TempEntityClass, Text, Uri


class CollectionSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:text-detail", lookup_field="pk"
    )
    collection_type = serializers.HyperlinkedRelatedField(
        view_name="apis:apis_api:collectiontype-detail", lookup_field="pk", read_only=True
    )
    parent_class = serializers.HyperlinkedRelatedField(
        view_name="apis:apis_api:collection-detail", lookup_field="pk", read_only=True
    )

    class Meta:
        fields = ["url", "name", "description", "collection_type", "parent_class"]
        model = Collection


class TextSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:text-detail", lookup_field="pk"
    )

    kind = serializers.HyperlinkedRelatedField(
        view_name="apis:apis_api:texttype-detail", lookup_field="pk", read_only=True
    )
    source = serializers.HyperlinkedRelatedField(
        view_name="apis:apis_api:source-detail", lookup_field="pk", read_only=True
    )

    class Meta:
        fields = ["kind", "text", "source", "url"]
        model = Text


class SourceSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:source-detail", lookup_field="pk"
    )

    class Meta:
        fields = "__all__"
        model = Source


class UriSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:uri-detail", lookup_field="pk"
    )
    entity = serializers.HyperlinkedRelatedField(
        view_name="apis:apis_api:tempentityclass-detail",
        lookup_field="pk",
        read_only=True,
    )

    class Meta:
        fields = "__all__"
        model = Uri


class TempEntityClassSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:tempentityclass-detail", lookup_field="pk"
    )
    collection = serializers.HyperlinkedRelatedField(
        view_name="apis:apis_api:collection-detail", lookup_field="pk", read_only=True
    )
    text = serializers.HyperlinkedRelatedField(
        view_name="apis:apis_api:text-detail", lookup_field="pk", read_only=True
    )
    source = serializers.HyperlinkedRelatedField(
        view_name="apis:apis_api:source-detail", lookup_field="pk", read_only=True
    )

    class Meta:
        fields = "__all__"
        model = TempEntityClass
