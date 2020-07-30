import json
import re
import inspect

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, Http404
from django.template.loader import render_to_string
from apis_core.apis_relations import forms as relation_form_module

from apis_core.apis_entities.models import Person, Institution, Place, Event, Work, AbstractEntity
from apis_core.apis_labels.models import Label
from apis_core.apis_metainfo.models import Uri
from .forms2 import GenericRelationForm
from .models import (
    PersonPlace, PersonPerson, PersonInstitution, InstitutionPlace,
    InstitutionInstitution, PlacePlace, PersonEvent, InstitutionEvent, PlaceEvent, PersonWork,
    InstitutionWork, PlaceWork, EventWork, WorkWork
)
#from .forms import PersonLabelForm, InstitutionLabelForm, PlaceLabelForm, EventLabelForm
from .tables import LabelTableEdit

form_module_list = [relation_form_module]

if 'apis_highlighter' in settings.INSTALLED_APPS:
    from apis_core.helper_functions.highlighter import highlight_text
    from apis_highlighter import forms as highlighter_form_module
    form_module_list.append(highlighter_form_module)


def turn_form_modules_into_dict(form_module_list):
    """
    Since form classes are loaded dynamically from the respective modules and it's settings-dependent which modules
    are imported and which not, it's better to differentiate here which modules are imported close to their imports
    and then providing a dict for later extraction of the required form class.
    """

    form_class_dict = {}
    for m in form_module_list:
        for name, cls in inspect.getmembers(m, inspect.isclass):
            form_class_dict[name] = cls

    return form_class_dict

form_class_dict = turn_form_modules_into_dict(form_module_list)


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
registered_forms = {'WorkWorkForm': [WorkWork, Work, Work],
                    'PersonPlaceForm': [PersonPlace, Person, Place],
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
                        Institution],
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
                    'SundayHighlighterForm': [ ],
                    'AddRelationHighlighterPersonForm': [],
                    #'PlaceHighlighterForm': [Annotation, ],
                    #'PersonHighlighterForm': [Annotation, ]
                    }


@login_required
def get_form_ajax(request):
    '''Returns forms rendered in html'''

    FormName = request.POST.get('FormName')
    SiteID = request.POST.get('SiteID')
    ButtonText = request.POST.get('ButtonText')
    ObjectID = request.POST.get('ObjectID')
    entity_type_str = request.POST.get('entity_type')
    form_match = re.match(r'([A-Z][a-z]+)([A-Z][a-z]+)(Highlighter)?Form', FormName)
    form_match2 = re.match(r'([A-Z][a-z]+)(Highlighter)?Form', FormName)
    if FormName and form_match:
        entity_type_v1 = ContentType.objects.filter(
            model='{}{}'.format(form_match.group(1).lower(), form_match.group(2)).lower(),
            app_label='apis_relations')
        entity_type_v2 = ContentType.objects.none()
    elif FormName and form_match2:
        entity_type_v2 = ContentType.objects.filter(
            model='{}'.format(
                form_match.group(1).lower(),
                app_label='apis_entities'))
        entity_type_v1 = ContentType.objects.none()
    else:
        entity_type_v1 = ContentType.objects.none()
        entity_type_v2 = ContentType.objects.none()
    if ObjectID == 'false' or ObjectID is None or ObjectID == 'None':
        ObjectID = False
        form_dict = {'entity_type': entity_type_str}
    elif entity_type_v1.count() > 0:
        d = entity_type_v1[0].model_class().objects.get(pk=ObjectID)
        form_dict = {'instance': d, 'siteID': SiteID, 'entity_type': entity_type_str}
    elif entity_type_v2.count() > 0:
        d = entity_type_v2[0].model_class().objects.get(pk=ObjectID)
        form_dict = {'instance': d, 'siteID': SiteID, 'entity_type': entity_type_str}
    else:
        if FormName not in registered_forms.keys():
            raise Http404
        d = registered_forms[FormName][0].objects.get(pk=ObjectID)
        form_dict = {'instance': d, 'siteID': SiteID, 'entity_type': entity_type_str}
    if entity_type_v1.count() > 0:
        form_dict['relation_form'] = '{}{}'.format(form_match.group(1), form_match.group(2))
        if form_match.group(3) == 'Highlighter':
            form_dict['highlighter'] = True
        form = GenericRelationForm(**form_dict)
    else:
        form_class = form_class_dict[FormName]
        form = form_class(**form_dict)
    tab = FormName[:-4]
    data = {'tab': tab, 'form': render_to_string("apis_relations/_ajax_form.html", {
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
    entity_type = AbstractEntity.get_entity_class_of_name(entity_type)

    form_match = re.match(r'([A-Z][a-z]+)([A-Z][a-z]+)?(Highlighter)?Form', kind_form)
    form_dict = {'data': request.POST,
                 'entity_type': entity_type,
                 'request': request}

    test_form_relations = ContentType.objects.filter(
        model='{}{}'.format(form_match.group(1).lower(), form_match.group(2)).lower(),
        app_label='apis_relations')
    tab = re.match(r'(.*)Form', kind_form).group(1)
    call_function = 'EntityRelationForm_response'
    if test_form_relations.count() > 0:
        relation_form = test_form_relations[0].model_class()
        form_dict['relation_form'] = relation_form
        if form_match.group(3) == 'Highlighter':
            form_dict['highlighter'] = True
            tab = form_match.group(1)+form_match.group(2)
            call_function = 'HighlForm_response'
        form = GenericRelationForm(**form_dict)
    else:
        form_class = form_class_dict[kind_form]
        form = form_class(**form_dict)
    if form.is_valid():
        site_instance = entity_type.objects.get(pk=SiteID)
        set_ann_proj = request.session.get('annotation_project', 1)
        entity_types_highlighter = request.session.get('entity_types_highlighter')
        users_show = request.session.get('users_show_highlighter', None)
        hl_text = None
        if ObjectID:
            instance = form.save(instance=ObjectID, site_instance=site_instance)
        else:
            instance = form.save(site_instance=site_instance)
        right_card = True
        if test_form_relations.count() > 0:
            table_html = form.get_html_table(entity_type_str, request, site_instance, form_match)
        if 'Highlighter' in tab or form_match.group(3) == 'Highlighter':
            hl_text = {
                'text': highlight_text(form.get_text_id(),
                                       users_show=users_show,
                                       set_ann_proj=set_ann_proj,
                                       types=entity_types_highlighter).strip(),
                'id': form.get_text_id()}
        if tab == 'PersonLabel':
            table_html = LabelTableEdit(
                    data=site_instance.label_set.all(),
                    prefix='PL-')
        elif tab == 'InstitutionLabel':
            table_html = LabelTableEdit(
                    data=site_instance.label_set.all(),
                    prefix='IL-')
        elif tab == 'PersonResolveUri':
            table_html = EntityUriTable(
                Uri.objects.filter(entity=site_instance),
                prefix='PURI-'
            )

        elif tab == 'AddRelationHighlighterPerson' or tab == 'PlaceHighlighter' or tab == 'PersonHighlighter' or tab == 'SundayHighlighter':
            table_html = None
            right_card = False
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
                'right_card': right_card}
    else:
        if 'Highlighter' in tab:
            call_function = 'HighlForm_response'
        data = {'test': False, 'call_function': call_function,
                'DivID': 'div_'+kind_form+instance_id,
                'form': render_to_string("apis_relations/_ajax_form.html", context={
                    "entity_type": entity_type_str,
                    "form": form, 'type1': kind_form, 'url2': 'save_ajax_'+kind_form,
                    'button_text': button_text, 'ObjectID': ObjectID, 'SiteID': SiteID},
                    request=request)}

    # except Exception as e:
    #     print('Error in save method')
    #     print(e)
    #     data = {'test': False, 'error': json.dumps(str(e))}
    return HttpResponse(json.dumps(data), content_type='application/json')
