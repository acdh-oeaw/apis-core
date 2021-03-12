from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import select_template
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DeleteView
from django_tables2 import RequestConfig
from guardian.core import ObjectPermissionChecker
from reversion.models import Version
import importlib

from apis_core.apis_entities.models import AbstractEntity
from apis_core.apis_labels.models import Label
from apis_core.apis_metainfo.models import Uri
from apis_core.apis_relations.models import AbstractRelation
from apis_core.apis_relations.tables import get_generic_relations_table, LabelTableEdit
from .forms import get_entities_form, FullTextForm, GenericEntitiesStanbolForm
from .views import get_highlighted_texts
from .views import set_session_variables
from ..apis_vocabularies.models import TextType

if 'apis_highlighter' in settings.INSTALLED_APPS:
    from apis_highlighter.forms import SelectAnnotatorAgreement


@method_decorator(login_required, name='dispatch')
class GenericEntitiesEditView(View):

    def get(self, request, *args, **kwargs):
        entity = kwargs['entity']
        pk = kwargs['pk']
        entity_model = AbstractEntity.get_entity_class_of_name(entity)
        instance = get_object_or_404(entity_model, pk=pk)
        request = set_session_variables(request)
        relations = AbstractRelation.get_relation_classes_of_entity_name(entity_name=entity)
        side_bar = []
        for rel in relations:
            match = [
                rel.get_related_entity_classA().__name__.lower(),
                rel.get_related_entity_classB().__name__.lower()
            ]
            prefix = "{}{}-".format(match[0].title()[:2], match[1].title()[:2])
            table = get_generic_relations_table(relation_class=rel, entity_instance=instance, detail=False)
            title_card = ''
            if match[0] == match[1]:
                title_card = entity.title()
                dict_1 = {'related_' + entity.lower() + 'A': instance}
                dict_2 = {'related_' + entity.lower() + 'B': instance}
                if 'apis_highlighter' in settings.INSTALLED_APPS:
                    objects = rel.objects.filter_ann_proj(request=request).filter(
                        Q(**dict_1) | Q(**dict_2))
                else:
                    objects = rel.objects.filter(
                        Q(**dict_1) | Q(**dict_2))
            else:
                if match[0].lower() == entity.lower():
                    title_card = match[1].title()
                else:
                    title_card = match[0].title()
                dict_1 = {'related_' + entity.lower(): instance}
                if 'apis_highlighter' in settings.INSTALLED_APPS:
                    objects = rel.objects.filter_ann_proj(request=request).filter(**dict_1)
                else:
                    objects = rel.objects.filter(**dict_1)
            tb_object = table(data=objects, prefix=prefix)
            tb_object_open = request.GET.get(prefix + 'page', None)
            RequestConfig(request, paginate={"per_page": 10}).configure(tb_object)
            side_bar.append((title_card, tb_object, ''.join([x.title() for x in match]), tb_object_open))
        form = get_entities_form(entity.title())
        form = form(instance=instance)
        form_text = FullTextForm(entity=entity.title(), instance=instance)
        if 'apis_highlighter' in settings.INSTALLED_APPS:
            form_ann_agreement = SelectAnnotatorAgreement()
        else:
            form_ann_agreement = False
        if 'apis_bibsonomy' in settings.INSTALLED_APPS:
            apis_bibsonomy = getattr(settings, 'APIS_BIBSONOMY_FIELDS', ['self'])
            apis_bibsonomy_texts = getattr(settings, "APIS_BIBSONOMY_TEXTS", False)
            if apis_bibsonomy_texts:
                apis_bibsonomy.extend([f"text_{pk}" for pk in TextType.objects.filter(name__in=apis_bibsonomy_texts).values_list('pk', flat=True) if f"text_{pk}" not in apis_bibsonomy])
            if isinstance(apis_bibsonomy, list):
                apis_bibsonomy = '|'.join([x.strip() for x in apis_bibsonomy])
        else:
            apis_bibsonomy = False
        object_revisions = Version.objects.get_for_object(instance)
        object_lod = Uri.objects.filter(entity=instance)
        object_texts, ann_proj_form = get_highlighted_texts(request, instance)
        object_labels = Label.objects.filter(temp_entity=instance)
        tb_label = LabelTableEdit(data=object_labels, prefix=entity.title()[:2] + 'L-')
        tb_label_open = request.GET.get('PL-page', None)
        side_bar.append(('Label', tb_label, 'PersonLabel', tb_label_open))
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_label)
        perm = ObjectPermissionChecker(request.user)
        permissions = {'change': perm.has_perm('change_{}'.format(entity), instance),
                       'delete': perm.has_perm('delete_{}'.format(entity), instance),
                       'create': request.user.has_perm('entities.add_{}'.format(entity))}
        template = select_template(['apis_entities/{}_create_generic.html'.format(entity),
                                    'apis_entities/entity_create_generic.html'])
        context = {
            'entity_type': entity,
            'form': form,
            'form_text': form_text,
            'instance': instance,
            'right_card': side_bar,
            'object_revisions': object_revisions,
            'object_texts': object_texts,
            'object_lod': object_lod,
            'ann_proj_form': ann_proj_form,
            'form_ann_agreement': form_ann_agreement,
            'apis_bibsonomy': apis_bibsonomy,
            'permissions': permissions}
        form_merge_with = GenericEntitiesStanbolForm(entity, ent_merge_pk=pk)
        context['form_merge_with'] = form_merge_with
        return HttpResponse(template.render(request=request, context=context))

    def post(self, request, *args, **kwargs):
        entity = kwargs['entity']
        pk = kwargs['pk']
        entity_model = AbstractEntity.get_entity_class_of_name(entity)
        instance = get_object_or_404(entity_model, pk=pk)
        form = get_entities_form(entity.title())
        form = form(request.POST, instance=instance)
        form_text = FullTextForm(request.POST, entity=entity.title())
        if form.is_valid() and form_text.is_valid():
            entity_2 = form.save()
            form_text.save(entity_2)
            return redirect(reverse('apis:apis_entities:generic_entities_edit_view', kwargs={
                'pk': pk, 'entity': entity
            }))
        else:
            template = select_template(['apis_entities/{}_create_generic.html'.format(entity),
                                        'apis_entities/entity_create_generic.html'])
            perm = ObjectPermissionChecker(request.user)
            permissions = {'change': perm.has_perm('change_{}'.format(entity), instance),
                           'delete': perm.has_perm('delete_{}'.format(entity), instance),
                           'create': request.user.has_perm('entities.add_{}'.format(entity))}
            context = {
                'form': form,
                'entity_type': entity,
                'form_text': form_text,
                'instance': instance,
                'permissions': permissions}
            if entity.lower() != 'place':
                form_merge_with = GenericEntitiesStanbolForm(entity, ent_merge_pk=pk)
                context['form_merge_with'] = form_merge_with
                return TemplateResponse(request, template, context=context)
            return HttpResponse(template.render(request=request, context=context))


@method_decorator(login_required, name='dispatch')
class GenericEntitiesCreateView(View):
    def get(self, request, *args, **kwargs):
        entity = kwargs['entity']
        form = get_entities_form(entity.title())
        form = form()
        form_text = FullTextForm(entity=entity.title())
        permissions = {'create': request.user.has_perm('entities.add_{}'.format(entity))}
        template = select_template(['apis_entities/{}_create_generic.html'.format(entity),
                                    'apis_entities/entity_create_generic.html'])
        return HttpResponse(template.render(request=request, context={
            'entity_type': entity,
            'permissions': permissions,
            'form': form,
            'form_text': form_text}))

    def post(self, request, *args, **kwargs):
        entity = kwargs['entity']
        form = get_entities_form(entity.title())
        form = form(request.POST)
        form_text = FullTextForm(request.POST, entity=entity.title())
        if form.is_valid() and form_text.is_valid():
            entity_2 = form.save()
            form_text.save(entity_2)
            return redirect(reverse('apis:apis_entities:generic_entities_detail_view', kwargs={
                'pk': entity_2.pk, 'entity': entity
            }))
        else:
            permissions = {'create': request.user.has_perm('apis_entities.add_{}'.format(entity))}
            template = select_template(['apis_entities/{}_create_generic.html'.format(entity),
                                        'apis_entities/entity_create_generic.html'])
            return HttpResponse(template.render(request=request, context={
                'permissions': permissions,
                'form': form,
                'form_text': form_text}))


@method_decorator(login_required, name='dispatch')
class GenericEntitiesCreateStanbolView(View):

    def post(self, request, *args, **kwargs):
        entity = kwargs['entity']
        ent_merge_pk = kwargs.get('ent_merge_pk', False)
        if ent_merge_pk:
            form = GenericEntitiesStanbolForm(entity, request.POST, ent_merge_pk=ent_merge_pk)
        else:
            form = GenericEntitiesStanbolForm(entity, request.POST)
        #form = form(request.POST)
        if form.is_valid():
            entity_2 = form.save()
            if ent_merge_pk:
                entity_2.merge_with(int(ent_merge_pk))
            return redirect(reverse('apis:apis_entities:generic_entities_edit_view', kwargs={
                'pk': entity_2.pk, 'entity': entity
            }))
        else:
            permissions = {'create': request.user.has_perm('apis_entities.add_{}'.format(entity))}
            template = select_template(['apis_entities/{}_create_generic.html'.format(entity),
                                        'apis_entities/entity_create_generic.html'])
            return HttpResponse(template.render(request=request, context={
                'permissions': permissions,
                'form': form}))


@method_decorator(login_required, name='dispatch')
class GenericEntitiesDeleteView(DeleteView):
    model = importlib.import_module("apis_core.apis_metainfo.models").TempEntityClass
    template_name = getattr(
        settings, 'APIS_DELETE_VIEW_TEMPLATE', 'apis_entities/confirm_delete.html'
    )

    def dispatch(self, request, *args, **kwargs):
        entity = kwargs['entity']
        self.success_url = reverse(
            'apis_core:apis_entities:generic_entities_list', kwargs={'entity': entity}
        )
        return super(GenericEntitiesDeleteView, self).dispatch(request, *args, **kwargs)
