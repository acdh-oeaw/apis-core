from django.http import HttpResponse, Http404
from django.template.loader import render_to_string
from django.template import RequestContext
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core import serializers
from django_tables2 import RequestConfig
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from .forms import (PersonPlaceForm, PersonPersonForm, PersonInstitutionForm,
                    InstitutionPlaceForm, InstitutionInstitutionForm, InstitutionPersonForm,
                    InstitutionLabelForm, PersonLabelForm, PersonPlaceHighlighterForm,
                    PersonInstitutionHighlighterForm, PersonPersonHighlighterForm,
                    AddRelationHighlighterPersonForm, PersonEventForm, InstitutionEventForm, PlaceEventForm,
                    EventLabelForm, PersonWorkForm, InstitutionWorkForm, PlaceWorkForm, EventWorkForm,
                    EntityLabelForm, PlacePlaceForm
                    )
from entities.forms import (PlaceHighlighterForm, PersonHighlighterForm)
from highlighter.models import Annotation
from .models import (PersonPlace, PersonPerson, PersonInstitution, InstitutionPlace,
                     InstitutionInstitution, PlacePlace, PersonEvent, InstitutionEvent, PlaceEvent, PersonWork,
                     InstitutionWork, PlaceWork, EventWork)
from .tables import PersonInstitutionTable
from relations.tables import (PersonInstitutionTable, PersonPersonTable, PersonPlaceTable,
                              EntityLabelTable, InstitutionPlaceTable, InstitutionInstitutionTable,
                              PersonEventTable, InstitutionEventTable, PlaceEventTable, PersonWorkTable,
                              InstitutionWorkTable, PlaceWorkTable, EventWorkTable, EntityUriTable, PlacePlaceTable)
from metainfo.models import Uri
from entities.models import Person, Institution, Place, Event, Work
from entities.forms import PersonResolveUriForm
from labels.models import Label
from helper_functions.highlighter import highlight_text

import json, re
from copy import deepcopy

############################################################################
############################################################################
#
#   Generic views for AjaxForms
#
############################################################################
############################################################################

######################################################
# test for class-ignoring _ajax_form-functions
######################################################

# Model-classes must be registered together with their ModelForm-classes
registered_forms = {'PersonPlaceForm': [PersonPlace, Person, Place],
                    'PersonPlaceHighlighterForm': [PersonPlace, Person, Place],
                    'PersonPersonForm': [PersonPerson, Person, Person],
                    'PersonPersonHighlighterForm': [PersonPerson, Person, Person],
                    'PersonInstitutionForm': [PersonInstitution, Person, Institution],
                    'PersonEventForm': [PersonEvent, Person, Event],
                    'PersonWorkForm': [PersonWork, Person, Work],
                    'PersonInstitutionHighlighterForm': [PersonInstitution, Person, Institution],
                    'PersonWorkHighlighterForm': [PersonWork, Person, Work],
                    'PlaceWorkHighlighterForm': [PlaceWork, Place, Work],
                    'InstitutionWorkHighlighterForm': [InstitutionWork, Institution, Work],
                    'InstitutionPlaceForm': [InstitutionPlace, Institution, Place],
                    'InstitutionInstitutionForm': [
                        InstitutionInstitution,
                        Institution,
                        Institution,
                        PersonInstitutionTable],
                    'InstitutionPersonForm': [PersonInstitution, Institution, Person],
                    'InstitutionEventForm': [InstitutionEvent, Institution, Event],
                    'InstitutionWorkForm': [InstitutionWork, Institution, Work],
                    'PlaceEventForm': [PlaceEvent, Place, Event],
                    'PlaceWorkForm': [PlaceWork, Place, Work],
                    'PlacePlaceForm': [PlacePlace, Place, Place],
                    'EventWorkForm': [EventWork, Event, Work],
                    'InstitutionLabelForm': [Label, Institution, Label],
                    'PersonLabelForm': [Label, Person, Label],
                    'EventLabelForm': [Label, Event, Label],
                    'PersonResolveUriForm': [Uri, Person, Uri],
                    'AddRelationHighlighterPersonForm': [],
                    'PlaceHighlighterForm': [Annotation, ],
                    'PersonHighlighterForm': [Annotation, ]
                    }


@login_required
def get_form_ajax(request):
    '''Returns forms rendered in html'''

    FormName = request.POST.get('FormName')
    SiteID = request.POST.get('SiteID')
    ButtonText = request.POST.get('ButtonText')
    ObjectID = request.POST.get('ObjectID')
    entity_type_str = request.POST.get('entity_type')
    print(entity_type_str)
    entity_type = ContentType.objects.get(model=entity_type_str.lower()).model_class()

    if FormName not in registered_forms.keys():
        raise Http404

    if ObjectID == 'false' or ObjectID is None or ObjectID == 'None':
        ObjectID = False
        form = globals()[FormName](entity_type=entity_type)
    else:
        d = registered_forms[FormName][0].objects.get(pk=ObjectID)
        form = globals()[FormName](instance=d, siteID=SiteID, entity_type=entity_type)
    tab = re.match(r'(.*)Form', FormName).group(1)

    data = {'tab': tab, 'form': render_to_string("_ajax_form.html", {
                "entity_type": entity_type_str,
                "form": form,
                'type1': FormName,
                'url2': 'save_ajax_'+FormName,
                'button_text': ButtonText,
                'ObjectID': ObjectID,
                'SiteID': SiteID})}

    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
def save_ajax_form(request, entity_type, kind_form, SiteID, ObjectID=False):
    '''Tests validity and saves AjaxForms, returns them when validity test fails'''
    if kind_form not in registered_forms.keys():
        raise Http404

    button_text = "create/modify"

    if not ObjectID:
        instance_id = ''
    else:
        instance_id = ObjectID
    entity_type_str = entity_type
    entity_type = globals()[entity_type]  # TODO: Use Django entity type instead
    try:
        form = globals()[kind_form](
            data=request.POST,
            entity_type=entity_type,
            request=request)
        call_function = 'EntityRelationForm_response'
        tab = re.match(r'(.*)Form', kind_form).group(1)
        if form.is_valid():
            site_instance = entity_type.objects.get(pk=SiteID)
            set_ann_proj = request.session.get('annotation_project', 1)
            entity_types_highlighter = request.session.get('entity_types_highlighter')
            users_show = request.session.get('users_show_highlighter', None)
            hl_text = None
            tab_query = {'related_'+entity_type_str.lower(): site_instance}
            if ObjectID:
                instance = form.save(instance=ObjectID, site_instance=site_instance)
            else:
                instance = form.save(site_instance=site_instance)
            right_panel = True
            if 'Highlighter' in tab:
                hl_text = {
                    'text': highlight_text(form.get_text_id(),
                                           users_show=users_show,
                                           set_ann_proj=set_ann_proj,
                                           types=entity_types_highlighter).strip(),
                    'id': form.get_text_id()}
            if tab == 'PersonPlace':
                table_html = PersonPlaceTable(
                    PersonPlace.annotation_links.filter_ann_proj(request=request).filter(**tab_query),
                        prefix='PPL-',
                        entity=entity_type_str)
            elif tab == 'InstitutionPlace':
                table_html = InstitutionPlaceTable(
                        InstitutionPlace.annotation_links.filter_ann_proj(request=request).filter(**tab_query),
                        prefix='IPL-',
                        entity=entity_type_str)
            elif tab == 'InstitutionEvent':
                table_html = InstitutionEventTable(
                        InstitutionEvent.annotation_links.filter_ann_proj(request=request).filter(**tab_query),
                        prefix='IEV-',
                        entity=entity_type_str)
            elif tab == 'PersonEvent':
                table_html = PersonEventTable(
                        PersonEvent.annotation_links.filter_ann_proj(request=request).filter(**tab_query),
                        prefix='PEV-',
                        entity=entity_type_str)
            elif tab == 'PersonInstitution':
                table_html = PersonInstitutionTable(
                        PersonInstitution.annotation_links.filter_ann_proj(request=request).filter(**tab_query),
                        prefix='PI-',
                        entity=entity_type_str)
            elif tab == 'PersonLabel':
                table_html = EntityLabelTable(
                        site_instance.label_set.all(),
                        prefix='PL-')
            elif tab == 'InstitutionLabel':
                table_html = EntityLabelTable(
                        site_instance.label_set.all(),
                        prefix='IL-')
            elif tab == 'PlaceEvent':
                table_html = PlaceEventTable(
                        PlaceEvent.annotation_links.filter_ann_proj(request=request).filter(**tab_query),
                        prefix='PLEV-',
                        entity=entity_type_str)
            elif tab == 'PersonWork':
                table_html = PersonWorkTable(
                        PersonWork.annotation_links.filter_ann_proj(request=request).filter(**tab_query),
                        prefix='PWRK-',
                        entity=entity_type_str)
            elif tab == 'InstitutionWork':
                table_html = InstitutionWorkTable(
                        InstitutionWork.annotation_links.filter_ann_proj(request=request).filter(**tab_query),
                        prefix='IWRK-',
                        entity=entity_type_str)
            elif tab == 'PlaceWork':
                table_html = PlaceWorkTable(
                        PlaceWork.annotation_links.filter_ann_proj(request=request).filter(**tab_query),
                        prefix='PLWRK-',
                        entity=entity_type_str)
            elif tab == 'EventWork':
                table_html = EventWorkTable(
                        EventWork.annotation_links.filter_ann_proj(request=request).filter(**tab_query),
                        prefix='EWRK-',
                        entity=entity_type_str)
            elif tab == 'PersonResolveUri':
                table_html = EntityUriTable(
                    Uri.objects.filter(entity=site_instance),
                    prefix = 'PURI-'
                )
            elif tab == 'PersonPerson':
                persPers = []
                for x in PersonPerson.annotation_links.filter_ann_proj(request=request).filter(Q(related_personA=site_instance) | Q(related_personB=site_instance)):
                    persPers.append(x.get_table_dict(site_instance))
                table_html = PersonPersonTable(persPers, prefix='PP-')
            elif tab == 'PlacePlace':
                placePlace = []
                for x in PlacePlace.annotation_links.filter_ann_proj(request=request).filter(
                                Q(related_placeA=site_instance) | Q(related_placeB=site_instance)):
                    placePlace.append(x.get_table_dict(site_instance))
                table_html = PlacePlaceTable(placePlace, prefix='PP-')
            elif tab == 'InstitutionInstitution':
                instInst = []
                for x in InstitutionInstitution.annotation_links.filter_ann_proj(request=request).filter(Q(related_institutionA=site_instance) | Q(related_institutionB=site_instance)):
                    instInst.append(x.get_table_dict(site_instance))
                table_html = InstitutionInstitutionTable(instInst, prefix='II-')
            elif tab == 'PersonPlaceHighlighter':
                tab = 'PersonPlace'
                table_html = PersonPlaceTable(
                    PersonPlace.annotation_links.filter_ann_proj(request=request).filter(**tab_query),
                    prefix='PPL-',
                    entity=entity_type_str)
                call_function = 'HighlForm_response'
            elif tab == 'PersonInstitutionHighlighter':
                tab = 'PersonInstitution'
                table_html = PersonInstitutionTable(
                        PersonInstitution.annotation_links.filter_ann_proj(request=request).filter(**tab_query),
                        prefix='PI-',
                        entity=entity_type_str)
                call_function = 'HighlForm_response'
            elif tab == 'PersonPersonHighlighter':
                persPers = []
                for x in PersonPerson.annotation_links.filter_ann_proj(request=request).filter(Q(related_personA=site_instance) | Q(related_personB=site_instance)):
                    persPers.append(x.get_table_dict(site_instance))
                table_html = PersonPersonTable(
                            persPers,
                            prefix='PP-')
                call_function = 'HighlForm_response'
            elif tab == 'AddRelationHighlighterPerson' or tab == 'PlaceHighlighter' or tab == 'PersonHighlighter':
                table_html = None
                right_panel = False
                call_function = 'PAddRelation_response'
                instance = None
            if instance:
                instance2 = instance.get_web_object()
            else:
                instance2 = None
            if table_html:
                table_html2 = table_html.as_html(request)
            else:
                table_html2 = None
            data = {'test': True, 'tab': tab, 'call_function': call_function,
                    'instance': instance2,
                    'table_html': table_html2,
                    'text': hl_text,
                    'right_panel': right_panel}
        else:
            if 'Highlighter' in tab:
                call_function = 'HighlForm_response'
            data = {'test': False, 'call_function': call_function,
                    'DivID': 'div_'+kind_form+instance_id,
                    'form': render_to_string("_ajax_form.html", {
                        "entity_type": entity_type_str,
                        "form": form, 'type1': kind_form, 'url2': 'save_ajax_'+kind_form,
                        'button_text': button_text, 'ObjectID': ObjectID, 'SiteID': SiteID},
                        context_instance=RequestContext(request))}

    except Exception as e:
        print('Error in save method')
        print(e)
        data = {'test': False, 'error': json.dumps(e)}
    return HttpResponse(json.dumps(data), content_type='application/json')
