from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.template.loader import select_template
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic.detail import DetailView
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django_tables2 import RequestConfig
from django.conf import settings

from entities.views import get_highlighted_texts
from .models import Work
from labels.models import Label
from metainfo.models import Uri
from relations.tables import get_generic_relations_table, EntityLabelTable, EntityDetailViewLabelTable


class GenericEntitiesDetailView(View):

    def get(self, request, *args, **kwargs):
        entity = kwargs['entity'].lower()
        pk = kwargs['pk']
        entity_model = ContentType.objects.get(app_label='entities', model=entity).model_class()
        instance = get_object_or_404(entity_model, pk=pk)
        relations = ContentType.objects.filter(app_label='relations', model__icontains=entity)
        side_bar = []
        for rel in relations:
            print(str(rel))
            match = str(rel).split()
            prefix = "{}{}-".format(match[0].title()[:2], match[1].title()[:2])
            table = get_generic_relations_table(''.join(match), entity, detail=True)
            title_panel = ''
            if match[0] == match[1]:
                title_panel = entity.title()
                dict_1 = {'related_' + entity.lower() + 'A': instance}
                dict_2 = {'related_' + entity.lower() + 'B': instance}
                if 'apis_highlighter' in settings.INSTALLED_APPS:
                    object_pre = rel.model_class().annotation_links.filter_ann_proj(request=request).filter(
                        Q(**dict_1) | Q(**dict_2))
                else:
                    object_pre = rel.model_class().objects.filter(
                        Q(**dict_1) | Q(**dict_2))
                objects = []
                for x in object_pre:
                    objects.append(x.get_table_dict(instance))
            else:
                if match[0].lower() == entity.lower():
                    title_panel = match[1].title()
                else:
                    title_panel = match[0].title()
                dict_1 = {'related_' + entity.lower(): instance}
                if 'apis_highlighter' in settings.INSTALLED_APPS:
                    objects = list(rel.model_class()
                                   .annotation_links.filter_ann_proj(request=request)
                                   .filter(**dict_1))
                else:
                    objects = list(rel.model_class().objects.filter(**dict_1))
            tb_object = table(objects, prefix=prefix)
            tb_object_open = request.GET.get(prefix + 'page', None)
            RequestConfig(request, paginate={"per_page": 10}).configure(tb_object)
            side_bar.append(
                (title_panel, tb_object, ''.join([x.title() for x in match]), tb_object_open)
            )
        object_lod = Uri.objects.filter(entity=instance)
        object_texts, ann_proj_form = get_highlighted_texts(request, instance)
        object_labels = Label.objects.filter(temp_entity=instance)
        tb_label = EntityDetailViewLabelTable(object_labels, prefix=entity.title()[:2]+'L-')
        tb_label_open = request.GET.get('PL-page', None)
        side_bar.append(('Label', tb_label, 'PersonLabel', tb_label_open))
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_label)
        template = select_template([
            'entities/detail_views/{}_detail_generic.html'.format(entity),
            'entities/detail_views/entity_detail_generic.html'
            ])
        return HttpResponse(template.render(
            request=request, context={
                'entity_type': entity,
                'object': instance,
                'right_panel': side_bar,
                'object_texts': object_texts,
                'object_lod': object_lod
                }
            ))


class WorkDetailView(DetailView):
    model = Work
    template_name = 'entities/detail_views/work_detail.html'

    def get_context_data(self, **kwargs):
        context = super(WorkDetailView, self).get_context_data(**kwargs)
        return context
