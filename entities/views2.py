from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import Context
from django.template.loader import select_template
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import DeleteView
from django_tables2 import RequestConfig
from guardian.core import ObjectPermissionChecker
from reversion.models import Version

from entities.views import get_highlighted_texts
from labels.models import Label
from metainfo.models import Uri
from relations.tables import get_generic_relations_table, EntityLabelTable
from .forms import get_entities_form, FullTextForm
from highlighter.forms import SelectAnnotatorAgreement


@method_decorator(login_required, name='dispatch')
class GenericEntitiesEditView(View):
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
            print(str(rel))
            match = str(rel).split()
            prefix = "{}{}-".format(match[0].title()[:2], match[1].title()[:2])
            table = get_generic_relations_table(''.join(match), entity)
            title_panel = ''
            if match[0] == match[1]:
                title_panel = entity.title()
                dict_1 = {'related_' + entity.lower() + 'A': instance}
                dict_2 = {'related_' + entity.lower() + 'B': instance}
                object_pre = rel.model_class().annotation_links.filter_ann_proj(request=request).filter(
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
                objects = list(rel.model_class().annotation_links.filter_ann_proj(request=request).filter(**dict_1))
            tb_object = table(objects, prefix=prefix)
            tb_object_open = request.GET.get(prefix + 'page', None)
            RequestConfig(request, paginate={"per_page": 10}).configure(tb_object)
            side_bar.append((title_panel, tb_object, ''.join([x.title() for x in match]), tb_object_open))
        form = get_entities_form(entity.title())
        form = form(instance=instance)
        form_text = FullTextForm(entity=entity.title(), instance=instance)
        form_ann_agreement = SelectAnnotatorAgreement()
        object_revisions = Version.objects.get_for_object(instance)
        object_lod = Uri.objects.filter(entity=instance)
        object_texts, ann_proj_form = get_highlighted_texts(request, instance)
        object_labels = Label.objects.filter(temp_entity=instance)
        tb_label = EntityLabelTable(object_labels, prefix=entity.title()[:2]+'L-')
        tb_label_open = request.GET.get('PL-page', None)
        side_bar.append(('Label', tb_label, 'PersonLabel', tb_label_open))
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_label)
        perm = ObjectPermissionChecker(request.user)
        permissions = {'change': perm.has_perm('change_{}'.format(entity), instance),
                       'delete': perm.has_perm('delete_{}'.format(entity), instance),
                       'create': request.user.has_perm('entities.add_{}'.format(entity))}
        template = select_template(['entities/{}_create_generic.html'.format(entity),
                                    'entities/entity_create_generic.html'])
        return HttpResponse(template.render(request=request, context={
            'entity_type': entity,
            'form': form,
            'form_text': form_text,
            'instance': instance,
            'right_panel': side_bar,
            'object_revisions': object_revisions,
            'object_texts': object_texts,
            'object_lod': object_lod,
            'ann_proj_form': ann_proj_form,
            'form_ann_agreement': form_ann_agreement,
            'permissions': permissions}))

    def post(self, request, *args, **kwargs):
        entity = kwargs['entity']
        pk = kwargs['pk']
        entity_model = ContentType.objects.get(app_label='entities', model=entity).model_class()
        instance = get_object_or_404(entity_model, pk=pk)
        form = get_entities_form(entity.title())
        form = form(request.POST, instance=instance)
        form_text = FullTextForm(request.POST, entity=entity.title())
        if form.is_valid() and form_text.is_valid():
            entity_2 = form.save()
            form_text.save(entity_2)
            return redirect(reverse('entities:generic_entities_edit_view', kwargs={
                'pk': pk, 'entity': entity
            }))
        else:
            template = select_template(['entities/{}_create_generic.html'.format(entity),
                                        'entities/entity_create_generic.html'])
            return HttpResponse(template.render(request=request, context={
                'form': form,
                'form_text': form_text,
                'instance': instance}))


@method_decorator(login_required, name='dispatch')
class GenericEntitiesCreateView(View):
    def get(self, request, *args, **kwargs):
        entity = kwargs['entity']
        form = get_entities_form(entity.title())
        form = form()
        form_text = FullTextForm(entity=entity.title())
        permissions = {'create': request.user.has_perm('entities.add_{}'.format(entity))}
        template = select_template(['entities/{}_create_generic.html'.format(entity),
                                    'entities/entity_create_generic.html'])
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
            return redirect(reverse('entities:generic_entities_edit_view', kwargs={
                'pk': entity_2.pk, 'entity': entity
            }))
        else:
            permissions = {'create': request.user.has_perm('entities.add_{}'.format(entity))}
            template = select_template(['entities/{}_create_generic.html'.format(entity),
                                        'entities/entity_create_generic.html'])
            return HttpResponse(template.render(request=request, context={
                'permissions': permissions,
                'form': form,
                'form_text': form_text}))


@method_decorator(login_required, name='dispatch')
class GenericEntitiesDeleteView(DeleteView):
    model = ContentType.objects.get(app_label='metainfo', model='tempentityclass').model_class()
    template_name = 'webpage/confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        entity = kwargs['entity']
        self.success_url = reverse('entities:generic_entities_list', kwargs={'entity': entity})
        return super(GenericEntitiesDeleteView, self).dispatch(request, *args, **kwargs)
