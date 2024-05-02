from rest_framework import serializers
from apis_core.apis_entities.models import Passage, Publication

class MinimalPublicationSerialiser(serializers.ModelSerializer):

    class Meta:
        model = Publication
        fields = ["id", "name"]


class MinimalPassageSerializer(serializers.ModelSerializer):
    entity_type = serializers.SerializerMethodField(method_name="add_entity_type")
    publication = serializers.SerializerMethodField(method_name="add_publication")

    def add_entity_type(self, object):
        return "Passage"

    def add_publication(self, object):
        rel = object.passagepublication_set.filter(relation_type_id=189)
        if rel.count() == 1:
            return MinimalPublicationSerialiser(rel[0].related_publication).data
        return None   

    class Meta:
        model = Passage
        fields = ["id", "entity_type", "name", "start_date_written", "start_date", "end_date_written", "end_date", "primary_date", "publication"]


class MinimalEntitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.SerializerMethodField(method_name="add_entity_type")
    name = serializers.CharField()
    start_date_written = serializers.CharField(required=False)
    end_date_written = serializers.CharField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    primary_date = serializers.DateField(required=False)


    def add_entity_type(self, object):
        return object.__class__.__name__
