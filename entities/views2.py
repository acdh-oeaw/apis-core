from django.db.models import Q
from django.views import View
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render, redirect, get_object_or_404
from reversion.models import Version

from entities.views import get_highlighted_texts
from labels.models import Label
from metainfo.models import Uri
from .forms import get_entities_form, FullTextForm
from highlighter.forms import SelectAnnotatorAgreement

import re


class GenericEntitiesView(View):
    @staticmethod
    def set_session_variables(request):
        ann_proj_pk = request.GET.get('project', None)
        types = request.GET.getlist('types', None)
        users_show = request.GET.getlist('users_show', None)
        if types:
            request.session['entity_types_highlighter'] = types
        if users_show:
            request.session['users_show_highlighter'] = users_show
        if ann_proj_pk:
            request.session['annotation_project'] = ann_proj_pk
        return request

    def get(self, request, *args, **kwargs):
        entity = kwargs['entity']
        pk = kwargs['pk']
        entity_model = ContentType.objects.get(app_label='entities', model=entity).model_class()
        instance = get_object_or_404(entity_model, pk=pk)
        request = self.set_session_variables(request)
        relations = ContentType.objects.filter(app_label='relations', model__icontains=entity)
        side_bar = []
        for rel in relations:
            match = re.match(r'([A-Z][a-z]*)([A-Z][a-z]*)', str(rel))
            if match.group(1) == match.group(2):
                dict_1 = {'related_' + entity.lower() + 'A': instance}
                dict_2 = {'related_' + entity.lower() + 'B': instance}
                object_pre = rel.model_class().annotation_links.filter_ann_proj(request=request).filter(
                    Q(**dict_1) | Q(**dict_2))
                object = []
                for x in object_pre:
                    object.append(x.get_table_dict(instance))
                prefix = "{}{}-".format(match.group(1)[:2], match.group(2)[:2])
                tb_object = PersonPersonTable(object_person, prefix=prefix)
                tb_object_open = request.GET.get(prefix+'page', None)
                RequestConfig(request, paginate={"per_page": 10}).configure(tb_person)
        right_panel = [
            ('Uri', tb_uri, 'PersonResolveUri', tb_uri_open),
            ('Person', tb_person, 'PersonPerson', tb_person_open),
            ('Institution', tb_institution, 'PersonInstitution', tb_institution_open),
            ('Place', tb_place, 'PersonPlace', tb_place_open),
            ('Event', tb_event, 'PersonEvent', tb_event_open),
            ('Work', tb_work, 'PersonWork', tb_work_open),
            ('Label', tb_label, 'PersonLabel', tb_label_open)]
        form = get_entities_form(entity.title())
        form = form(instance=instance)
        form_text = FullTextForm(entity.title(), instance=instance)
        form_ann_agreement = SelectAnnotatorAgreement()
        object_revisions = Version.objects.get_for_object(instance)
        object_lod = Uri.objects.filter(entity=instance)
        object_texts, ann_proj_form = get_highlighted_texts(request, instance)
        object_labels = Label.objects.filter(temp_entity=instance)
        tb_label = EntityLabelTable(object_labels, prefix=entity.title()[:2]+'L-')
        tb_label_open = request.GET.get('PL-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_label)
        return render(request, 'entities/person_create_generic.html', {
            'entity_type': entity.title(),
            'form': form,
            'form_text': form_text,
            'instance': instance,
            'right_panel': right_panel,
            'object_revisions': object_revisions,
            'object_texts': object_texts,
            'object_lod': object_lod,
            'ann_proj_form': ann_proj_form,
            'form_ann_agreement': form_ann_agreement})

    #def post(self, request, *args, **kwargs):

