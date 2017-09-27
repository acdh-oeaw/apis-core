# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.views.generic.edit import DeleteView
from django.views import generic
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

from .models import Person, Place, Institution, Event, Work
from .forms import (PersonForm, PlaceForm, InstitutionForm, EventForm, FullTextForm, SearchForm,
                    WorkForm, GenericFilterFormHelper, NetworkVizFilterForm, PersonResolveUriForm)
from relations.models import (PersonPerson, PersonInstitution, PersonEvent,
                              PersonPlace, InstitutionEvent, InstitutionPlace, InstitutionInstitution, PlacePlace,
                              PlaceEvent, PersonWork, InstitutionWork, PlaceWork, EventWork)
from vocabularies.models import LabelType
from relations.tables import (PersonInstitutionTable, PersonPersonTable, PersonPlaceTable,
                              EntityLabelTable, InstitutionPlaceTable, InstitutionInstitutionTable,
                              PlacePlaceTable, PersonEventTable, PlaceEventTable, InstitutionEventTable,
                              PersonWorkTable, InstitutionWorkTable, PlaceWorkTable, EventWorkTable, EntityUriTable)
from metainfo.models import Uri, UriCandidate, TempEntityClass, Text
from apis.settings.base import BASE_DIR
from helper_functions.stanbolQueries import retrieve_obj
from helper_functions.highlighter import highlight_text
from helper_functions.RDFparsers import GenericRDFParser
from labels.models import Label
from .tables import PersonTable, PlaceTable, InstitutionTable, EventTable, WorkTable
from .filters import PersonListFilter, PlaceListFilter, InstitutionListFilter, EventListFilter, WorkListFilter
from highlighter.forms import SelectAnnotationProject, SelectAnnotatorAgreement

import json


############################################################################
############################################################################
#
#   Helper Functions
#
############################################################################
############################################################################


def set_session_variables(request):
    ann_proj_pk = request.GET.get('project', None)
    types = request.GET.getlist('types', None)
    users_show = request.GET.getlist('users_show', None)
    print(users_show)
    if types:
        request.session['entity_types_highlighter'] = types
    if users_show:
        request.session['users_show_highlighter'] = users_show
    if ann_proj_pk:
        request.session['annotation_project'] = ann_proj_pk
    return request


def get_highlighted_texts(request, instance):
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

############################################################################
############################################################################
#
#   GenericViews
#
############################################################################
############################################################################

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

############################################################################
############################################################################
#
#   PersonViews
#
############################################################################
############################################################################


@method_decorator(login_required, name='dispatch')
class PersonListViewOld(generic.ListView):  # deprecated
    model = Person
    template_name = 'entities/person_list.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        return Person.objects.order_by('name')


@method_decorator(login_required, name='dispatch')
class PersonListView(GenericListView):
    model = Person
    table_class = PersonTable
    template_name = 'entities/person_list_generic.html'
    filter_class = PersonListFilter
    formhelper_class = GenericFilterFormHelper


@login_required
def person_create(request):
    if request.method == "POST":
        form = PersonForm(request.POST)
        form_text = FullTextForm(request.POST, entity='Person')
        if form.is_valid() and form_text.is_valid():
            entity = form.save()
            form_text.save(entity)
            return redirect('entities:person_list')
        else:
            return render(request, 'entities/person_create_generic.html', {
                    'form': form,
                    'form_text': form_text})
    else:
        form = PersonForm()
        form_text = FullTextForm(entity='Person')
        return render(request, 'entities/person_create_generic.html', {
                'form': form,
                'form_text': form_text})


@login_required
def person_edit(request, pk):
    instance = get_object_or_404(Person, pk=pk)
    if request.method == "POST":
        form = PersonForm(request.POST, instance=instance)
        form_text = FullTextForm(request.POST, entity='Person')
        if form.is_valid() and form_text.is_valid():
            entity = form.save()
            form_text.save(entity)
            return redirect('entities:person_list')
        else:
            return render(request, 'entities/person_create_generic.html', {
                    'form': form,
                    'form_text': form_text,
                    'instance': instance})
    else:
        request = set_session_variables(request)
        object_person_pre = PersonPerson.annotation_links.filter_ann_proj(request=request).filter(
            Q(related_personA=instance) | Q(related_personB=instance))
        object_person = []
        for x in object_person_pre:
            object_person.append(x.get_table_dict(instance))
        tb_person = PersonPersonTable(object_person, prefix="PP-")
        tb_person_open = request.GET.get('PP-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_person)
        object_institution = PersonInstitution.annotation_links.filter_ann_proj(request=request).filter(related_person=instance)
        tb_institution = PersonInstitutionTable(list(object_institution), prefix='PI-')
        tb_institution_open = request.GET.get('PI-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_institution)
        object_event = PersonEvent.annotation_links.filter_ann_proj(request=request).filter(related_person=instance)
        tb_event = PersonEventTable(list(object_event), prefix='PE-')
        tb_event_open = request.GET.get('PE-page', None)
        RequestConfig(request).configure(tb_event)
        object_place = PersonPlace.annotation_links.filter_ann_proj(request=request).filter(related_person=instance)
        tb_place = PersonPlaceTable(list(object_place), prefix='PPL-')
        tb_place_open = request.GET.get('PPL-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_place)
        object_work = PersonWork.annotation_links.filter_ann_proj(request=request).filter(related_person=instance)
        tb_work = PersonWorkTable(list(object_work), prefix='PWRK-')
        tb_work_open = request.GET.get('PWRK-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_work)
        object_uri = Uri.objects.filter(entity=instance)
        tb_uri = EntityUriTable(object_uri, prefix='PURI-')
        tb_uri_open = request.GET.get('PURI-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_uri)
        object_revisions = Version.objects.get_for_object(instance)
        object_lod = Uri.objects.filter(entity=instance)
        object_texts, ann_proj_form = get_highlighted_texts(request, instance)
        object_labels = Label.objects.filter(temp_entity=instance)
        tb_label = EntityLabelTable(object_labels, prefix='PL-')
        tb_label_open = request.GET.get('PL-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_label)
        right_panel = [
            ('Uri', tb_uri, 'PersonResolveUri', tb_uri_open),
            ('Person', tb_person, 'PersonPerson', tb_person_open),
            ('Institution', tb_institution, 'PersonInstitution', tb_institution_open),
            ('Place', tb_place, 'PersonPlace', tb_place_open),
            ('Event', tb_event, 'PersonEvent', tb_event_open),
            ('Work', tb_work, 'PersonWork', tb_work_open),
            ('Label', tb_label, 'PersonLabel', tb_label_open)]
        form = PersonForm(instance=instance)
        form_text = FullTextForm(entity='Person', instance=instance)
        form_ann_agreement = SelectAnnotatorAgreement()
        return render(request, 'entities/person_create_generic.html', {
            'entity_type': 'Person',
            'form': form,
            'form_text': form_text,
            'instance': instance,
            'right_panel': right_panel,
            'object_revisions': object_revisions,
            'object_texts': object_texts,
            'object_lod': object_lod,
            'ann_proj_form': ann_proj_form,
            'form_ann_agreement': form_ann_agreement})


@method_decorator(login_required, name='dispatch')
class PersonDelete(DeleteView):
    model = Person
    template_name = 'webpage/confirm_delete.html'
    success_url = reverse_lazy('entities:person_list')


############################################################################
############################################################################
#
#   InstitutionViews
#
############################################################################
############################################################################


@method_decorator(login_required, name='dispatch')
class InstitutionListViewOld(generic.ListView):     #deprecated
    model = Institution
    template_name = 'entities/institution_list.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        return Institution.objects.order_by('name')


@method_decorator(login_required, name='dispatch')
class InstitutionListView(GenericListView):
    model = Institution
    table_class = InstitutionTable
    template_name = 'entities/institution_list_generic.html'
    filter_class = InstitutionListFilter
    formhelper_class = GenericFilterFormHelper

# class InstitutionListViewCustom(generic.ListView):
#   model = Institution
#   template_name = 'entities/institution_list.html'
#   context_object_name = 'object_list'

#   def get_queryset(self, collection_id):
#       return Institution.objects.filter(collection__id=collection_id).order_by('name')


@login_required
def institution_custom_list(request, collection_id):
    collection_id = collection_id
    institutions = Institution.objects.filter(collection__id=collection_id).order_by('name')
    context = {'object_list': institutions}
    context["number_of_objects"] = len(institutions)
    return render(request, 'entities/institution_list.html', context)


@login_required
def institution_create(request):
    if request.method == "POST":
        form = InstitutionForm(request.POST)
        form_text = FullTextForm(request.POST, entity='Institution')
        if form.is_valid() and form_text.is_valid():
            entity = form.save()
            form_text.save(entity)
            return redirect('entities:institution_list')
        else:
            return render(request, 'entities/institution_create_generic.html', {'form': form})
    else:
        form = InstitutionForm()
        form_text = FullTextForm(entity='Institution')
        return render(request, 'entities/institution_create_generic.html', {'form': form, 'form_text': form_text})


@login_required
def institution_edit(request, pk):
    instance = get_object_or_404(Institution, pk=pk)
    if request.method == "POST":
        form = InstitutionForm(request.POST, instance=instance)
        form_text = FullTextForm(request.POST, entity='Institution')
        if form.is_valid() and form_text.is_valid():
            entity = form.save()
            form_text.save(entity)
            return redirect('entities:institution_list')
        else:
            return render(request, 'entities/institution_create_generic.html', {
                'form': form,
                'form_text': form_text,
                'instance': instance})
    else:
        request = set_session_variables(request)
        object_institution = InstitutionInstitution.annotation_links.filter_ann_proj(request=request).filter(
            Q(related_institutionA=instance) | Q(related_institutionB=instance))
        tb_institution = InstitutionInstitutionTable([x.get_table_dict(instance) for x in object_institution], prefix="II-")
        tb_institution_open = request.GET.get('II-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_institution)
        object_person = PersonInstitution.annotation_links.filter_ann_proj(request=request).filter(related_institution=instance)
        tb_person = PersonInstitutionTable(list(object_person), entity='Institution', prefix='PI-')
        tb_person_open = request.GET.get('PI-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_person)
        object_event = InstitutionEvent.annotation_links.filter_ann_proj(request=request).filter(related_institution=instance)
        tb_event = InstitutionEventTable(list(object_event), prefix='IEV-')
        tb_event_open = request.GET.get('IEV-page', None)
        RequestConfig(request).configure(tb_event)
        object_place = InstitutionPlace.annotation_links.filter_ann_proj(request=request).filter(related_institution=instance)
        tb_place = InstitutionPlaceTable(list(object_place), prefix='IPL-')
        tb_place_open = request.GET.get('IPL-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_place)
        object_work = InstitutionWork.annotation_links.filter_ann_proj(request=request).filter(related_institution=instance)
        tb_work = InstitutionWorkTable(list(object_work), prefix='IWRK-')
        tb_work_open = request.GET.get('IWRK-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_work)
        object_revisions = Version.objects.get_for_object(instance)
        object_labels = Label.objects.filter(temp_entity=instance)
        tb_label = EntityLabelTable(object_labels, prefix='IL-')
        tb_label_open = request.GET.get('IL-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_label)
        object_texts, ann_proj_form = get_highlighted_texts(request, instance)
        right_panel = [
            ('Institution', tb_institution, 'InstitutionInstitution', tb_institution_open),
            ('Person', tb_person, 'PersonInstitution', tb_person_open),
            ('Place', tb_place, 'InstitutionPlace', tb_place_open),
            ('Event', tb_event, 'InstitutionEvent', tb_event_open),
            ('Work', tb_work, 'InstitutionWork', tb_work_open),
            ('Label', tb_label, 'PersonLabel', tb_label_open)]
        form = InstitutionForm(instance=instance)
        form_text = FullTextForm(entity='Institution', instance=instance)
        return render(request, 'entities/institution_create_generic.html', {
            'entity_type': 'Institution',
            'form': form,
            'form_text': form_text,
            'instance': instance,
            'right_panel': right_panel,
            'object_texts': object_texts,
            'ann_proj_form': ann_proj_form,
            'object_revisions': object_revisions})


@method_decorator(login_required, name='dispatch')
class InstitutionDelete(DeleteView):
    model = Institution
    template_name = 'webpage/confirm_delete.html'
    success_url = reverse_lazy('entities:institution_list')

############################################################################
############################################################################
#
#   PlaceViews
#
############################################################################
############################################################################

@method_decorator(login_required, name='dispatch')
class PlaceListView(GenericListView):
    model = Place
    table_class = PlaceTable
    template_name = 'entities/place_list_generic.html'
    filter_class = PlaceListFilter
    formhelper_class = GenericFilterFormHelper


@login_required
def place_create(request):
    if request.method == "POST":
        form = PlaceForm(request.POST)
        form_text = FullTextForm(request.POST, entity='Place')
        if form.is_valid() and form_text.is_valid():
            entity = form.save()
            form_text.save(entity)
            return redirect('entities:place_list')
        else:
            return render(request, 'entities/place_create_generic.html', {
                        'form': form,
                        'form_text': form_text})
    else:
        form = PlaceForm()
        form_text = FullTextForm(entity='Place')
        return render(request, 'entities/place_create_generic.html', {
                        'form': form,
                        'form_text': form_text})


@login_required
def place_edit(request, pk):
    instance = get_object_or_404(Place, pk=pk)
    if request.method == "POST":
        form = PlaceForm(request.POST, instance=instance)
        form_text = FullTextForm(request.POST, entity='Place')
        if form.is_valid() and form_text.is_valid():
            entity = form.save()
            form_text.save(entity)
            return redirect('entities:place_list')
        else:
            return render(request, 'entities/place_create_generic.html', {
                'entity_type': 'Place',
            'form': form,
            'form_text': form_text,
            'instance': instance,
            })
    else:
        request = set_session_variables(request)
        object_place = PlacePlace.annotation_links.filter_ann_proj(request=request).filter(
            Q(related_placeA=instance) | Q(related_placeB=instance))
        tb_place = PlacePlaceTable([x.get_table_dict(instance) for x in object_place], prefix="PP-")
        tb_place_open = request.GET.get('PP-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_place)
        object_event = PlaceEvent.annotation_links.filter_ann_proj(request=request).filter(related_place=instance)
        tb_event = PlaceEventTable(list(object_event), prefix='PLEV-')
        tb_event_open = request.GET.get('PLEV-page', None)
        RequestConfig(request).configure(tb_event)
        object_institution = InstitutionPlace.annotation_links.filter_ann_proj(request=request).filter(related_place=instance)
        tb_institution = InstitutionPlaceTable(list(object_institution), entity='Place', prefix='IPL-')
        tb_institution_open = request.GET.get('IPL-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_institution)
        object_person = PersonPlace.annotation_links.filter_ann_proj(request=request).filter(related_place=instance)
        tb_person = PersonPlaceTable(list(object_person), entity='Place', prefix='PPL-')
        tb_person_open = request.GET.get('PPL-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_person)
        object_work = PlaceWork.annotation_links.filter_ann_proj(request=request).filter(related_place=instance)
        tb_work = PlaceWorkTable(list(object_work), prefix='PLWRK-')
        tb_work_open = request.GET.get('PLWRK-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_work)
        object_revisions = Version.objects.get_for_object(instance)
        object_lod = Uri.objects.filter(entity=instance)
        object_labels = Label.objects.filter(temp_entity=instance)
        tb_label = EntityLabelTable(object_labels, prefix='PLL-')
        tb_label_open = request.GET.get('PLL-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_label)
        object_texts, ann_proj_form = get_highlighted_texts(request, instance)
        right_panel = [
            ('Place', tb_place, 'PlacePlace', tb_place_open),
            ('Person', tb_person, 'PersonPlace', tb_person_open),
            ('Institution', tb_institution, 'InstitutionPlace', tb_institution_open),
            ('Event', tb_event, 'PlaceEvent', tb_event_open),
            ('Work', tb_work, 'PlaceWork', tb_work_open),
            ('Label', tb_label, 'PersonLabel', tb_label_open)]
        form = PlaceForm(instance=instance)
        form_text = FullTextForm(entity='Place', instance=instance)
        return render(request, 'entities/place_create_generic.html', {
            'entity_type': 'Place',
            'form': form,
            'form_text': form_text,
            'instance': instance,
            'right_panel': right_panel,
            'object_revisions': object_revisions,
            'object_texts': object_texts,
            'ann_proj_form': ann_proj_form,
            'object_lod': object_lod})


@method_decorator(login_required, name='dispatch')
class PlaceDelete(DeleteView):
    model = Place
    template_name = 'webpage/confirm_delete.html'
    success_url = reverse_lazy('entities:place_list')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PlaceDelete, self).dispatch(*args, **kwargs)

############################################################################
############################################################################
#
#   EventViews
#
############################################################################
############################################################################


@method_decorator(login_required, name='dispatch')
class EventListView(GenericListView):
    model = Event
    table_class = EventTable
    template_name = 'entities/event_list_generic.html'
    filter_class = EventListFilter
    formhelper_class = GenericFilterFormHelper


@login_required
def event_create(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        form_text = FullTextForm(request.POST, entity='Event')
        if form.is_valid() and form_text.is_valid():
            entity = form.save()
            form_text.save(entity)
            return redirect('entities:event_list')
        else:
            return render(request, 'entities/event_create_generic.html', {
                    'form': form,
                    'form_text': form_text})
    else:
        form = EventForm()
        form_text = FullTextForm(entity='Event')
        return render(request, 'entities/event_create_generic.html', {
                'form': form,
                'form_text': form_text})


@login_required
def event_edit(request, pk):
    instance = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        form = EventForm(request.POST, instance=instance)
        form_text = FullTextForm(request.POST, entity='Event')
        if form.is_valid() and form_text.is_valid():
            entity = form.save()
            form_text.save(entity)
            return redirect('entities:event_list')
        else:
            return render(request, 'entities/event_create_generic.html', {
                'form': form,
                'form_text': form_text,
                'instance': instance})
    else:
        request = set_session_variables(request)
        object_person = PersonEvent.annotation_links.filter_ann_proj(request=request).filter(related_event=instance)
        tb_person = PersonEventTable(list(object_person), entity='Event', prefix='PE-')
        tb_person_open = request.GET.get('PE-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_person)
        object_institution = InstitutionEvent.annotation_links.filter_ann_proj(request=request).filter(related_event=instance)
        tb_institution = InstitutionEventTable(list(object_institution), prefix='IEV-', entity='Event')
        tb_institution_open = request.GET.get('IEV-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_institution)
        object_place = PlaceEvent.annotation_links.filter_ann_proj(request=request).filter(related_event=instance)
        tb_place = PlaceEventTable(list(object_place), prefix='PLEV-', entity='Event')
        tb_place_open = request.GET.get('PLEV-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_place)
        object_work = EventWork.annotation_links.filter_ann_proj(request=request).filter(related_event=instance)
        tb_work = EventWorkTable(list(object_work), prefix='EWRK-')
        tb_work_open = request.GET.get('EWRK-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_work)
        object_revisions = Version.objects.get_for_object(instance)
        object_labels = Label.objects.filter(temp_entity=instance)
        tb_label = EntityLabelTable(object_labels, prefix='EL-')
        tb_label_open = request.GET.get('EL-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_label)
        object_texts, ann_proj_form = get_highlighted_texts(request, instance)
        right_panel = [
            ('Institution', tb_institution, 'InstitutionEvent', tb_institution_open),
            ('Person', tb_person, 'PersonEvent', tb_person_open),
            ('Place', tb_place, 'PlaceEvent', tb_place_open),
            ('Work', tb_work, 'EventWork', tb_work_open),
            ('Label', tb_label, 'PersonLabel', tb_label_open)]
        form = EventForm(instance=instance)
        form_text = FullTextForm(entity='Event', instance=instance)
        return render(request, 'entities/event_create_generic.html', {
            'entity_type': 'Event',
            'form': form,
            'form_text': form_text,
            'instance': instance,
            'right_panel': right_panel,
            'object_texts': object_texts,
            'ann_proj_form': ann_proj_form,
            'object_revisions': object_revisions})


@method_decorator(login_required, name='dispatch')
class EventDelete(DeleteView):
    model = Event
    template_name = 'webpage/confirm_delete.html'
    success_url = reverse_lazy('entities:event_list')


############################################################################
############################################################################
#
#   WorkViews
#
############################################################################
############################################################################


@method_decorator(login_required, name='dispatch')
class WorkListView(GenericListView):
    model = Work
    table_class = WorkTable
    template_name = 'entities/work_list_generic.html'
    filter_class = WorkListFilter
    formhelper_class = GenericFilterFormHelper


@login_required
def work_create(request):
    if request.method == "POST":
        form = WorkForm(request.POST)
        form_text = FullTextForm(request.POST, entity='Work')
        if form.is_valid() and form_text.is_valid():
            entity = form.save()
            form_text.save(entity)
            return redirect('entities:work_list')
        else:
            return render(request, 'entities/work_create_generic.html', {
                    'form': form,
                    'form_text': form_text})
    else:
        form = WorkForm()
        form_text = FullTextForm(entity='Event')
        return render(request, 'entities/work_create_generic.html', {
                'form': form,
                'form_text': form_text})


@login_required
def work_edit(request, pk):
    instance = get_object_or_404(Work, pk=pk)
    if request.method == "POST":
        form = WorkForm(request.POST, instance=instance)
        form_text = FullTextForm(request.POST, entity='Work')
        if form.is_valid() and form_text.is_valid():
            entity = form.save()
            form_text.save(entity)
            return redirect('entities:work_list')
        else:
            return render(request, 'entities/work_create_generic.html', {
                'form': form,
                'form_text': form_text,
                'instance': instance})
    else:
        request = set_session_variables(request)
        object_person = PersonWork.annotation_links.filter_ann_proj(request=request).filter(related_work=instance)
        tb_person = PersonWorkTable(list(object_person), entity='Work', prefix='PWRK-')
        tb_person_open = request.GET.get('PWRK-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_person)
        object_institution = InstitutionWork.annotation_links.filter_ann_proj(request=request).filter(related_work=instance)
        tb_institution = InstitutionWorkTable(list(object_institution), prefix='IWRK-', entity='Work')
        tb_institution_open = request.GET.get('IWRK-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_institution)
        object_place = PlaceWork.annotation_links.filter_ann_proj(request=request).filter(related_work=instance)
        tb_place = PlaceWorkTable(list(object_place), prefix='PLWRK-', entity='Work')
        tb_place_open = request.GET.get('PLWRK-page', None)
        object_event = EventWork.annotation_links.filter_ann_proj(request=request).filter(related_work=instance)
        tb_event = EventWorkTable(list(object_event), prefix='EWRK-', entity='Work')
        tb_event_open = request.GET.get('EWRK-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_place)
        object_revisions = Version.objects.get_for_object(instance)
        object_labels = Label.objects.filter(temp_entity=instance)
        tb_label = EntityLabelTable(object_labels, prefix='WRKL-')
        tb_label_open = request.GET.get('WRKL-page', None)
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_label)
        object_texts, ann_proj_form = get_highlighted_texts(request, instance)
        right_panel = [
            ('Institution', tb_institution, 'InstitutionWork', tb_institution_open),
            ('Person', tb_person, 'PersonWork', tb_person_open),
            ('Place', tb_place, 'PlaceWork', tb_place_open),
            ('Event', tb_event, 'EventWork', tb_event_open),
            ('Label', tb_label, 'PersonLabel', tb_label_open)]
        form = WorkForm(instance=instance)
        form_text = FullTextForm(entity='Work', instance=instance)
        return render(request, 'entities/work_create_generic.html', {
            'entity_type': 'Work',
            'form': form,
            'form_text': form_text,
            'instance': instance,
            'right_panel': right_panel,
            'object_texts': object_texts,
            'ann_proj_form': ann_proj_form,
            'object_revisions': object_revisions})


@method_decorator(login_required, name='dispatch')
class WorkDelete(DeleteView):
    model = Work
    template_name = 'webpage/confirm_delete.html'
    success_url = reverse_lazy('entities:work_list')


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
        pers_url = reverse_lazy('entities:person_edit', kwargs={'pk': str(x.related_person.pk)})
        place_url = reverse_lazy('entities:place_edit', kwargs={'pk': str(x.related_place.pk)})
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
        url = reverse_lazy('entities:place_edit', kwargs={'pk': str(pl_n_1.pk)})
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
