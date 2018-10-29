from django.conf import settings
from django.views.generic.detail import DetailView
from django.contrib.contenttypes.models import ContentType

from apis_core.apis_entities.views import GenericListViewNew
from . forms2 import GenericRelationForm
from . rel_forms import PersonPlaceFilterFormHelper


class GenericRelationView(GenericListViewNew):

    # formhelper_class = GenericRelationForm
    context_filter_name = 'filter'
    paginate_by = 25
    template_name = getattr(
        settings,
        'APIS_LIST_VIEW_TEMPLATE',
        'apis_entities/generic_list.html'
    )
    login_url = '/accounts/login/'

    def get_formhelper(self):
        return PersonPlaceFilterFormHelper


class GenericRelationDetailView(DetailView):

    template_name = getattr(
        settings,
        'APIS_RELATIONS_DETAIL_VIEW_TEMPLATE',
        'apis_relations/relations_detail_generic.html'
    )

    def get_object(self):
        entity = self.kwargs['entity'].lower()
        entity_model = ContentType.objects.get(
            app_label='apis_relations', model=entity).model_class()
        return entity_model

    def get_context_data(self, **kwargs):
        context = super(GenericRelationDetailView, self).get_context_data()
        context['entity'] = self.kwargs['entity'].lower()
        context['entity_type'] = context['entity']
        return context
