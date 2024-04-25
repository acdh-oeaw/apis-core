from rest_framework import serializers
from apis_core.apis_entities.models import Passage, Publication


class MinimalPassageSerializer(serializers.ModelSerializer):
    entity_type = serializers.SerializerMethodField(method_name="add_entity_type")
    publication = serializers.SerializerMethodField(method_name="add_publication")

    def add_entity_type(self, object):
        return "Passage"

    def add_publication(self, object):
        if object.publication_json:
            return object.publication_json
        return None   

    class Meta:
        model = Passage
        fields = ["id", "entity_type", "name", "start_date_written", "start_date", "end_date_written", "end_date", "primary_date", "publication"]