from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, filters, mixins
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from django.contrib.contenttypes.models import ContentType
import pickle
from django.conf import settings

from .models import Project, TextHigh, MenuEntry, VocabularyAPI, Annotation
from .serializer import (
    projectSerializer, texthighSerializer,
    menuentrySerializer, highlightText, vocabapiSerializer, annotationSerializer,
    highlightTextTEI
)
from metainfo.models import Text
from metainfo.api_renderers import TEIBaseRenderer
from helper_functions.inter_annotator_agreement import InternalDataAgreement

if 'deep learning' in getattr(settings, "APIS_COMPONENTS", []):
    from helper_functions.dl_models import test_model




class HighlighterProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint that returns the menus for the different texts
    """
    #allowed_methods = ['GET']
    serializer_class = projectSerializer
    queryset = Project.objects.all()

    # def get_queryset(self):
    #     pk = self.request.query_params.get('q_pk', None)
    #     if pk:
    #         return self.queryset.filter(pk=pk)
    #     else:
    #         return self.queryset


class HighlighterTextHighViewSet(viewsets.ModelViewSet):

    serializer_class = texthighSerializer
    queryset = TextHigh.objects.all()


class HighlighterMenuEntryViewSet(viewsets.ModelViewSet):

    allowed_methods = ['GET']
    serializer_class = menuentrySerializer
    queryset = MenuEntry.objects.all()


class HighlighterAnnotationViewSet(viewsets.ModelViewSet):

    serializer_class = annotationSerializer
    queryset = Annotation.objects.all()


class HighlighterVocabularyAPIViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = vocabapiSerializer
    queryset = VocabularyAPI.objects.all()


class HighlighterHighlightTextViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):

    renderer_classes = (JSONRenderer, TEIBaseRenderer) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def get_queryset(self):
        queryset = Text.objects.all()
        pk = self.request.query_params.get('q_pk', None)
        self.user_pk = self.request.query_params.get('user', None)
        self.ann_proj_pk = self.request.query_params.get('ann_proj', None)
        self.types = self.request.query_params.get('types', None)
        self.users_show = self.request.query_params.get('users_show', None)
        if self.types:
            self.request.session['entity_types_highlighter'] = self.types.split(',')
        else:
            self.request.session['entity_types_highlighter'] = []
        if self.users_show:
            self.request.session['users_show_highlighter'] = self.users_show.split(',')
            self.users_show = self.users_show.split(',')
        else:
            self.request.session['users_show_highlighter'] = []
        self.request.session['annotation_project'] = self.ann_proj_pk
        if pk:
            return queryset.filter(pk__in=pk.split(','))
        else:
            return queryset

    def get_serializer_class(self):
        if self.request.accepted_renderer.media_type == 'application/json':
            return highlightText
        elif self.request.accepted_renderer.media_type == 'application/xml+tei':
            return highlightTextTEI
        else:
            return highlightText

    def get_serializer_context(self):
        return {'user_pk': self.user_pk,
                'ann_proj_pk': self.ann_proj_pk,
                'types': self.types,
                'users_show': self.users_show}


class AnnotatorAgreementView(APIView):

    def get(self, request, format=None):
        metrics = request.query_params.get('metrics', 'Do_alpha')
        user_group = request.query_params.get('user_group', None)
        gold_standard = request.query_params.get('gold_standard', None)
        kind_instance = request.query_params.get('kind_instance')
        instance = request.query_params.get('instance', None)
        collection = request.query_params.get('collection', None)
        ann_proj_pk = self.request.session['annotation_project']
        if instance:
            entity = ContentType.objects.get(app_label='entities',
                                             model=kind_instance).get_object_for_this_type(pk=instance)
            data = InternalDataAgreement(entity, ann_proj_pk,
                                         metrics=metrics, user_group=user_group, gold_standard=gold_standard)
        elif collection:
            entity = ContentType.objects.get(app_label='entities',
                                             model=kind_instance).model_class()
            txts = Text.objects.filter(tempentityclass__in=entity.filter(collection_id=collection))
            data = InternalDataAgreement(txts, ann_proj_pk,
                                            metrics=metrics, user_group=user_group, gold_standard=gold_standard)

        return Response({'data': data.get_html_table()})


class ShowOverlappingHighlights(APIView):

    def get(self, request, format=None):
        text_id = request.query_params.get('text_id')
        char_start = request.query_params.get('char_start')
        char_end = request.query_params.get('char_end')
        left_offset = int(request.query_params.get('left_offset', 5))
        right_offset = int(request.query_params.get('right_offset', 5))
        res = '<ul class="annotations_list">'
        txt = Text.objects.get(pk=text_id)
        for ann in Annotation.objects.filter(start__gte=char_start, end__lte=char_end, text_id=text_id):
            left_list = txt.text[:ann.start].split()
            if len(left_list) < left_offset:
                left_offset = len(left_list) - 1
            left_offset_text = ' '.join(left_list[-left_offset:])
            right_list = txt.text[ann.end:].split()
            if len(right_list) < right_offset:
                right_offset = len(right_list) - 1
            right_offset_text = ' '.join(right_list[:right_offset])
            res += '<li>{} {}{}</mark> {}</li>'.format(
                left_offset_text, ann.get_html_markup(), txt.text[ann.start:ann.end], right_offset_text)
        res += '</ul>'
        return Response({'data': res})


class TestDLModel(APIView):

    def get(self, request, format=None):
        model = request.query_params.get('model')
        text = request.query_params.get('text')

        res = test_model(model, text)
        print(res)
        return Response({'data': res})
