# -*- coding: utf-8 -*-
from django import forms
from django.core.urlresolvers import reverse_lazy
#from autocomplete_light import shortcuts as al
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.layout import Layout
from crispy_forms.bootstrap import Accordion, AccordionGroup
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.db.models.fields import BLANK_CHOICE_DASH
from django.contrib.contenttypes.models import ContentType

from .models import Person, Place, Institution, Event, Work
from vocabularies.models import TextType
from metainfo.models import Text, Uri
from highlighter.models import Annotation, AnnotationProject

from helper_functions.RDFparsers import GenericRDFParser


class SearchForm(forms.Form):
    search = forms.CharField(label='Search')

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_id = 'searchForm'
        helper.form_tag = False
        helper.add_input(Submit('fieldn', 'search'))
        helper.form_method = 'GET'
        return helper


def get_entities_form(entity):
    class GenericEntitiesForm(forms.ModelForm):
        class Meta:
            model = ContentType.objects.get(app_label='entities', model=entity.lower()).model_class()
            exclude = ['start_date', 'end_date', 'text', 'source']

        def __init__(self, *args, **kwargs):
            super(GenericEntitiesForm, self).__init__(*args, **kwargs)
            self.helper = FormHelper()
            self.helper.form_class = entity.title()+'Form'
            self.helper.form_tag = False
            self.helper.help_text_inline = True
            acc_grp1 = AccordionGroup('Metadata {}'.format(entity.title()))
            acc_grp2 = AccordionGroup(
                        'MetaInfo',
                        'collection',
                        'references',
                        'notes',
                        'review')
            for f in self.fields.keys():
                if f not in acc_grp2:
                    acc_grp1.append(f)
            self.helper.layout = Layout(
                Accordion(
                    acc_grp1,
                    acc_grp2
                    )
            )
            self.fields['status'].required = False
            self.fields['start_date_written'].required = False
            self.fields['end_date_written'].required = False
    return GenericEntitiesForm


class PersonForm(forms.ModelForm):

    class Meta:
        model = Person
        fields = [
            'first_name', 'name', 'title', 'profession', 'gender',
            'review', 'start_date_written', 'end_date_written', 'collection', 'references', 'notes']
        labels = {
            'start_date_written': _('Day of birth'),
            'end_date_written': _('Day of Death'),
        }

    def __init__(self, *args, **kwargs):
        super(PersonForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'PersonForm'
        self.helper.form_tag = False
        self.helper.help_text_inline = True
        self.helper.layout = Layout(
            Accordion(
                AccordionGroup(
                    'Names, Titles & Profession',
                    'name',
                    'first_name',
                    'title',
                    'profession'),
                AccordionGroup(
                    'Birth- and Deathdates',
                    'start_date_written',
                    'end_date_written',
                    'gender'),
                AccordionGroup(
                    'MetaInfo',
                    'collection',
                    'references',
                    'notes',
                    'review'))
            )
        self.fields['start_date_written'].required = False
        self.fields['end_date_written'].required = False


class InstitutionForm(forms.ModelForm):

    class Meta:
        model = Institution
        fields = [
            'name', 'kind', 'start_date_written', 'end_date_written',
            'homepage', 'collection', 'review', 'references', 'notes']
        labels = {
            'start_date_written': _('Day of foundation'),
            'end_date_written': _('Day of closing'),
        }

    def __init__(self, *args, **kwargs):
        super(InstitutionForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'InstitutionForm'
        self.helper.form_tag = False
        self.helper.help_text_inline = True
        self.helper.layout = Layout(
            Accordion(
                AccordionGroup(
                    'Name, Type and Dates',
                    'name',
                    'kind',
                    'start_date_written',
                    'end_date_written',
                    'homepage'
                    ),
                AccordionGroup(
                    'MetaInfo',
                    'collection',
                    'references',
                    'notes',
                    'review')
                )
            )
        self.fields['start_date_written'].required = False
        self.fields['end_date_written'].required = False


class PlaceForm(forms.ModelForm):
    start_date_written = forms.CharField(label='since', required=False)
    end_date_written = forms.CharField(label='until', required=False)

    class Meta:
        model = Place
        fields = [
            'name', 'kind', 'status', 'lat', 'lng', 'start_date_written',
            'end_date_written', 'collection', 'review', 'references', 'notes']

    def __init__(self, *args, **kwargs):
        super(PlaceForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'PlaceForm'
        self.helper.form_tag = False
        self.helper.help_text_inline = True
        self.helper.layout = Layout(
            Accordion(
                AccordionGroup(
                    'Name, Type and Dates',
                    'name',
                    'kind',
                    'status',
                    'lat',
                    'lng',
                    'start_date_written',
                    'end_date_written',
                ),
                AccordionGroup(
                    'MetaInfo',
                    'collection',
                    'references',
                    'notes',
                    'review')
            )
        )
        self.fields['start_date_written'].required = False
        self.fields['end_date_written'].required = False


class EventForm(forms.ModelForm):

    class Meta:
        model = Event
        fields = [
            'name', 'kind', 'start_date_written', 'end_date_written',
            'collection', 'review', 'references', 'notes']
        labels = {
            'start_date_written': _('Start date'),
            'end_date_written': _('End date'),
        }

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'EventForm'
        self.helper.form_tag = False
        self.helper.help_text_inline = True
        self.helper.layout = Layout(
            Accordion(
                AccordionGroup(
                    'Name, Type and Dates',
                    'name',
                    'kind',
                    'start_date_written',
                    'end_date_written',
                    ),
                AccordionGroup(
                    'MetaInfo',
                    'collection',
                    'references',
                    'notes',
                    'review')
                )
            )
        self.fields['start_date_written'].required = False
        self.fields['end_date_written'].required = False


class WorkForm(forms.ModelForm):

    class Meta:
        model = Work
        fields = [
            'name', 'kind', 'start_date_written', 'end_date_written',
            'collection', 'review', 'references', 'notes']
        labels = {
            'start_date_written': _('Start date'),
            'end_date_written': _('End date'),
        }

    def __init__(self, *args, **kwargs):
        super(WorkForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'WorkForm'
        self.helper.form_tag = False
        self.helper.help_text_inline = True
        self.helper.layout = Layout(
            Accordion(
                AccordionGroup(
                    'Name, Type and Dates',
                    'name',
                    'kind',
                    'start_date_written',
                    'end_date_written',
                    ),
                AccordionGroup(
                    'MetaInfo',
                    'collection',
                    'references',
                    'notes',
                    'review')
                )
            )
        self.fields['start_date_written'].required = False
        self.fields['end_date_written'].required = False


class FullTextForm(forms.Form):

    def save(self, entity):
        cd = self.cleaned_data
        text = None
        for f in cd.keys():
            text_type = TextType.objects.get(pk=f.split('_')[1])
            print(text_type)
            text = Text.objects.filter(tempentityclass=entity, kind=text_type)
            if text.count() == 1:
                text = text[0]
                text.text = cd[f]
                text.save()
            elif text.count() == 0:
                text = Text(text=cd[f], kind=text_type)
                text.save()
                entity.text.add(text)
        return text

    def __init__(self, *args, **kwargs):
        if 'entity' in kwargs.keys():
            entity = kwargs.pop('entity', None)
        else:
            entity = None
        if 'instance' in kwargs.keys():
            instance = kwargs.pop('instance', None)
        else:
            instance = None
        super(FullTextForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'FullTextForm'
        self.helper.form_tag = False
        self.helper.help_text_inline = True
        collections = []
        if instance:
            for i in instance.collection.all():
                collections.append(i)
        try:
            if len(collections) > 0:
                q = TextType.objects.filter(entity__iexact=entity, collections__in=collections)
            else:
                q = TextType.objects.filter(entity__iexact=entity)
            for txt in q:
                self.fields['text_'+str(txt.pk)] = forms.CharField(
                    label=txt.name,
                    help_text=txt.description,
                    required=False,
                    widget=forms.Textarea)
            if instance:
                for t in Text.objects.filter(tempentityclass=instance):
                    self.fields['text_'+str(t.kind.pk)].initial = t.text
        except:
            pass


class PersonResolveUriForm(forms.Form):
    #person = forms.CharField(label=False, widget=al.TextWidget('PersonAutocomplete'))
    person = forms.CharField(label=False)
    person_uri = forms.CharField(required=False, widget=forms.HiddenInput())

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        if cd['person'].startswith('http'):
            uri = Uri.objects.create(uri=cd['person'], entity=site_instance)
        else:
            uri = Uri.objects.create(uri=cd['person_uri'], entity=site_instance)
        return uri

    def __init__(self, *args, **kwargs):
        entity_type = kwargs.pop('entity_type', False)
        self.request = kwargs.pop('request', False)
        super(PersonResolveUriForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    def clean(self):
        cleaned_data = super(PersonResolveUriForm, self).clean()
        if Uri.objects.filter(uri=cleaned_data['person_uri']).exists():
            self.add_error('person', 'This Person has already been added to the DB.')
        elif cleaned_data['person'].startswith('http'):
            if Uri.objects.filter(uri=cleaned_data['person']).exists():
                self.add_error('person', 'This URI has already been added to the DB.')


class BaseEntityHighlighterForm(forms.Form):
    HL_start = forms.IntegerField(widget=forms.HiddenInput)
    HL_end = forms.IntegerField(widget=forms.HiddenInput)
    HL_text_id = forms.CharField(widget=forms.HiddenInput)
    HL_id = forms.CharField(widget=forms.HiddenInput, required=False)

    def save(self, *args, **kwargs):
        cd = self.cleaned_data
        txt = Text.objects.get(pk=cd['HL_text_id'][5:])
        if cd['HL_id']:
            a = Annotation.objects.get(pk=cd['HL_id'])
            a.user_added = self.request.user
            a.annotation_project_id = int(self.request.session.get('annotation_project', 1))
        else:
            a = Annotation(
                start=cd['HL_start'],
                end=cd['HL_end'],
                text=txt,
                user_added=self.request.user,
                annotation_project_id=int(self.request.session.get('annotation_project', 1)))
        a.save()
        return a

    def __init__(self, *args, **kwargs):
        self.entity_type = kwargs.pop('entity_type', False)
        self.request = kwargs.pop('request', False)
        self.instance = kwargs.pop('instance', False)
        siteID = kwargs.pop('siteID', False)
        super(BaseEntityHighlighterForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['HL_id'].initial = self.instance
        self.helper = FormHelper()
        self.helper.form_tag = False

    def get_text_id(self):
        return self.cleaned_data['HL_text_id'][5:]


class PersonHighlighterForm(BaseEntityHighlighterForm):

    #person = forms.CharField(label='Person', widget=al.TextWidget('PersonAutocomplete'))
    person = forms.CharField(label='Person')
    person_uri = forms.CharField(required=False, widget=forms.HiddenInput())

    def save(self, *args, **kwargs):
        x = super(PersonHighlighterForm, self).save(*args, **kwargs)
        cd = self.cleaned_data
        p = Person.get_or_create_uri(cd['person_uri'])
        if not p:
            p = GenericRDFParser(cd['person_uri'], 'Person').get_or_create()
        if len(x.entity_link.all()) > 0:
            if p != x.entity_link.all()[0]:
                x.entity_link.clear()
                x.entity_link.add(p)
        else:
            x.entity_link.add(p)
        return p

    def __init__(self, *args, **kwargs):
        super(PersonHighlighterForm, self).__init__(*args, **kwargs)
        self.helper.form_class = 'PersonEntityForm'
        if self.instance:
            a = self.instance
            ent = a.entity_link.all()[0]
            self.fields['person'].initial = ent.name+', '+ent.first_name
            self.fields['person_uri'].initial = Uri.objects.filter(entity=ent)[0].uri


class PlaceHighlighterForm(BaseEntityHighlighterForm):
    #place = forms.CharField(label='Place', widget=al.TextWidget('OrtAutocomplete'))
    place = forms.CharField(label='Place')
    place_uri = forms.CharField(required=False, widget=forms.HiddenInput())

    def save(self, *args, **kwargs):
        x = super(PlaceHighlighterForm, self).save(*args, **kwargs)
        cd = self.cleaned_data
        p = Place.get_or_create_uri(cd['place_uri'])
        if not p:
            p = GenericRDFParser(cd['place_uri'], 'Place').get_or_create()
        if len(x.entity_link.all()) > 0:
            if p != x.entity_link.all()[0]:
                x.entity_link.clear()
                x.entity_link.add(p)
        else:
            x.entity_link.add(p)
        return p

    def __init__(self, *args, **kwargs):
        super(PlaceHighlighterForm, self).__init__(*args, **kwargs)
        self.helper.form_class = 'PlaceEntityForm'
        if self.instance:
            a = self.instance
            ent = a.entity_link.all()[0]
            self.fields['place'].initial = ent.name
            self.fields['place_uri'].initial = Uri.objects.filter(entity=ent)[0].uri


class NetworkVizFilterForm(forms.Form):
    choices = (('PersonPlace', 'Person Place'),
               ('PersonInstitution', 'Person Institution'),
               ('PersonEvent', 'Person Event'),
               ('PersonWork', 'Person Work'),
               ('PersonPerson', 'Person Person'),
               ('InstitutionPlace', 'Institution Place'),
               ('InstitutionEvent', 'Institution Event'),
               ('InstitutionWork', 'Institution Work'),
               ('InstitutionInstitution', 'Institution Institution'),
               ('PlaceEvent', 'Place Event'),
               ('PlaceWork', 'Place Work'),
               ('PlacePlace', 'Place Place'),
               ('EventWork', 'Event Work'),
               ('EventEvent', 'Event Event'),
               ('WorkWork', 'Work Work'))
    select_relation = forms.ChoiceField(choices=choices)
    #search_source = forms.CharField(widget=al.ChoiceWidget('DB_PersonAutocomplete'), required=False)
    search_source = forms.CharField(required=False)
    #select_kind = forms.CharField(widget=al.ChoiceWidget('VCPersonPlaceAutocomplete'), required=False)
    search_target = forms.CharField(required=False)
    #search_target = forms.CharField(widget=al.ChoiceWidget('DB_PlaceAutocomplete'), required=False)
    ann_include_all = forms.BooleanField(required=False, label='Include general relations',
                                        help_text="""Not all relations are connected to an annotation.\
                                        If checked relations that are not attached to an annotation are include.\
                                        This setting is only used when an Annotation project is specified.""")
    start_date = forms.CharField(label='Start date', required=False,
                                 widget=forms.TextInput(attrs={
                                     'data-provide': 'datepicker',
                                     'data-date-format': 'dd.mm.yyyy'}))
    end_date = forms.CharField(label='End date', required=False,
                               widget=forms.TextInput(attrs={
                                   'data-provide': 'datepicker',
                                   'data-date-format': 'dd.mm.yyyy'}))

    def __init__(self, *args, **kwargs):
        super(NetworkVizFilterForm, self).__init__(*args, **kwargs)
        self.fields['annotation_proj'] = forms.ChoiceField(
            label='Annotation Project',
            choices=BLANK_CHOICE_DASH + list((x.pk, x.name) for x in AnnotationProject.objects.all()),
            required=False,
            help_text="Include only relations related to this annotation project \
            (See the include general relations checkbox)")
        self.helper = FormHelper()
        self.helper.form_class = 'FilterNodesForm'
        self.helper.form_action = 'NetJson-list'
        self.helper.add_input(Submit('Submit', 'Add nodes'))
        self.order_fields(('select_relation', 'ann_include_all',
                           'annotation_proj', 'search_source', 'select_kind', 'search_target'))


class GenericFilterFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(GenericFilterFormHelper, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_class = 'genericFilterForm'
        self.form_method = 'GET'
        self.add_input(Submit('Filter', 'Filter'))
