from rest_framework import serializers
from .models import Annotation, Project, TextHigh, MenuEntry, VocabularyAPI
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from helper_functions.highlighter import highlight_text, highlight_textTEI

from vocabularies.serializers import UserAccSerializer


class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


class annotationSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for the Annotation model.
    """

    class Meta:
        model = Annotation
        fields = ('start', 'end', 'uri')


class texthighSerializer(serializers.HyperlinkedModelSerializer):
    #project = serializers.HyperlinkedRelatedField(many=False, view_name='api:project-detail', read_only=True)

    class Meta:
        model = TextHigh
        fields = ('text_id', 'text_class')


class vocabapiSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = VocabularyAPI
        fields = ('name', 'api_endpoint', 'method')


class menuentrySerializer(serializers.HyperlinkedModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(many=False, read_only=True)
    api = vocabapiSerializer(many=False, read_only=True)

    class Meta:
        model = MenuEntry
        fields = ('id', 'name', 'kind', 'api', 'parent')


class projectSerializer(serializers.HyperlinkedModelSerializer):
    texthigh_set = texthighSerializer(many=True, read_only=True)
    menuentry_set = menuentrySerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ('name', 'base_url', 'store_text', 'texthigh_set', 'menuentry_set')


class annotationSerializer(serializers.HyperlinkedModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(many=False, read_only=True)
    user_added = UserAccSerializer(many=False, read_only=True)

    class Meta:
        model = Annotation
        fields = ('start', 'end', 'text', 'user_added', 'parent')


class highlightText(serializers.BaseSerializer):
    func_offset = highlight_text

    def to_representation(self, obj):
        html_return = self.func_offset(
            obj,
            user=self.context['user_pk'],
            ann_proj=self.context['ann_proj_pk'],
            types=self.context['types'],
            users_show=self.context['users_show'])
        res = {
            'text_id': obj.pk,
            'text': html_return
        }
        return res

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', False)
        self.ann_proj = kwargs.pop('ann_proj', False)
        super().__init__(*args, **kwargs)

class highlightTextTEI(highlightText):
    func_offset = highlight_textTEI
