from rest_framework import serializers

from apis_core.apis_vocabularies.serializers import LabelTypeSerializer
from .models import Label


class LabelSerializerLegacy(serializers.ModelSerializer):
    label_type = LabelTypeSerializer()

    class Meta:
        model = Label
        fields = ('id', 'label', 'isoCode_639_3', 'label_type')
