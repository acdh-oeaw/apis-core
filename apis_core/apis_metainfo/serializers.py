from rest_framework import serializers
from apis_core.apis_vocabularies.serializers import TextTypeSerializer
from .models import Collection, Text, Source, Uri, TempEntityClass


class CollectionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        #fields = '__all__'
        exclude = ('groups_allowed', )
        model = Collection


class TextSerializer(serializers.HyperlinkedModelSerializer):
    #kind = TextTypeSerializer()

    class Meta:
        fields = '__all__'
        model = Text


class SourceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        fields = '__all__'
        model = Source


class UriSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        fields = '__all__'
        model = Uri


class TempEntityClassSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        fields = '__all__'
        model = TempEntityClass
