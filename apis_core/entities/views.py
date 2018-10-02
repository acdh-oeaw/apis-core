# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.views.generic.edit import DeleteView
from django.views import generic
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
#from reversion import revisions as reversion
from reversion.models import Version
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.db.models import Q
from django_tables2 import SingleTableView
from django_tables2 import RequestConfig
from reversion_compare.views import HistoryCompareDetailView
import reversion
from django_tables2.export.views import ExportMixin

from .models import Person, Place, Institution, Event, Work
from .forms import (FullTextForm, SearchForm, GenericFilterFormHelper,
                    NetworkVizFilterForm, PersonResolveUriForm,
                    get_entities_form, GenericEntitiesStanbolForm)
from relations.models import (PersonPerson, PersonInstitution, PersonEvent,
                              PersonPlace, InstitutionEvent, InstitutionPlace,
                              InstitutionInstitution, PlacePlace, PlaceEvent, PersonWork,
                              InstitutionWork, PlaceWork, EventWork)
from vocabularies.models import LabelType
from relations.tables import (PersonInstitutionTable, PersonPersonTable, PersonPlaceTable,
                              EntityLabelTable, InstitutionPlaceTable, InstitutionInstitutionTable,
                              PlacePlaceTable, PersonEventTable, PlaceEventTable,
                              InstitutionEventTable, PersonWorkTable, InstitutionWorkTable,
                              PlaceWorkTable, EventWorkTable, EntityUriTable)
from metainfo.models import Uri, UriCandidate, TempEntityClass, Text
from apis.settings.base import BASE_DIR
from helper_functions.stanbolQueries import retrieve_obj
from helper_functions.RDFparsers import GenericRDFParser
from labels.models import Label
from .tables import (
    PersonTable, PlaceTable, InstitutionTable, EventTable, WorkTable,
    get_entities_table
)
from .filters import (
    PersonListFilter, PlaceListFilter, InstitutionListFilter, EventListFilter, WorkListFilter,
    get_generic_list_filter
)
from relations.forms2 import GenericRelationForm


import json

if 'apis_highlighter' in settings.INSTALLED_APPS:
    from apis_highlighter.forms import SelectAnnotationProject, SelectAnnotatorAgreement
    from helper_functions.highlighter import highlight_text


############################################################################
############################################################################
#
#   Helper Functions
#
############################################################################
############################################################################

@login_required
def set_session_variables(request):
    ann_proj_pk = request.GET.get('project', None)
    types = request.GET.getlist('types', None)
    users_show = request.GET.getlist('users_show', None)
    edit_views = request.GET.get('edit_views', False)
    print('edit views: {}'.format(edit_views))
    if types:
        request.session['entity_types_highlighter'] = types
    if users_show:
        request.session['users_show_highlighter'] = users_show
    if ann_proj_pk:
        request.session['annotation_project'] = ann_proj_pk
    if edit_views:
        if edit_views != 'false':
            request.session['edit_views'] = True
    return request


@login_required
def get_highlighted_texts(request, instance):
    if 'apis_highlighter' in settings.INSTALLED_APPS:
        set_ann_proj = request.session.get('annotation_project', 1)
        entity_types_highlighter = request.session.get('entity_types_highlighter', None)
        users_show = request.session.get('users_show_highlighter', None)
        object_texts = [{'text': highlight_text(
            x,
            set_ann_proj=set_ann_proj,
            types=entity_types_highlighter,
            users_show=users_show).strip(),
                         'id': x.pk,
                         'kind': x.kind} for x in Text.objects.filter(tempentityclass=instance)]
        ann_proj_form = SelectAnnotationProject(
            set_ann_proj=set_ann_proj,
            entity_types_highlighter=entity_types_highlighter,
            users_show_highlighter=users_show)
        return object_texts, ann_proj_form
    else:
        object_texts = [{
            'text': x.text,
            'id': x.pk,
            'kind': x.kind
        } for x in Text.objects.filter(tempentityclass=instance)]
        return object_texts, False

############################################################################
############################################################################
#
#   GenericViews
#
############################################################################
############################################################################


@method_decorator(login_required, name='dispatch')
class GenericListView(SingleTableView):
    filter_class = None
    formhelper_class = None
    context_filter_name = 'filter'
    paginate_by = 25

    def get_queryset(self, **kwargs):
        qs = super(GenericListView, self).get_queryset()
        self.filter = self.filter_class(self.request.GET, queryset=qs)
        self.filter.form.helper = self.formhelper_class()
        return self.filter.qs

    def get_table(self, **kwargs):
        table = super(GenericListView, self).get_table()
        RequestConfig(self.request, paginate={
            'page': 1, 'per_page': self.paginate_by}).configure(table)
        return table

    def get_context_data(self, **kwargs):
        context = super(GenericListView, self).get_context_data()
        context[self.context_filter_name] = self.filter
        return context

    def __init__(self, *args, **kwargs):
        super(GenericListView, self).__init__(*args, **kwargs)
        print('Kwargs: {}'.format(self.request))


@method_decorator(login_required, name='dispatch')
class GenericListViewNew(ExportMixin, SingleTableView):
    formhelper_class = GenericFilterFormHelper
    context_filter_name = 'filter'
    paginate_by = 25
    template_name = 'entities/generic_list.html'

    def get_queryset(self, **kwargs):
        self.entity = self.kwargs.get('entity')
        qs = ContentType.objects.get(app_label='entities', model=self.entity.lower()).model_class().objects.all()
        self.filter = get_generic_list_filter(self.entity.title())(self.request.GET, queryset=qs)
        self.filter.form.helper = self.formhelper_class()
        return self.filter.qs

    def get_table(self, **kwargs):
        self.request = set_session_variables(self.request)
        edit_v = self.request.session.get('edit_views', False)
        self.table_class = get_entities_table(self.entity.title(), edit_v)
        table = super(GenericListViewNew, self).get_table()
        RequestConfig(self.request, paginate={
            'page': 1, 'per_page': self.paginate_by}).configure(table)
        return table

    def get_context_data(self, **kwargs):
        context = super(GenericListViewNew, self).get_context_data()
        context[self.context_filter_name] = self.filter
        context['entity'] = self.entity
        context['entity_create_stanbol'] = GenericEntitiesStanbolForm(self.entity)
        return context



############################################################################
############################################################################
#
#   OtherViews
#
############################################################################
############################################################################

@login_required
def getGeoJson(request):
    '''Used to retrieve GeoJsons for single objects'''
    #if request.is_ajax():
    pk_obj = request.GET.get("object_id")
    instance = get_object_or_404(Place, pk=pk_obj)
    uria = Uri.objects.filter(entity=instance)
    urib = UriCandidate.objects.filter(entity=instance)
    if urib.count() > 0:
        uric = urib
    elif uria.count() > 0:
        uric = uria
        add_info = ""
    lst_json = []
    if uric.count() > 0 and not instance.status.startswith('distinct'):
        for x in uric:
            o = retrieve_obj(x.uri)
            if o:
                url_r = reverse_lazy('entities:resolve_ambigue_place', kwargs={'pk': str(instance.pk), 'uri': o['representation']['id'][7:]})
                select_text = "<a href='{}'>Select this URI</a>".format(url_r)
                try:
                    add_info = "<b>Confidence:</b> {}<br/><b>Feature:</b> <a href='{}'>{}</a>".format(x.confidence, x.uri, x.uri)
                except:
                    add_info = "<b>Confidence:</b>no value provided <br/><b>Feature:</b> <a href='{}'>{}</a>".format(x.uri, x.uri)
                r = {"geometry": {
                        "type": "Point",
                        "coordinates": [
                            float(
                                o['representation']
                                ['http://www.w3.org/2003/01/geo/wgs84_pos#long'][0]['value']),
                            float(
                                o['representation']
                                ['http://www.w3.org/2003/01/geo/wgs84_pos#lat'][0]['value'])
                        ]
                        },
                    "type": "Feature",
                    "properties": {
                        "popupContent": "<b>ÖBL name:</b> %s<br/><b>Geonames:</b> %s<br/>%s<br/>%s" % (instance.name, o['representation']['http://www.geonames.org/ontology#name'][0]['value'], select_text, add_info)
                    },
                    "id": x.pk
                    }
                lst_json.append(r)
    elif instance.lat is not None and instance.lng is not None:
        r = {"geometry": {
            "type": "Point",
            "coordinates": [
                instance.lng,
                instance.lat
            ]
        },
            "type": "Feature",
            "properties": {
                "popupContent": "<b>Name:</b> %s<br/>" % (instance.name)
            },
            "id": instance.pk
        }
        lst_json.append(r)

    return HttpResponse(json.dumps(lst_json), content_type='application/json')


@login_required
def getGeoJsonList(request):
    '''Used to retrieve a list of GeoJsons. To generate the list the kind of connection
    and the connected entity is needed'''
    relation = ContentType.objects.get(app_label='relations', model=request.GET.get("relation")).model_class()
    #relation_type = request.GET.get("relation_type")
    objects = relation.objects.filter(
            related_place__status='distinct').select_related('related_person', 'related_place', 'relation_type')
    lst_json = []
    for x in objects:
        pers_url = reverse_lazy('entities:generic_entities_edit_view', kwargs={'pk': str(x.related_person.pk),
                                                                               'entity': 'person'})
        place_url = reverse_lazy('entities:generic_entities_edit_view', kwargs={'pk': str(x.related_place.pk),
                                                                                'entity': 'place'})
        r = {"geometry": {
                        "type": "Point",
                        "coordinates": [x.related_place.lng, x.related_place.lat]
                        },
                    "type": "Feature",
                    "relation_type": x.relation_type.name,
                    "properties": {
                        "popupContent": "<b>Person:</b> <a href='%s'>%s</a><br/><b>Connection:</b> %s<br/><b>Place:</b> <a href='%s'>%s</a>" % (pers_url, x.related_person, x.relation_type, place_url, x.related_place)
                    },
                    "id": x.pk
                    }
        lst_json.append(r)
    return HttpResponse(json.dumps(lst_json), content_type='application/json')


@login_required
def getNetJsonList(request):
    '''Used to retrieve a Json to draw a network'''
    relation = ContentType.objects.get(app_label='relations', model='PersonPlace').model_class()
    objects = relation.objects.filter(
            related_place__status='distinct')
    nodes = dict()
    edges = []

    for x in objects:
        if x.related_place.pk not in nodes.keys():
            place_url = reverse_lazy('entities:place_edit', kwargs={'pk': str(x.related_place.pk)})
            tt = "<div class='arrow'></div>\
            <div class='sigma-tooltip-header'>%s</div>\
            <div class='sigma-tooltip-body'>\
            <table>\
                <tr><th>Type</th> <td>%s</td></tr>\
                <tr><th>Entity</th> <td><a href='%s'>Link</a></td></tr>\
            </table>\
            </div>"% (x.related_place.name, 'place', place_url)
            nodes[x.related_place.pk] = {'type': 'place', 'label': x.related_place.name, 'id': str(x.related_place.pk), 'tooltip': tt}
        if x.related_person.pk not in nodes.keys():
            pers_url = reverse_lazy('entities:person_edit', kwargs={'pk': str(x.related_person.pk)})
            tt = "<div class='arrow'></div>\
            <div class='sigma-tooltip-header'>%s</div>\
            <div class='sigma-tooltip-body'>\
            <table>\
                <tr><th>Type</th> <td>%s</td></tr>\
                <tr><th>Entity</th> <td><a href='%s'>Link</a></td></tr>\
            </table>\
            </div>"% (str(x.related_person), 'person', pers_url)
            nodes[x.related_person.pk] = {'type': 'person', 'label': str(x.related_person), 'id': str(x.related_person.pk), 'tooltip': tt}
        edges.append({'source': x.related_person.pk, 'target': x.related_place.pk, 'kind': x.relation_type.name, 'id': str(x.pk)})
    lst_json = {'edges': edges, 'nodes': [nodes[x] for x in nodes.keys()]}

    return HttpResponse(json.dumps(lst_json), content_type='application/json')


@login_required
def getNetJsonListInstitution(request):
    '''Used to retrieve a Json to draw a network'''
    relation = ContentType.objects.get(app_label='relations', model='PersonInstitution').model_class()
    objects = relation.objects.all()
    nodes = dict()
    edges = []

    for x in objects:
        if x.related_institution.pk not in nodes.keys():
            inst_url = reverse_lazy('entities:institution_edit', kwargs={'pk': str(x.related_institution.pk)})
            tt = "<div class='arrow'></div>\
            <div class='sigma-tooltip-header'>%s</div>\
            <div class='sigma-tooltip-body'>\
            <table>\
                <tr><th>Type</th> <td>%s</td></tr>\
                <tr><th>Entity</th> <td><a href='%s'>Link</a></td></tr>\
            </table>\
            </div>"% (x.related_institution.name, 'institution', inst_url)
            nodes[x.related_institution.pk] = {'type': 'institution', 'label': x.related_institution.name, 'id': str(x.related_institution.pk), 'tooltip': tt}
        if x.related_person.pk not in nodes.keys():
            pers_url = reverse_lazy('entities:person_edit', kwargs={'pk': str(x.related_person.pk)})
            tt = "<div class='arrow'></div>\
            <div class='sigma-tooltip-header'>%s</div>\
            <div class='sigma-tooltip-body'>\
            <table>\
                <tr><th>Type</th> <td>%s</td></tr>\
                <tr><th>Entity</th> <td><a href='%s'>Link</a></td></tr>\
            </table>\
            </div>"% (str(x.related_person), 'person', pers_url)
            nodes[x.related_person.pk] = {'type': 'person', 'label': str(x.related_person), 'id': str(x.related_person.pk), 'tooltip': tt}
        edges.append({'source': x.related_person.pk, 'target': x.related_institution.pk, 'kind': x.relation_type.name, 'id': str(x.pk)})
    lst_json = {'edges': edges, 'nodes': [nodes[x] for x in nodes.keys()]}

    return HttpResponse(json.dumps(lst_json), content_type='application/json')


@login_required
def resolve_ambigue_place(request, pk, uri):
    '''Only used to resolve place names.'''
    with reversion.create_revision():
        uri = 'http://'+uri
        entity = Place.objects.get(pk=pk)
        pl_n = GenericRDFParser(uri, kind='Place')
        pl_n_1 = pl_n.save()
        pl_n_1 = pl_n.merge(entity)
        url = reverse_lazy(
            'entities:generic_entities_edit_view',
            kwargs={
                'entity': 'place',
                'pk': str(pl_n_1.pk),
            }
        )
        if pl_n.created:
            pl_n_1.status = 'distinct (manually resolved)'
            pl_n_1.save()
        UriCandidate.objects.filter(entity=entity).delete()
        reversion.set_user(request.user)

    return HttpResponseRedirect(url)


@login_required
def resolve_ambigue_person(request):
    if request.method == "POST":
        form = PersonResolveUriForm(request.POST)
    if form.is_valid():
        pers = form.save()
        return redirect(reverse('entities:person_edit', kwargs={'pk': pers.pk}))
    else:
        print(form)


############################################################################
############################################################################
#
#   VisualizationViews
#
############################################################################
############################################################################

@login_required
def birth_death_map(request):
    return render(request, 'entities/map_list.html')


@login_required
def pers_place_netw(request):
    return render(request, 'entities/network.html')


@login_required
def pers_inst_netw(request):
    return render(request, 'entities/network_institution.html')


@login_required
def generic_network_viz(request):
    if request.method == 'GET':
        form = NetworkVizFilterForm()
        return render(request, 'entities/generic_network_visualization.html',
                      {'form': form})


############################################################################
############################################################################
#
#  Reversion Views
#
############################################################################
############################################################################

class ReversionCompareView(HistoryCompareDetailView):
    template_name = 'entities/compare_base.html'

    def dispatch(self, request, app, kind, pk, *args, **kwargs):
        self.model = ContentType.objects.get(app_label=app, model=kind).model_class()
        return super(ReversionCompareView, self).dispatch(request, *args, **kwargs)
