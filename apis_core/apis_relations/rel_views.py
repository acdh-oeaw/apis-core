from django.conf import settings
from django.views.generic.detail import DetailView
from django.contrib.contenttypes.models import ContentType

from django_tables2 import RequestConfig

from apis_core.apis_entities.views import GenericListViewNew
from . forms2 import GenericRelationForm
from . tables import get_generic_relation_listview_table
from . rel_filters import get_generic_relation_filter


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
        qs = ContentType.objects.get(
            app_label__startswith='apis_', model=self.entity.lower()
        ).model_class().objects.all()
        self.filter = get_generic_relation_filter(
            self.entity.title())(self.request.GET, queryset=qs)
        self.filter.form.helper = self.formhelper_class()
        return self.filter.qs.distinct()

    def get_table(self, **kwargs):
        relation = self.kwargs['entity'].lower()
        self.table_class = get_generic_relation_listview_table(relation)
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
        entity_model = ContentType.objects.get(
            app_label='apis_relations', model=entity).model_class()
        instance = entity_model.objects.get(pk=instance)
        return instance

    def get_context_data(self, **kwargs):
        context = super(GenericRelationDetailView, self).get_context_data()
        context['entity'] = self.kwargs['entity'].lower()
        context['entity_type'] = context['entity']
        return context
