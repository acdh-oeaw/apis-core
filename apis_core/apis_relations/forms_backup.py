#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime

from django import forms
import autocomplete_light.shortcuts as al
from django.utils.translation import ugettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.bootstrap import Accordion, AccordionGroup
from django.contrib.contenttypes.models import ContentType

from .models import (PersonPlace, PersonPerson, PersonInstitution,
                     InstitutionPlace, InstitutionInstitution, PersonEvent, InstitutionEvent,
                     PlaceEvent, PersonWork, InstitutionWork, PlaceWork, EventWork, PlacePlace)
from apis_core.entities.models import Place, Institution, Person, Event, Work
from apis_core.metainfo.models import Uri, Text
from apis_core.vocabularies.models import (PersonInstitutionRelation, PersonPlaceRelation, InstitutionPlaceRelation,
                                 PersonEventRelation, InstitutionEventRelation, PlaceEventRelation,
                                 InstitutionInstitutionRelation, PersonPersonRelation)
from apis_core.labels.models import Label
from highlighter.models import Annotation
from apis_core.helper_functions.RDFparsers import GenericRDFParser


##############################################
# Generic
##############################################

class EntityLabelForm(forms.ModelForm):

    class Meta:
        model = Label
        fields = ['label', 'isoCode_639_3', 'label_type']

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        if instance:
            x = Label.objects.get(pk=instance)
            x.label = cd['label']
            x.isoCode_639_3 = cd['isoCode_639_3']
            x.label_type = cd['label_type']
        else:
            x = super(EntityLabelForm, self).save(commit=False)
            x.temp_entity = site_instance
        x.save()
        return x

    def __init__(self, siteID=None, *args, **kwargs):
        entity_type = kwargs.pop('entity_type', False)
        self.request = kwargs.pop('request', False)
        super(EntityLabelForm, self).__init__(*args, **kwargs)
        self.fields['label'].required = True
        self.fields['label_type'].required = True
        self.helper = FormHelper()
        self.helper.form_class = 'EntityLabelForm'
        self.helper.form_tag = False

##############################################
# Person
##############################################


class PersonPlaceForm(forms.ModelForm):
    place = forms.CharField(label='Ort', widget=al.TextWidget('OrtAutocomplete'))
    place_uri = forms.CharField(required=False, widget=forms.HiddenInput())
    person = forms.CharField(label='Person', widget=al.TextWidget('PersonAutocomplete'))
    person_uri = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = PersonPlace
        fields = ['relation_type', 'place', 'place_uri', 'person', 'person_uri', 'start_date_written', 'end_date_written', 'references', 'notes']
        labels = {
            'start_date_written': _('Start'),
            'end_date_written': _('End'),
            'relation_type': _('Type')
            }
        widgets = {
        'relation_type': al.ChoiceWidget('VCPersonPlaceAutocomplete')
        }

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        if instance:
            x = PersonPlace.objects.get(pk=str(instance))
            x.relation_type = cd['relation_type']
            x.start_date_written = cd['start_date_written']
            x.end_date_written = cd['end_date_written']
            x.notes = cd['notes']
            x.references = cd['references']
        else:
            x = super(PersonPlaceForm, self).save(commit=False)
        if 'place' in cd.keys():
            x.related_person = site_instance
            place = GenericRDFParser(cd['place_uri'], 'Place').get_or_create()
            x.related_place = place
        elif 'person' in cd.keys():
            x.related_place = site_instance
            person = Person.get_or_create_uri(cd['person_uri'])
            if not person:
                person = GenericRDFParser(cd['person_uri'], 'Person').get_or_create()
            x.related_person = person
        x.save()
        return x

    def __init__(self, siteID=None, *args, **kwargs):
        entity_type = kwargs.pop('entity_type', False)
        self.request = kwargs.pop('request', False)
        if not hasattr(self, 'request'):
            self.request = kwargs.pop('request', False)
        super(PersonPlaceForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['relation_type'].required = True
        self.helper = FormHelper()
        self.helper.form_class = 'PersonPlaceForm'
        self.helper.form_tag = False
        self.helper.layout = Layout(
                'relation_type',
                'start_date_written',
                'end_date_written',
                Accordion(
                    AccordionGroup(
                        'Notes and References',
                        'notes',
                        'references',
                        active=False,
                        css_id="persPlace_notes_refs")))
        if entity_type == Place:
            choices = []
            self.fields.pop('place')
            self.fields.pop('place_uri')
            for x in PersonPlaceRelation.objects.all():
                choices.append((x.pk, x.name_reverse))
            self.fields['relation_type'].choices = choices
            if instance and instance.id:
                self.fields['person'].initial = instance.related_person
                self.fields['person_uri'].initial = Uri.objects.filter(entity=instance.related_person)[0]
                self.fields['relation_type'].widget = al.ChoiceWidget(
                    'VCPersonPlaceReverseAutocomplete',
                    extra_context={'values': [instance.relation_type.pk],
                                   'choices': [instance.relation_type.label_reverse]})
            else:
                self.fields['relation_type'].widget = al.ChoiceWidget('VCPersonPlaceReverseAutocomplete')
            self.helper.layout.insert(1, 'person')
            self.helper.layout.insert(2, 'person_uri')            
        else:
            self.fields.pop('person')
            self.fields.pop('person_uri')
            if instance and instance.id:
                self.fields['place'].initial = instance.related_place.name
                self.fields['place_uri'].initial = Uri.objects.filter(entity=instance.related_place)[0]
                self.fields['relation_type'].widget = al.ChoiceWidget(
                    'VCPersonPlaceReverseAutocomplete',
                    extra_context={'values': [instance.relation_type.pk],
                                   'choices': [instance.relation_type.label]})
            self.helper.layout.insert(1, 'place')
            self.helper.layout.insert(2, 'place_uri')


class PersonPersonForm(forms.ModelForm):
    person = forms.CharField(label='Person', widget=al.TextWidget('PersonAutocomplete'))
    person_uri = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = PersonPerson
        fields = ['relation_type', 'person', 'start_date_written', 'end_date_written', 'references', 'notes']
        labels = {
            'start_date_written': _('Start'),
            'end_date_written': _('End'),
            'relation_type': _('Art'),
        }
        widgets = {
            'relation_type': al.ChoiceWidget('VCPersonPersonAutocomplete')
        }

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        if instance:
            x = PersonPerson.objects.select_related(
                'related_personA__tempentityclass_ptr__uri',
                'related_personB__tempentityclass_ptr__uri').get(pk=instance)
            x.start_date_written = cd['start_date_written']
            x.end_date_written = cd['end_date_written']
            x.relation_type = cd['relation_type']
            x.notes = cd['notes']
            x.references = cd['references']
            if site_instance == x.related_personB:
                if x.related_personA.uri_set.filter(uri=cd['person_uri']).count() == 0:
                    personA = Person.get_or_create_uri(cd['person_uri'])
                    if not personA:
                        personA = GenericRDFParser(cd['person_uri'], 'Person').get_or_create()
                    x.related_personA = personA
        else:
            x = super(PersonPersonForm, self).save(commit=False)
            x.related_personA = site_instance
            personB = Person.get_or_create_uri(cd['person_uri'])
            if not personB:
                personB = GenericRDFParser(cd['person_uri'], 'Person').get_or_create()  # TODO: Function needs to be replaced with class
            x.related_personB = personB
        x.save()
        return x

    def __init__(self, siteID=None, *args, **kwargs):
        entity_type = kwargs.pop('entity_type', False)
        self.request = kwargs.pop('request', False)
        if not hasattr(self, 'request'):
            self.request = kwargs.pop('request', False)
        super(PersonPersonForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.id:
            if siteID:
                siteID = Person.objects.get(pk=siteID)
                if siteID == instance.related_personB:
                    rel_pers = instance.related_personA
                    self.fields['relation_type'].widget = al.ChoiceWidget(
                        'VCPersonPersonReverseAutocomplete',
                        extra_context={'values': [instance.relation_type.pk],
                                       'choices': [instance.relation_type.label_reverse]})
                else:
                    rel_pers = instance.related_personB
            self.fields['person'].initial = rel_pers
            self.fields['person_uri'].initial = Uri.objects.filter(entity=rel_pers)[0]
        self.fields['relation_type'].required = True
        self.helper = FormHelper()
        self.helper.form_class = 'PersonPersonForm'
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'relation_type',
            'person',
            'person_uri',
            'start_date_written',
            'end_date_written',
            Accordion(
                AccordionGroup(
                    'Notes and References',
                    'notes',
                    'references',
                    active=False,
                    css_id="persPers_notes_refs")))


class PersonInstitutionForm(forms.ModelForm):
    institution = forms.CharField(
        label='Institution',
        widget=al.TextWidget('InstitutionAutocomplete'))
    institution_uri = forms.CharField(required=False, widget=forms.HiddenInput())
    person = forms.CharField(label='Person', widget=al.TextWidget('PersonAutocomplete'))
    person_uri = forms.CharField(required=False, widget=forms.HiddenInput())
    #relation_type = forms.CharField(label='relation Type', widget=al.TextWidget('VCPersonInstitutionAutocomplete'))

    class Meta:
        model = PersonInstitution
        fields = ['relation_type', 'person', 'institution', 'start_date_written', 'end_date_written', 'references', 'notes']
        labels = {
            'start_date_written': _('Start'),
            'end_date_written': _('End'),
            'relation_type': _('Type'),
        }
        widgets = {
            'relation_type': al.ChoiceWidget('VCPersonInstitutionAutocomplete')
        }

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        if instance:
            x = PersonInstitution.objects.get(pk=instance)
            x.relation_type = cd['relation_type']
            x.start_date_written = cd['start_date_written']
            x.end_date_written = cd['end_date_written']
            x.notes = cd['notes']
            x.references = cd['references']
        else:
            x = super(PersonInstitutionForm, self).save(commit=False)
        if 'institution' in cd.keys():
            x.related_person = site_instance
            institution = Institution.get_or_create_uri(cd['institution_uri'])
            if not institution:
                institution = GenericRDFParser(cd['institution_uri'], 'Institution').get_or_create()
            x.related_institution = institution
        elif 'person' in cd.keys():
            x.related_institution = site_instance
            person = Person.get_or_create_uri(cd['person_uri'])
            if not person:
                person = GenericRDFParser(cd['person_uri'], 'Person').get_or_create()
            x.related_person = person
        x.save()
        return x

    def __init__(self, siteID=None, *args, **kwargs):
        entity_type = kwargs.pop('entity_type', False)
        self.request = kwargs.pop('request', False)
        if not hasattr(self, 'request'):
            self.request = kwargs.pop('request', False)
        super(PersonInstitutionForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.id:
            self.fields['institution'].initial = instance.related_institution.name
            self.fields['institution_uri'].initial = Uri.objects.filter(entity=instance.related_institution)[0]
        self.fields['relation_type'].required = True
        self.helper = FormHelper()
        self.helper.form_class = 'PersonInstitutionForm'
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'relation_type',
            'start_date_written',
            'end_date_written',
            Accordion(
                AccordionGroup(
                    'Notes and References',
                    'notes',
                    'references',
                    active=False,
                    css_id="persInst_notes_refs")))
        if entity_type == Institution:
            choices = []
            for x in PersonInstitutionRelation.objects.all():
                choices.append((x.pk, x.name_reverse))

            self.fields.pop('institution')
            self.fields.pop('institution_uri')
            if instance and instance.id:
                self.fields['person'].initial = instance.related_person
                self.fields['person_uri'].initial = Uri.objects.filter(entity=instance.related_person)[0]
                self.fields['relation_type'].widget = al.ChoiceWidget('VCPersonInstitutionReverseAutocomplete',
                                                                      extra_context={
                                                                          'values': [instance.relation_type.pk],
                                                                          'choices': [
                                                                              instance.relation_type.label_reverse]}
                                                                      )
            else:
                self.fields['relation_type'].widget = al.ChoiceWidget('VCPersonInstitutionReverseAutocomplete')
            self.helper.layout.insert(1, 'person')
            self.helper.layout.insert(2, 'person_uri')
        else:
            self.fields.pop('person')
            self.fields.pop('person_uri')
            if instance and instance.id:
                self.fields['institution'].initial = instance.related_institution.name
                self.fields['institution_uri'].initial = Uri.objects.filter(entity=instance.related_institution)[0]
                self.fields['relation_type'].widget = al.ChoiceWidget('VCPersonInstitutionReverseAutocomplete',
                                                                      extra_context={
                                                                          'values': [instance.relation_type.pk],
                                                                          'choices': [
                                                                              instance.relation_type.label]}
                                                                      )
            self.helper.layout.insert(1, 'institution')
            self.helper.layout.insert(2, 'institution_uri')


class PersonEventForm(forms.ModelForm):
    event = forms.CharField(
        label='Event',
        widget=al.TextWidget('EventAutocomplete'))
    event_uri = forms.CharField(required=False, widget=forms.HiddenInput())
    person = forms.CharField(label='Person', widget=al.TextWidget('PersonAutocomplete'))
    person_uri = forms.CharField(required=False, widget=forms.HiddenInput())
    #relation_type = forms.CharField(label='relation Type', widget=al.TextWidget('VCPersonInstitutionAutocomplete'))

    class Meta:
        model = PersonEvent
        fields = ['relation_type', 'person', 'event', 'start_date_written', 'end_date_written', 'references', 'notes']
        labels = {
            'start_date_written': _('Start'),
            'end_date_written': _('End'),
            'relation_type': _('Type'),
        }
        widgets = {
            'relation_type': al.ChoiceWidget('VCPersonEventAutocomplete')
        }

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        if instance:
            x = PersonEvent.objects.get(pk=instance)
            x.relation_type = cd['relation_type']
            x.start_date_written = cd['start_date_written']
            x.end_date_written = cd['end_date_written']
            x.notes = cd['notes']
            x.references = cd['references']
        else:
            x = super(PersonEventForm, self).save(commit=False)
        if 'event' in cd.keys():
            x.related_person = site_instance
            event = Event.get_or_create_uri(cd['event_uri'])
            if not event:
                event = GenericRDFParser(cd['event_uri'], 'Event').get_or_create()
            x.related_event = event
        elif 'person' in cd.keys():
            x.related_event = site_instance
            person = Person.get_or_create_uri(cd['person_uri'])
            if not person:
                person = GenericRDFParser(cd['person_uri'], 'Person').get_or_create()
            x.related_person = person
        x.save()
        return x

    def __init__(self, siteID=None, *args, **kwargs):
        entity_type = kwargs.pop('entity_type', False)
        self.request = kwargs.pop('request', False)
        if not hasattr(self, 'request'):
            self.request = kwargs.pop('request', False)
        super(PersonEventForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.id:
            self.fields['event'].initial = instance.related_event.name
            self.fields['event_uri'].initial = Uri.objects.filter(entity=instance.related_event)[0]
        self.fields['relation_type'].required = True
        self.helper = FormHelper()
        self.helper.form_class = 'PersonEventForm'
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'relation_type',
            'start_date_written',
            'end_date_written',
            Accordion(
                AccordionGroup(
                    'Notes and References',
                    'notes',
                    'references',
                    active=False,
                    css_id="persEvent_notes_refs")))
        if entity_type == Event:
            choices = []
            for x in PersonEventRelation.objects.all():
                choices.append((x.pk, x.name_reverse))
            self.fields['relation_type'].choices = choices
            self.fields.pop('event')
            self.fields.pop('event_uri')
            if instance and instance.id:
                self.fields['person'].initial = instance.related_person
                self.fields['person_uri'].initial = Uri.objects.filter(entity=instance.related_person)[0]
                self.fields['relation_type'].widget = al.ChoiceWidget(
                    'VCPersonEventReverseAutocomplete',
                    extra_context={'values': [instance.relation_type.pk],
                                   'choices': [instance.relation_type.label_reverse]})
            else:
                self.fields['relation_type'].widget = al.ChoiceWidget('VCPersonEventReverseAutocomplete')
            self.helper.layout.insert(1, 'person')
            self.helper.layout.insert(2, 'person_uri')
        else:
            self.fields.pop('person')
            self.fields.pop('person_uri')
            if instance and instance.id:
                self.fields['event'].initial = instance.related_event.name
                self.fields['event_uri'].initial = Uri.objects.filter(entity=instance.related_event)[0]
                self.fields['relation_type'].widget = al.ChoiceWidget(
                    'VCPersonEventReverseAutocomplete',
                    extra_context={'values': [instance.relation_type.pk],
                                   'choices': [instance.relation_type.label]})
            self.helper.layout.insert(1, 'event')
            self.helper.layout.insert(2, 'event_uri')


class PersonWorkForm(forms.ModelForm):
    work = forms.CharField(
        label='Work',
        widget=al.TextWidget('WorkAutocomplete'))
    work_uri = forms.CharField(required=False, widget=forms.HiddenInput())
    person = forms.CharField(label='Person', widget=al.TextWidget('PersonAutocomplete'))
    person_uri = forms.CharField(required=False, widget=forms.HiddenInput())
    #relation_type = forms.CharField(label='relation Type', widget=al.TextWidget('VCPersonInstitutionAutocomplete'))

    class Meta:
        model = PersonWork
        fields = ['relation_type', 'person', 'work', 'start_date_written', 'end_date_written', 'references', 'notes']
        labels = {
            'start_date_written': _('Start'),
            'end_date_written': _('End'),
            'relation_type': _('Type'),
        }
        widgets = {
            'relation_type': al.ChoiceWidget('VCPersonWorkAutocomplete')
        }

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        if instance:
            x = PersonWork.objects.get(pk=instance)
            x.relation_type = cd['relation_type']
            x.start_date_written = cd['start_date_written']
            x.end_date_written = cd['end_date_written']
            x.notes = cd['notes']
            x.references = cd['references']
        else:
            x = super(PersonWorkForm, self).save(commit=False)
        if 'work' in cd.keys():
            x.related_person = site_instance
            work = Work.get_or_create_uri(cd['work_uri'])
            if not work:
                work = GenericRDFParser(cd['work_uri'], 'Work')  # TODO: Create work entries for GND parser
            x.related_work = work
        elif 'person' in cd.keys():
            x.related_work = site_instance
            person = Person.get_or_create_uri(cd['person_uri'])
            if not person:
                person = GenericRDFParser(cd['person_uri'], 'Person').get_or_create()
            x.related_person = person
        x.save()
        return x

    def __init__(self, siteID=None, *args, **kwargs):
        entity_type = kwargs.pop('entity_type', False)
        self.request = kwargs.pop('request', False)
        if not hasattr(self, 'request'):
            self.request = kwargs.pop('request', False)
        super(PersonWorkForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.id:
            self.fields['work'].initial = instance.related_work.name
            self.fields['work_uri'].initial = Uri.objects.filter(entity=instance.related_work)[0]
        self.fields['relation_type'].required = True
        self.helper = FormHelper()
        self.helper.form_class = 'PersonWorkForm'
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'relation_type',
            'start_date_written',
            'end_date_written',
            Accordion(
                AccordionGroup(
                    'Notes and References',
                    'notes',
                    'references',
                    active=False,
                    css_id="persWork_notes_refs")))
        if entity_type == Work:
            self.fields.pop('work')
            self.fields.pop('work_uri')
            if instance and instance.id:
                self.fields['person'].initial = instance.related_person
                self.fields['person_uri'].initial = Uri.objects.filter(entity=instance.related_person)[0]
                self.fields['relation_type'].widget = al.ChoiceWidget('VCPersonWorkReverseAutocomplete',
                                                                      extra_context={
                                                                          'values': [instance.relation_type.pk],
                                                                          'choices': [
                                                                              instance.relation_type.label_reverse]}
                                                                      )
            else:
                self.fields['relation_type'].widget = al.ChoiceWidget('VCPersonWorkReverseAutocomplete')
            self.helper.layout.insert(1, 'person')
            self.helper.layout.insert(2, 'person_uri')
        else:
            self.fields.pop('person')
            self.fields.pop('person_uri')
            if instance and instance.id:
                self.fields['work'].initial = instance.related_work.name
                self.fields['work_uri'].initial = Uri.objects.filter(entity=instance.related_work)[0]
                self.fields['relation_type'].widget = al.ChoiceWidget('VCPersonWorkReverseAutocomplete',
                                                                      extra_context={
                                                                          'values': [instance.relation_type.pk],
                                                                          'choices': [
                                                                              instance.relation_type.label]}
                                                                      )
            self.helper.layout.insert(1, 'work')
            self.helper.layout.insert(2, 'work_uri')

class PersonLabelForm(EntityLabelForm):
    pass

##############################################
# Institutions
##############################################


class InstitutionPlaceForm(forms.ModelForm):
    place = forms.CharField(label='Ort', widget=al.TextWidget('OrtAutocomplete'))
    place_uri = forms.CharField(required=False, widget=forms.HiddenInput())
    institution = forms.CharField(label='Institution', widget=al.TextWidget('InstitutionAutocomplete'))
    institution_uri = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = InstitutionPlace
        fields = ['relation_type', 'start_date_written', 'end_date_written', 'references', 'notes']
        labels = {
            'start_date_written': _('Start'),
            'end_date_written': _('End'),
            'relation_type': _('Type')
        }
        widgets = {'relation_type': al.ChoiceWidget('VCInstitutionPlaceAutocomplete')}

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        if instance:
            x = InstitutionPlace.objects.get(pk=instance)
            x.relation_type = cd['relation_type']
            x.start_date_written = cd['start_date_written']
            x.end_date_written = cd['end_date_written']
            x.notes = cd['notes']
            x.references = cd['references']
        else:
            x = super(InstitutionPlaceForm, self).save(commit=False)
        if 'place' in cd.keys():
            x.related_institution = site_instance
            place = GenericRDFParser(cd['place_uri'], 'Place').get_or_create()
            x.related_place = place
        elif 'institution' in cd.keys():
            x.related_place = site_instance
            institution = Institution.get_or_create_uri(cd['institution_uri'])
            if not institution:
                institution = GenericRDFParser(cd['institution_uri'], 'Institution').get_or_create()
            x.related_institution = institution
        x.save()
        return x

    def __init__(self, siteID=None, *args, **kwargs):
        entity_type = kwargs.pop('entity_type', False)
        self.request = kwargs.pop('request', False)
        super(InstitutionPlaceForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['relation_type'].required = True
        self.helper = FormHelper()
        self.helper.form_class = 'InstitutionPlaceForm'
        self.helper.form_tag = False
        if entity_type == Place:
            self.fields.pop('place')
            self.fields.pop('place_uri')
            if instance and instance.id:
                self.fields['institution'].initial = instance.related_institution.name
                self.fields['institution_uri'].initial = Uri.objects.filter(entity=instance.related_institution)[0]
                self.fields['relation_type'].widget = al.ChoiceWidget(
                    'VCInstitutionPlaceReverseAutocomplete',
                    extra_context={'values': [instance.relation_type.pk],
                                   'choices': [instance.relation_type.label_reverse]})
            else:
                self.fields['relation_type'].widget = al.ChoiceWidget('VCInstitutionPlaceReverseAutocomplete')
            self.helper.layout = Layout(
                    'relation_type',
                    'institution',
                    'institution_uri',
                    'start_date_written',
                    'end_date_written',
                    Accordion(
                        AccordionGroup(
                            'Notes and References',
                            'notes',
                            'references',
                            active=False,
                            css_id="instPlace_notes_refs")))
        else:
            self.fields.pop('institution')
            self.fields.pop('institution_uri')
            if instance and instance.id:
                self.fields['place'].initial = instance.related_place.name
                self.fields['place_uri'].initial = Uri.objects.filter(entity=instance.related_place)[0]
                self.fields['relation_type'].widget = al.ChoiceWidget(
                    'VCInstitutionPlaceReverseAutocomplete',
                    extra_context={'values': [instance.relation_type.pk],
                                   'choices': [instance.relation_type.label]})
            self.helper.layout = Layout(
                'relation_type',
                'place',
                'place_uri',
                'start_date_written',
                'end_date_written',
                Accordion(
                    AccordionGroup(
                        'Notes and References',
                        'notes',
                        'references',
                        active=False,
                        css_id="instPlace_notes_refs")))


class InstitutionEventForm(forms.ModelForm):
    event = forms.CharField(label='Event', widget=al.TextWidget('EventAutocomplete'))
    event_uri = forms.CharField(required=False, widget=forms.HiddenInput())
    institution = forms.CharField(label='Institution', widget=al.TextWidget('InstitutionAutocomplete'))
    institution_uri = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = InstitutionEvent
        fields = ['relation_type', 'start_date_written', 'end_date_written', 'references', 'notes']
        labels = {
            'start_date_written': _('Start'),
            'end_date_written': _('End'),
            'relation_type': _('Type')
        }
        widgets = {
            'relation_type': al.ChoiceWidget('VCInstitutionEventAutocomplete')
        }

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        if instance:
            x = InstitutionEvent.objects.get(pk=instance)
            x.relation_type = cd['relation_type']
            x.start_date_written = cd['start_date_written']
            x.end_date_written = cd['end_date_written']
            x.notes = cd['notes']
            x.references = cd['references']
        else:
            x = super(InstitutionEventForm, self).save(commit=False)
        if 'event' in cd.keys():
            x.related_institution = site_instance
            event = Event.get_or_create_uri(cd['event_uri'].strip())
            if not event:
                event = GenericRDFParser(cd['event_uri'], 'Event').get_or_create()
            x.related_event = event
        elif 'institution' in cd.keys():
            x.related_event = site_instance
            institution = Institution.get_or_create_uri(cd['institution_uri'].strip())
            if not institution:
                institution = GenericRDFParser(cd['institution_uri'], 'Institution').get_or_create()
            x.related_institution = institution
        x.save()
        return x

    def __init__(self, siteID=None, *args, **kwargs):
        entity_type = kwargs.pop('entity_type', False)
        self.request = kwargs.pop('request', False)
        super(InstitutionEventForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['relation_type'].required = True
        self.helper = FormHelper()
        self.helper.form_class = 'InstitutionEventForm'
        self.helper.form_tag = False
        if entity_type == Event:
            choices = []
            self.fields.pop('event')
            self.fields.pop('event_uri')
            for x in InstitutionEventRelation.objects.all():
                choices.append((x.pk, x.name_reverse))
            self.fields['relation_type'].choices = choices
            if instance and instance.id:
                self.fields['institution'].initial = instance.related_institution.name
                self.fields['institution_uri'].initial = Uri.objects.filter(entity=instance.related_institution)[0]
                self.fields['relation_type'].widget = al.ChoiceWidget(
                    'VCInstitutionEventReverseAutocomplete',
                    extra_context={'values': [instance.relation_type.pk],
                                   'choices': [instance.relation_type.label_reverse]})
            else:
                self.fields['relation_type'].widget = al.ChoiceWidget('VCInstitutionEventReverseAutocomplete')
            self.helper.layout = Layout(
                    'relation_type',
                    'institution',
                    'institution_uri',
                    'start_date_written',
                    'end_date_written',
                    Accordion(
                        AccordionGroup(
                            'Notes and References',
                            'notes',
                            'references',
                            active=False,
                            css_id="instEvent_notes_refs")))
        else:
            self.fields.pop('institution')
            self.fields.pop('institution_uri')
            if instance and instance.id:
                self.fields['event'].initial = instance.related_event.name
                self.fields['event_uri'].initial = Uri.objects.filter(entity=instance.related_event)[0]
                self.fields['relation_type'].widget = al.ChoiceWidget(
                    'VCInstitutionEventReverseAutocomplete',
                    extra_context={'values': [instance.relation_type.pk],
                                   'choices': [instance.relation_type.label]})
            self.helper.layout = Layout(
                'relation_type',
                'event',
                'event_uri',
                'start_date_written',
                'end_date_written',
                Accordion(
                    AccordionGroup(
                        'Notes and References',
                        'notes',
                        'references',
                        active=False,
                        css_id="instEvent_notes_refs")))


class InstitutionWorkForm(forms.ModelForm):
    work = forms.CharField(label='Work', widget=al.TextWidget('WorkAutocomplete'))
    work_uri = forms.CharField(required=False, widget=forms.HiddenInput())
    institution = forms.CharField(label='Institution', widget=al.TextWidget('InstitutionAutocomplete'))
    institution_uri = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = InstitutionWork
        fields = ['relation_type', 'start_date_written', 'end_date_written', 'references', 'notes']
        labels = {
            'start_date_written': _('Start'),
            'end_date_written': _('End'),
            'relation_type': _('Type')
        }
        widgets = {
            'relation_type': al.ChoiceWidget('VCInstitutionWorkAutocomplete')
        }

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        if instance:
            x = InstitutionWork.objects.get(pk=instance)
            x.relation_type = cd['relation_type']
            x.start_date_written = cd['start_date_written']
            x.end_date_written = cd['end_date_written']
            x.notes = cd['notes']
            x.references = cd['references']
        else:
            x = super(InstitutionWorkForm, self).save(commit=False)
        if 'work' in cd.keys():
            x.related_institution = site_instance
            work = Work.get_or_create_uri(cd['work_uri'].strip())
            if not work:
                work = GenericRDFParser(cd['work_uri'], 'Work').get_or_create()
            x.related_work = work
        elif 'institution' in cd.keys():
            x.related_work = site_instance
            institution = Institution.get_or_create_uri(cd['institution_uri'].strip())
            if not institution:
                institution = GenericRDFParser(cd['institution_uri'], 'Institution').get_or_create()
            x.related_institution = institution
        x.save()
        return x

    def __init__(self, siteID=None, *args, **kwargs):
        entity_type = kwargs.pop('entity_type', False)
        self.request = kwargs.pop('request', False)
        super(InstitutionWorkForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['relation_type'].required = True
        self.helper = FormHelper()
        self.helper.form_class = 'InstitutionWorkForm'
        self.helper.form_tag = False
        if entity_type == Work:
            choices = []
            self.fields.pop('work')
            self.fields.pop('work_uri')
            if instance and instance.id:
                self.fields['institution'].initial = instance.related_institution.name
                self.fields['institution_uri'].initial = Uri.objects.filter(entity=instance.related_institution)[0]
                self.fields['relation_type'].widget = al.ChoiceWidget(
                    'VCInstitutionWorkReverseAutocomplete',
                    extra_context={'values': [instance.relation_type.pk],
                                   'choices': [instance.relation_type.label_reverse]})
            else:
                self.fields['relation_type'].widget = al.ChoiceWidget('VCInstitutionWorkReverseAutocomplete')
            self.helper.layout = Layout(
                    'relation_type',
                    'institution',
                    'institution_uri',
                    'start_date_written',
                    'end_date_written',
                    Accordion(
                        AccordionGroup(
                            'Notes and References',
                            'notes',
                            'references',
                            active=False,
                            css_id="instWork_notes_refs")))
        else:
            self.fields.pop('institution')
            self.fields.pop('institution_uri')
            if instance and instance.id:
                self.fields['work'].initial = instance.related_work.name
                self.fields['work_uri'].initial = Uri.objects.filter(entity=instance.related_work)[0]
                self.fields['relation_type'].widget = al.ChoiceWidget(
                    'VCInstitutionWorkReverseAutocomplete',
                    extra_context={'values': [instance.relation_type.pk],
                                   'choices': [instance.relation_type.label]})
            self.helper.layout = Layout(
                'relation_type',
                'work',
                'work_uri',
                'start_date_written',
                'end_date_written',
                Accordion(
                    AccordionGroup(
                        'Notes and References',
                        'notes',
                        'references',
                        active=False,
                        css_id="instWork_notes_refs")))


class InstitutionInstitutionForm(forms.ModelForm):
    institution = forms.CharField(label='Institution', widget=al.TextWidget('InstitutionAutocomplete'))
    institution_uri = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = InstitutionInstitution
        fields = ['relation_type', 'institution', 'start_date_written', 'end_date_written', 'references', 'notes']
        labels = {
            'start_date_written': _('Start'),
            'end_date_written': _('End'),
            'relation_type': _('Art'),
        }
        widgets = {
            'relation_type': al.ChoiceWidget('VCInstitutionInstitutionAutocomplete')
        }

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        if instance:
            x = InstitutionInstitution.objects.select_related(
                'related_institutionA__tempentityclass_ptr__uri',
                'related_institutionB__tempentityclass_ptr__uri').get(pk=instance)
            x.start_date_written = cd['start_date_written']
            x.end_date_written = cd['end_date_written']
            x.relation_type = cd['relation_type']
            x.notes = cd['notes']
            x.references = cd['references']
            if site_instance == x.related_institutionB:
                if x.related_institutionA.uri_set.filter(uri=cd['institution_uri']).count() == 0:
                    institutionA = Institution.get_or_create_uri(cd['institution_uri'])
                    x.related_institutionA = institutionA
        else:
            x = super(InstitutionInstitutionForm, self).save(commit=False)
            x.related_institutionA = site_instance
            institutionB = Institution.get_or_create_uri(cd['institution_uri'])
            if not institutionB:
                institutionB = GenericRDFParser(['institution_uri'], 'Institution').get_or_create()
            x.related_institutionB = institutionB
        x.save()
        return x

    def __init__(self, siteID=None, *args, **kwargs):
        entity_type = kwargs.pop('entity_type', False)
        self.request = kwargs.pop('request', False)
        super(InstitutionInstitutionForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.id:
            if siteID:
                siteID = Institution.objects.get(pk=siteID)
                if siteID == instance.related_institutionB:
                    rel_inst = instance.related_institutionA
                    self.fields['relation_type'].widget = al.ChoiceWidget(
                        'VCInstitutionInstitutionReverseAutocomplete',
                        extra_context={'values': [instance.relation_type.pk],
                                       'choices': [instance.relation_type.label_reverse]})
                else:
                    rel_inst = instance.related_institutionB
            self.fields['institution'].initial = rel_inst.name
            try:
                self.fields['institution_uri'].initial = Uri.objects.filter(
                    entity=rel_inst)[0]
            except:
                pass
        self.fields['relation_type'].required = True
        self.helper = FormHelper()
        self.helper.form_class = 'InstitutionInstitutionForm'
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'relation_type',
            'institution',
            'institution_uri',
            'start_date_written',
            'end_date_written',
            Accordion(
                AccordionGroup(
                    'Notes and References',
                    'notes',
                    'references',
                    active=False,
                    css_id="instInst_notes_refs")))


class InstitutionPersonForm(forms.ModelForm):
    person = forms.CharField(
        label='Person',
        widget=al.TextWidget('PersonAutocomplete'),
        )
    person_uri = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = PersonInstitution
        fields = ['relation_type', 'start_date_written', 'end_date_written', 'references', 'notes']
        labels = {
            'start_date_written': _('Start'),
            'end_date_written': _('End'),
            'relation_type': _('Type'),
            'related_person': _('Person')
        }
        widgets = {
            'related_person': al.ChoiceWidget('PersonAutocomplete')
        }

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        if instance:
            x = PersonInstitution.objects.get(pk=instance)
            x.relation_type = cd['relation_type']
            x.start_date_written = cd['start_date_written']
            x.end_date_written = cd['end_date_written']
            x.notes = cd['notes']
            x.references = cd['references']
        else:
            x = super(InstitutionPersonForm, self).save(commit=False)
            x.related_institution = site_instance
        person = Person.get_or_create_uri(cd['person_uri'])
        if not person:
            person = GenericRDFParser(cd['person_uri'], 'Person').get_or_create()
        x.related_person = person
        x.save()
        return x

    def __init__(self, siteID=None, *args, **kwargs):
        self.request = kwargs.pop('request', False)
        super(InstitutionPersonForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.id:
            self.fields['person'].initial = instance.related_person.name+", "+instance.related_person.first_name
            self.fields['person_uri'].initial = Uri.objects.filter(entity=instance.related_person)[0]
        self.fields['relation_type'].required = True
        self.helper = FormHelper()
        self.helper.form_class = 'InstitutionPersonForm'
        self.helper.form_tag = False


class InstitutionLabelForm(EntityLabelForm):
    pass


##############################################
# Places
##############################################


class PlaceEventForm(forms.ModelForm):
    event = forms.CharField(label='Event', widget=al.TextWidget('EventAutocomplete'))
    event_uri = forms.CharField(required=False, widget=forms.HiddenInput())
    place = forms.CharField(label='Place', widget=al.TextWidget('OrtAutocomplete'))
    place_uri = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = PlaceEvent
        fields = ['relation_type', 'start_date_written', 'end_date_written', 'references', 'notes']
        labels = {
            'start_date_written': _('Start'),
            'end_date_written': _('End'),
            'relation_type': _('Type')
        }
        widgets = {
            'relation_type': al.ChoiceWidget('VCPlaceEventAutocomplete')
        }

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        if instance:
            x = PlaceEvent.objects.get(pk=instance)
            x.relation_type = cd['relation_type']
            x.start_date_written = cd['start_date_written']
            x.end_date_written = cd['end_date_written']
            x.notes = cd['notes']
            x.references = cd['references']
        else:
            x = super(PlaceEventForm, self).save(commit=False)
        if 'event' in cd.keys():
            x.related_place = site_instance
            event = Event.get_or_create_uri(cd['event_uri'])
            if not event:
                event = GenericRDFParser(cd['event_uri'], 'Event').get_or_create()
            x.related_event = event
        elif 'place' in cd.keys():
            x.related_event = site_instance
            place = Place.get_or_create_uri(cd['place_uri'])
            if not place:
                place = GenericRDFParser(cd['place_uri'], 'Place').get_or_create()
            x.related_place = place
        x.save()
        return x

    def __init__(self, siteID=None, *args, **kwargs):
        entity_type = kwargs.pop('entity_type', False)
        self.request = kwargs.pop('request', False)
        super(PlaceEventForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['relation_type'].required = True
        self.helper = FormHelper()
        self.helper.form_class = 'PlaceEventForm'
        self.helper.form_tag = False
        if entity_type == Event:
            self.fields.pop('event')
            self.fields.pop('event_uri')

            if instance and instance.id:
                self.fields['place'].initial = instance.related_place.name
                self.fields['place_uri'].initial = Uri.objects.filter(entity=instance.related_place)[0]
                self.fields['relation_type'].widget = al.ChoiceWidget(
                    'VCPlaceEventReverseAutocomplete',
                    extra_context={'values': [instance.relation_type.pk],
                                   'choices': [instance.relation_type.label_reverse]})
            else:
                self.fields['relation_type'].widget = al.ChoiceWidget('VCPlaceEventReverseAutocomplete')
            self.helper.layout = Layout(
                    'relation_type',
                    'place',
                    'place_uri',
                    'start_date_written',
                    'end_date_written',
                    Accordion(
                        AccordionGroup(
                            'Notes and References',
                            'notes',
                            'references',
                            active=False,
                            css_id="placeEvent_notes_refs")))
        else:
            self.fields.pop('place')
            self.fields.pop('place_uri')
            if instance and instance.id:
                self.fields['event'].initial = instance.related_event.name
                self.fields['event_uri'].initial = Uri.objects.filter(entity=instance.related_event)[0]
                self.fields['relation_type'].widget = al.ChoiceWidget(
                    'VCPlaceEventReverseAutocomplete',
                    extra_context={'values': [instance.relation_type.pk],
                                   'choices': [instance.relation_type.label]})
            self.helper.layout = Layout(
                'relation_type',
                'event',
                'event_uri',
                'start_date_written',
                'end_date_written',
                Accordion(
                    AccordionGroup(
                        'Notes and References',
                        'notes',
                        'references',
                        active=False,
                        css_id="placeEvent_notes_refs")))


class PlaceWorkForm(forms.ModelForm):
    work = forms.CharField(label='Work', widget=al.TextWidget('WorkAutocomplete'))
    work_uri = forms.CharField(required=False, widget=forms.HiddenInput())
    place = forms.CharField(label='Place', widget=al.TextWidget('OrtAutocomplete'))
    place_uri = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = PlaceWork
        fields = ['relation_type', 'start_date_written', 'end_date_written', 'references', 'notes']
        labels = {
            'start_date_written': _('Start'),
            'end_date_written': _('End'),
            'relation_type': _('Type')
        }
        widgets = {
            'relation_type': al.ChoiceWidget('VCPlaceWorkAutocomplete')
        }

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        if instance:
            x = PlaceWork.objects.get(pk=instance)
            x.relation_type = cd['relation_type']
            x.start_date_written = cd['start_date_written']
            x.end_date_written = cd['end_date_written']
            x.notes = cd['notes']
            x.references = cd['references']
        else:
            x = super(PlaceWorkForm, self).save(commit=False)
        if 'work' in cd.keys():
            x.related_place = site_instance
            work = Work.get_or_create_uri(cd['work_uri'])
            if not work:
                work = GenericRDFParser(cd['work_uri'], 'Work').get_or_create()
            x.related_work = work
        elif 'place' in cd.keys():
            x.related_work = site_instance
            place = Place.get_or_create_uri(cd['place_uri'])
            if not place:
                place = GenericRDFParser(cd['place_uri'], 'Place').get_or_create()
            x.related_place = place
        x.save()
        return x

    def __init__(self, siteID=None, *args, **kwargs):
        entity_type = kwargs.pop('entity_type', False)
        self.request = kwargs.pop('request', False)
        super(PlaceWorkForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['relation_type'].required = True
        self.helper = FormHelper()
        self.helper.form_class = 'PlaceWorkForm'
        self.helper.form_tag = False
        if entity_type == Work:
            self.fields.pop('work')
            self.fields.pop('work_uri')

            if instance and instance.id:
                self.fields['place'].initial = instance.related_place.name
                self.fields['place_uri'].initial = Uri.objects.filter(entity=instance.related_place)[0]
                self.fields['relation_type'].widget = al.ChoiceWidget(
                    'VCPlaceWorkReverseAutocomplete',
                    extra_context={'values': [instance.relation_type.pk],
                                   'choices': [instance.relation_type.label_reverse]})
            else:
                self.fields['relation_type'].widget = al.ChoiceWidget('VCPlaceWorkReverseAutocomplete')
            self.helper.layout = Layout(
                'relation_type',
                'place',
                'place_uri',
                'start_date_written',
                'end_date_written',
                Accordion(
                    AccordionGroup(
                        'Notes and References',
                        'notes',
                        'references',
                        active=False,
                        css_id="placeWork_notes_refs")))
        else:
            self.fields.pop('place')
            self.fields.pop('place_uri')
            if instance and instance.id:
                self.fields['work'].initial = instance.related_work.name
                self.fields['work_uri'].initial = Uri.objects.filter(entity=instance.related_work)[0]
                self.fields['relation_type'].widget = al.ChoiceWidget(
                    'VCPlaceWorkReverseAutocomplete',
                    extra_context={'values': [instance.relation_type.pk],
                                   'choices': [instance.relation_type.label]})
            self.helper.layout = Layout(
                'relation_type',
                'work',
                'work_uri',
                'start_date_written',
                'end_date_written',
                Accordion(
                    AccordionGroup(
                        'Notes and References',
                        'notes',
                        'references',
                        active=False,
                        css_id="placeWork_notes_refs")))


class PlacePlaceForm(forms.ModelForm):
    place = forms.CharField(label='Place', widget=al.TextWidget('OrtAutocomplete'))
    place_uri = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = PlacePlace
        fields = ['relation_type', 'place', 'start_date_written', 'end_date_written', 'references', 'notes']
        labels = {
            'start_date_written': _('Start'),
            'end_date_written': _('End'),
            'relation_type': _('Art'),
        }
        widgets = {
            'relation_type': al.ChoiceWidget('VCPlacePlaceAutocomplete')
        }

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        if instance:
            x = PlacePlace.objects.select_related(
                'related_placeA__tempentityclass_ptr__uri',
                'related_placeB__tempentityclass_ptr__uri').get(pk=instance)
            x.start_date_written = cd['start_date_written']
            x.end_date_written = cd['end_date_written']
            x.relation_type = cd['relation_type']
            x.notes = cd['notes']
            x.references = cd['references']
            if site_instance == x.related_placeB:
                if x.related_placeA.uri_set.filter(uri=cd['place_uri']).count() == 0:
                    placeA = GenericRDFParser(cd['place_uri'], 'Place').get_or_create()
                    x.related_placeA = placeA
        else:
            x = super(PlacePlaceForm, self).save(commit=False)
            x.related_placeA = site_instance
            placeB = GenericRDFParser(cd['place_uri'], 'Place').get_or_create()
            x.related_placeB = placeB
        x.save()
        return x

    def __init__(self, siteID=None, *args, **kwargs):
        entity_type = kwargs.pop('entity_type', False)
        self.request = kwargs.pop('request', False)
        if not hasattr(self, 'request'):
            self.request = kwargs.pop('request', False)
        super(PlacePlaceForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.id:
            if siteID:
                siteID = Place.objects.get(pk=siteID)
                if siteID == instance.related_placeB:
                    rel_place = instance.related_placeA
                    self.fields['relation_type'].widget = al.ChoiceWidget(
                        'VCPlacePlaceReverseAutocomplete',
                        extra_context={'values': [instance.relation_type.pk],
                                       'choices': [instance.relation_type.label_reverse]})
                else:
                    rel_place = instance.related_placeB
            self.fields['place'].initial = rel_place
            self.fields['place_uri'].initial = Uri.objects.filter(entity=rel_place)[0]
        self.fields['relation_type'].required = True
        self.helper = FormHelper()
        self.helper.form_class = 'PlacePlaceForm'
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'relation_type',
            'place',
            'place_uri',
            'start_date_written',
            'end_date_written',
            Accordion(
                AccordionGroup(
                    'Notes and References',
                    'notes',
                    'references',
                    active=False,
                    css_id="placePlace_notes_refs")))


##############################################
# Events
##############################################


class EventWorkForm(forms.ModelForm):
    work = forms.CharField(label='Work', widget=al.TextWidget('WorkAutocomplete'))
    work_uri = forms.CharField(required=False, widget=forms.HiddenInput())
    event = forms.CharField(label='Event', widget=al.TextWidget('EventAutocomplete'))
    event_uri = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = EventWork
        fields = ['relation_type', 'start_date_written', 'end_date_written', 'references', 'notes']
        labels = {
            'start_date_written': _('Start'),
            'end_date_written': _('End'),
            'relation_type': _('Type')
        }
        widgets = {
            'relation_type': al.ChoiceWidget('VCEventWorkAutocomplete')
        }

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        if instance:
            x = EventWork.objects.get(pk=instance)
            x.relation_type = cd['relation_type']
            x.start_date_written = cd['start_date_written']
            x.end_date_written = cd['end_date_written']
            x.notes = cd['notes']
            x.references = cd['references']
        else:
            x = super(EventWorkForm, self).save(commit=False)
        if 'work' in cd.keys():
            x.related_event = site_instance
            work = Work.get_or_create_uri(cd['work_uri'])
            if not work:
                work = GenericRDFParser(cd['work_uri'], 'Work').get_or_create()
            x.related_work = work
        elif 'event' in cd.keys():
            x.related_work = site_instance
            event = Event.get_or_create_uri(cd['event_uri'])
            if not event:
                event = GenericRDFParser(cd['event_uri'], 'Event').get_or_create()
            x.related_event = event
        x.save()
        return x

    def __init__(self, siteID=None, *args, **kwargs):
        entity_type = kwargs.pop('entity_type', False)
        self.request = kwargs.pop('request', False)
        super(EventWorkForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['relation_type'].required = True
        self.helper = FormHelper()
        self.helper.form_class = 'EventWorkForm'
        self.helper.form_tag = False
        if entity_type == Work:
            self.fields.pop('work')
            self.fields.pop('work_uri')

            if instance and instance.id:
                self.fields['event'].initial = instance.related_event.name
                self.fields['event_uri'].initial = Uri.objects.filter(entity=instance.related_event)[0]
                self.fields['relation_type'].widget = al.ChoiceWidget(
                    'VCEventWorkReverseAutocomplete',
                    extra_context={'values': [instance.relation_type.pk],
                                   'choices': [instance.relation_type.label_reverse]})
            else:
                self.fields['relation_type'].widget = al.ChoiceWidget('VCEventWorkReverseAutocomplete')
            self.helper.layout = Layout(
                'relation_type',
                'event',
                'event_uri',
                'start_date_written',
                'end_date_written',
                Accordion(
                    AccordionGroup(
                        'Notes and References',
                        'notes',
                        'references',
                        active=False,
                        css_id="eventWork_notes_refs")))
        else:
            self.fields.pop('event')
            self.fields.pop('event_uri')
            if instance and instance.id:
                self.fields['work'].initial = instance.related_work.name
                self.fields['work_uri'].initial = Uri.objects.filter(entity=instance.related_work)[0]
                self.fields['relation_type'].widget = al.ChoiceWidget(
                    'VCEventWorkReverseAutocomplete',
                    extra_context={'values': [instance.relation_type.pk],
                                   'choices': [instance.relation_type.label]})
            self.helper.layout = Layout(
                'relation_type',
                'work',
                'work_uri',
                'start_date_written',
                'end_date_written',
                Accordion(
                    AccordionGroup(
                        'Notes and References',
                        'notes',
                        'references',
                        active=False,
                        css_id="eventWork_notes_refs")))


class EventLabelForm(EntityLabelForm):
    pass


##############################################
# Entities Base Forms
#############################################

class PlaceEntityForm(forms.Form):
    place = forms.CharField(label='Place', widget=al.TextWidget('OrtAutocomplete'))
    place_uri = forms.CharField(required=False, widget=forms.HiddenInput())

    def save(self, *args, **kwargs):
        cd = self.cleaned_data
        pl = Place.get_or_create_uri(cd['place_uri'])
        if not pl:
            pl = GenericRDFParser(cd['place_uri'], 'Place').get_or_create()
        return pl

##############################################
# Highlighter
##############################################


class PlaceEntityHighlighterForm(forms.Form):
    place = forms.CharField(label='Place', widget=al.TextWidget('OrtAutocomplete'))
    place_uri = forms.CharField(required=False, widget=forms.HiddenInput())
    HL_start = forms.IntegerField(widget=forms.HiddenInput)
    HL_end = forms.IntegerField(widget=forms.HiddenInput)
    HL_text_id = forms.CharField(widget=forms.HiddenInput)

    def save(self, *args, **kwargs):
        cd = self.cleaned_data
        pl = Place.get_or_create_uri(cd['place_uri'])
        if not pl:
            pl = GenericRDFParser(cd['place_uri'], 'Place').get_or_create()
        txt = Text.objects.get(pk=cd['HL_text_id'][5:])
        a = Annotation(
            start=cd['HL_start'],
            end=cd['HL_end'],
            text=txt,
            user_added=self.request.user,
            annotation_project_id=int(self.request.session.get('annotation_project', 1)))
        a.save()
        a.entity_link.add(pl)
        return a

    def __init__(self, *args, **kwargs):
        entity_type = kwargs.pop('entity_type', False)
        self.request = kwargs.pop('request', False)
        super(PlaceEntityHighlighterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'PlaceEntityForm'
        self.helper.form_tag = False


class PersonPlaceHighlighterForm(PersonPlaceForm):
    HL_start = forms.IntegerField(widget=forms.HiddenInput)
    HL_end = forms.IntegerField(widget=forms.HiddenInput)
    HL_text_id = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        #self.request = kwargs.pop('request', False)
        super(PersonPlaceHighlighterForm, self).__init__(*args, **kwargs)
        self.helper.layout.pop(-1)
        self.helper.layout.extend([
            'HL_start',
            'HL_end',
            'HL_text_id',
            Accordion(
                 AccordionGroup(
                     'Notes and References',
                     'notes',
                     'references',
                     active=False,
                     css_id="persPlaceHL_notes_refs"))])

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        x = super(PersonPlaceHighlighterForm, self).save(site_instance, commit=True)
        txt = Text.objects.get(pk=cd['HL_text_id'][5:])
        a = Annotation(
            start=cd['HL_start'],
            end=cd['HL_end'],
            text=txt,
            user_added=self.request.user,
            annotation_project_id=int(self.request.session.get('annotation_project', 1)))
        a.save()
        a.entity_link.add(x)
        return x

    def get_text_id(self):
        return self.cleaned_data['HL_text_id'][5:]


class PersonInstitutionHighlighterForm(PersonInstitutionForm):
    HL_start = forms.IntegerField(widget=forms.HiddenInput)
    HL_end = forms.IntegerField(widget=forms.HiddenInput)
    HL_text_id = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        #self.request = kwargs.pop('request', False)
        super(PersonInstitutionHighlighterForm, self).__init__(*args, **kwargs)
        self.helper.layout.pop(-1)
        self.helper.layout.extend([
            'HL_start',
            'HL_end',
            'HL_text_id',
            Accordion(
                 AccordionGroup(
                     'Notes and References',
                     'notes',
                     'references',
                     active=False,
                     css_id="persInstHL_notes_refs"))])

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        x = super(PersonInstitutionHighlighterForm, self).save(site_instance, commit=True)
        txt = Text.objects.get(pk=cd['HL_text_id'][5:])
        a = Annotation(
            start=cd['HL_start'],
            end=cd['HL_end'],
            text=txt,
            user_added=self.request.user,
            annotation_project_id=int(self.request.session.get('annotation_project', 1)))
        a.save()
        a.entity_link.add(x)
        return x

    def get_text_id(self):
        return self.cleaned_data['HL_text_id'][5:]


class PersonPersonHighlighterForm(PersonPersonForm):
    HL_start = forms.IntegerField(widget=forms.HiddenInput)
    HL_end = forms.IntegerField(widget=forms.HiddenInput)
    HL_text_id = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        #self.request = kwargs.pop('request', False)
        super(PersonPersonHighlighterForm, self).__init__(*args, **kwargs)
        self.helper.layout.pop(-1)
        self.helper.layout.extend([
            'HL_start',
            'HL_end',
            'HL_text_id',
            Accordion(
                 AccordionGroup(
                     'Notes and References',
                     'notes',
                     'references',
                     active=False,
                     css_id="persPlaceHL_notes_refs"))])

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        x = super(PersonPersonHighlighterForm, self).save(site_instance, commit=True)
        txt = Text.objects.get(pk=cd['HL_text_id'][5:])
        a = Annotation(
            start=cd['HL_start'],
            end=cd['HL_end'],
            text=txt,
            user_added=self.request.user,
            annotation_project_id=int(self.request.session.get('annotation_project', 1)))
        a.save()
        a.entity_link.add(x)
        return x

    def get_text_id(self):
        return self.cleaned_data['HL_text_id'][5:]


class PlaceWorkHighlighterForm(PlaceWorkForm):
    HL_start = forms.IntegerField(widget=forms.HiddenInput)
    HL_end = forms.IntegerField(widget=forms.HiddenInput)
    HL_text_id = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        #self.request = kwargs.pop('request', False)
        super(PlaceWorkHighlighterForm, self).__init__(*args, **kwargs)
        self.helper.layout.pop(-1)
        self.helper.layout.extend([
            'HL_start',
            'HL_end',
            'HL_text_id',
            Accordion(
                 AccordionGroup(
                     'Notes and References',
                     'notes',
                     'references',
                     active=False,
                     css_id="placeWorkHL_notes_refs"))])

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        x = super(PlaceWorkHighlighterForm, self).save(site_instance, commit=True)
        txt = Text.objects.get(pk=cd['HL_text_id'][5:])
        a = Annotation(
            start=cd['HL_start'],
            end=cd['HL_end'],
            text=txt,
            user_added=self.request.user,
            annotation_project_id=int(self.request.session.get('annotation_project', 1)))
        a.save()
        a.entity_link.add(x)
        return x

    def get_text_id(self):
        return self.cleaned_data['HL_text_id'][5:]


class PersonWorkHighlighterForm(PersonWorkForm):
    HL_start = forms.IntegerField(widget=forms.HiddenInput)
    HL_end = forms.IntegerField(widget=forms.HiddenInput)
    HL_text_id = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        #self.request = kwargs.pop('request', False)
        super(PersonWorkHighlighterForm, self).__init__(*args, **kwargs)
        self.helper.layout.pop(-1)
        self.helper.layout.extend([
            'HL_start',
            'HL_end',
            'HL_text_id',
            Accordion(
                 AccordionGroup(
                     'Notes and References',
                     'notes',
                     'references',
                     active=False,
                     css_id="personWorkHL_notes_refs"))])

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        x = super(PersonWorkHighlighterForm, self).save(site_instance, commit=True)
        txt = Text.objects.get(pk=cd['HL_text_id'][5:])
        a = Annotation(
            start=cd['HL_start'],
            end=cd['HL_end'],
            text=txt,
            user_added=self.request.user,
            annotation_project_id=int(self.request.session.get('annotation_project', 1)))
        a.save()
        a.entity_link.add(x)
        return x

    def get_text_id(self):
        return self.cleaned_data['HL_text_id'][5:]


class InstitutionWorkHighlighterForm(InstitutionWorkForm):
    HL_start = forms.IntegerField(widget=forms.HiddenInput)
    HL_end = forms.IntegerField(widget=forms.HiddenInput)
    HL_text_id = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        #self.request = kwargs.pop('request', False)
        super(InstitutionWorkHighlighterForm, self).__init__(*args, **kwargs)
        self.helper.layout.pop(-1)
        self.helper.layout.extend([
            'HL_start',
            'HL_end',
            'HL_text_id',
            Accordion(
                 AccordionGroup(
                     'Notes and References',
                     'notes',
                     'references',
                     active=False,
                     css_id="institutionWorkHL_notes_refs"))])

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        x = super(InstitutionWorkHighlighterForm, self).save(site_instance, commit=True)
        txt = Text.objects.get(pk=cd['HL_text_id'][5:])
        a = Annotation(
            start=cd['HL_start'],
            end=cd['HL_end'],
            text=txt,
            user_added=self.request.user,
            annotation_project_id=int(self.request.session.get('annotation_project', 1)))
        a.save()
        a.entity_link.add(x)
        return x

    def get_text_id(self):
        return self.cleaned_data['HL_text_id'][5:]


class AddRelationHighlighterBaseForm(forms.Form):
    HL_start = forms.IntegerField(widget=forms.HiddenInput)
    HL_end = forms.IntegerField(widget=forms.HiddenInput)
    HL_text_id = forms.CharField(widget=forms.HiddenInput)
    RL_type = forms.CharField(widget=forms.HiddenInput)
    RL_pk = forms.IntegerField(widget=forms.HiddenInput)

    def save(self):
        cd = self.cleaned_data
        #x = super(AddRelationHighlighterBaseForm, self).save()
        txt = Text.objects.get(pk=cd['HL_text_id'][5:])
        ent = ContentType.objects.get(
            pk=cd['RL_type']).model_class().objects.get(pk=cd['RL_pk'])
        self.ann = Annotation(
            start=cd['HL_start'],
            end=cd['HL_end'],
            text=txt,
            user_added=self.request.user)
        self.ann.save()
        self.ann.entity_link.add(ent)
        return self.ann


class AddRelationHighlighterPersonForm(AddRelationHighlighterBaseForm):
    relation = forms.CharField(
        label='Relation',
        widget=al.TextWidget('AddRelationPersonHighlighterAutocomplete'),
        )

    def save(self, *args, **kwargs):
        cd = self.cleaned_data
        x = super().save()

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', False)
        self.entity_type = kwargs.pop('entity_type', False)
        super(AddRelationHighlighterPersonForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    def get_text_id(self):
        return self.cleaned_data['HL_text_id'][5:]

