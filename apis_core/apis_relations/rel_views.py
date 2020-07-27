from django.conf import settings
from django.views.generic.detail import DetailView
from django_tables2 import RequestConfig

from apis_core.apis_entities.views import GenericListViewNew
from apis_core.apis_relations.models import AbstractRelation
from .rel_filters import get_generic_relation_filter
from .tables import get_generic_relation_listview_table


class GenericRelationView(GenericListViewNew):

    context_filter_name = 'filter'
    paginate_by = 25
    template_name = getattr(
        settings,
        'APIS_LIST_VIEW_TEMPLATE',
        'apis_entities/generic_list.html'
    )
    login_url = '/accounts/login/'

    def get_queryset(self, **kwargs):
        self.entity = self.kwargs.get('entity')
        qs = AbstractRelation.get_relation_class_of_name(self.entity).objects.all()
        self.filter = get_generic_relation_filter(
            self.entity.title())(self.request.GET, queryset=qs)
        self.filter.form.helper = self.formhelper_class()
        if callable(getattr(self.filter.qs, 'filter_for_user', None)):
            return self.filter.qs.filter_for_user().distinct()
        else:
            return self.filter.qs.distinct()


    def get_table(self, **kwargs):
        relation_name = self.kwargs['entity'].lower()
        self.table_class = get_generic_relation_listview_table(relation_name=relation_name)
        table = super(GenericListViewNew, self).get_table()
        RequestConfig(self.request, paginate={
            'page': 1, 'per_page': self.paginate_by}).configure(table)
        return table


class GenericRelationDetailView(DetailView):

    template_name = getattr(
        settings,
        'APIS_RELATIONS_DETAIL_VIEW_TEMPLATE',
        'apis_relations/relations_detail_generic.html'
    )

    def get_object(self):
        entity = self.kwargs['entity'].lower()
        instance = self.kwargs['pk'].lower()
        entity_model = AbstractRelation.get_relation_class_of_name(entity)
        instance = entity_model.objects.get(pk=instance)
        return instance

    def get_context_data(self, **kwargs):
        context = super(GenericRelationDetailView, self).get_context_data()
        context['entity'] = self.kwargs['entity'].lower()
        context['entity_type'] = context['entity']
        return context
