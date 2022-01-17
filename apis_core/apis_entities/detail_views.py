from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import select_template
from django.views import View
from django_tables2 import RequestConfig
from django.urls import reverse

from apis_core.apis_labels.models import Label
from apis_core.apis_metainfo.models import Uri
from apis_core.apis_relations.models import AbstractRelation
from apis_core.apis_relations.tables import get_generic_relations_table, LabelTableBase  # , EntityDetailViewLabelTable
from apis_core.helper_functions.utils import access_for_all
from .models import AbstractEntity
from .views import get_highlighted_texts


class GenericEntitiesDetailView(UserPassesTestMixin, View):

    #login_url = '/accounts/login/'

    def test_func(self):
        access = access_for_all(self, viewtype="detail")
        return access

    def get(self, request, *args, **kwargs):

        entity = kwargs['entity'].lower()
        pk = kwargs['pk']
        entity_model = AbstractEntity.get_entity_class_of_name(entity)
        instance = get_object_or_404(entity_model, pk=pk)
        relations = AbstractRelation.get_relation_classes_of_entity_name(entity_name=entity)
        side_bar = []
        for rel in relations:
            match = [
                rel.get_related_entity_classA().__name__.lower(),
                rel.get_related_entity_classB().__name__.lower()
            ]
            prefix = "{}{}-".format(match[0].title()[:2], match[1].title()[:2])
            table = get_generic_relations_table(relation_class=rel, entity_instance=instance, detail=True)
            if match[0] == match[1]:
                title_card = entity.title()
                dict_1 = {'related_' + entity.lower() + 'A': instance}
                dict_2 = {'related_' + entity.lower() + 'B': instance}
                if 'apis_highlighter' in settings.INSTALLED_APPS:
                    objects = rel.objects.filter_ann_proj(request=request).filter_for_user().filter(
                        Q(**dict_1) | Q(**dict_2))
                else:
                    objects = rel.objects.filter(
                        Q(**dict_1) | Q(**dict_2))
                    if callable(getattr(objects, 'filter_for_user', None)):
                        objects = objects.filter_for_user()
            else:
                if match[0].lower() == entity.lower():
                    title_card = match[1].title()
                else:
                    title_card = match[0].title()
                dict_1 = {'related_' + entity.lower(): instance}
                if 'apis_highlighter' in settings.INSTALLED_APPS:
                    objects = rel.objects.filter_ann_proj(request=request).filter_for_user().filter(**dict_1)
                else:
                    objects = rel.objects.filter(**dict_1)
                    if callable(getattr(objects, 'filter_for_user', None)):
                        objects = objects.filter_for_user()
            tb_object = table(data=objects, prefix=prefix)
            tb_object_open = request.GET.get(prefix + 'page', None)
            RequestConfig(request, paginate={"per_page": 10}).configure(tb_object)
            side_bar.append(
                (title_card, tb_object, ''.join([x.title() for x in match]), tb_object_open)
            )
        object_lod = Uri.objects.filter(entity=instance)
        object_texts, ann_proj_form = get_highlighted_texts(request, instance)
        object_labels = Label.objects.filter(temp_entity=instance)
        tb_label = LabelTableBase(data=object_labels, prefix=entity.title()[:2]+'L-')
        tb_label_open = request.GET.get('PL-page', None)
        side_bar.append(('Label', tb_label, 'PersonLabel', tb_label_open))
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_label)
        template = select_template([
            'apis_entities/detail_views/{}_detail_generic.html'.format(entity),
            'apis_entities/detail_views/entity_detail_generic.html'
            ])
        tei = getattr(settings, "APIS_TEI_TEXTS", [])
        if tei:
            tei = set(tei) & set([x.kind.name for x in instance.text.all()])
        ceteicean_css = getattr(settings, "APIS_CETEICEAN_CSS", None)
        ceteicean_js = getattr(settings, "APIS_CETEICEAN_JS", None)
        openseadragon_js = getattr(settings, "APIS_OSD_JS", None)
        openseadragon_img = getattr(settings, "APIS_OSD_IMG_PREFIX", None)
        iiif_field = getattr(settings, "APIS_IIIF_WORK_KIND", None)
        if iiif_field:
            try:
                if "{}".format(instance.kind) == "{}".format(iiif_field):
                    iiif = True
                else:
                    iiif = False
            except AttributeError:
                iiif = False
        else:
            iiif = False
        iiif_server = getattr(settings, "APIS_IIIF_SERVER", None)
        iiif_info_json = instance.name
        try:
            no_merge_labels = [
                x for x in object_labels if not x.label_type.name.startswith('Legacy')
            ]
        except AttributeError:
            no_merge_labels = []
        return HttpResponse(template.render(
            request=request, context={
                'entity_type': entity,
                'object': instance,
                'right_card': side_bar,
                'no_merge_labels': no_merge_labels,
                'object_lables': object_labels,
                'object_texts': object_texts,
                'object_lod': object_lod,
                'tei': tei,
                'ceteicean_css': ceteicean_css,
                'ceteicean_js': ceteicean_js,
                'iiif': iiif,
                'openseadragon_js': openseadragon_js,
                'openseadragon_img': openseadragon_img,
                'iiif_field': iiif_field,
                'iiif_info_json': iiif_info_json,
                'iiif_server': iiif_server,
                }
            ))


# TODO __sresch__ : This seems unused. Remove it once sure
# class WorkDetailView(DetailView):
#     model = Work
#     template_name = 'apis_entities/detail_views/work_detail.html'
#
#     def get_context_data(self, **kwargs):
#         context = super(WorkDetailView, self).get_context_data(**kwargs)
#         return context
