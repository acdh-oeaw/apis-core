#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime

from django import forms
#import autocomplete_light.shortcuts as al
from django.utils.translation import ugettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.bootstrap import Accordion, AccordionGroup
from django.contrib.contenttypes.models import ContentType

from .models import (PersonPlace, PersonPerson, PersonInstitution,
                     InstitutionPlace, InstitutionInstitution, PersonEvent, InstitutionEvent,
                     PlaceEvent, PersonWork, InstitutionWork, PlaceWork, EventWork, PlacePlace)
from entities.models import Place, Institution, Person, Event, Work
from metainfo.models import Uri, Text
from vocabularies.models import (PersonInstitutionRelation, PersonPlaceRelation, InstitutionPlaceRelation,
                                 PersonEventRelation, InstitutionEventRelation, PlaceEventRelation,
                                 InstitutionInstitutionRelation, PersonPersonRelation)
from labels.models import Label
from highlighter.models import Annotation
from helper_functions.RDFparsers import GenericRDFParser
from dal import autocomplete


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


class PersonLabelForm(EntityLabelForm):
    pass

##############################################
# Institutions
##############################################


class InstitutionLabelForm(EntityLabelForm):
    pass


##############################################
# Places
##############################################




##############################################
# Events
##############################################





class EventLabelForm(EntityLabelForm):
    pass


##############################################
# Entities Base Forms
#############################################

class PlaceEntityForm(forms.Form):
    #place = forms.CharField(label='Place', widget=al.TextWidget('OrtAutocomplete'))
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
    place = forms.CharField(label='Place', widget=autocomplete.ModelSelect2(url='autocomplete/place'))
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
    # relation = forms.CharField(
    #     label='Relation',
    #     widget=al.TextWidget('AddRelationPersonHighlighterAutocomplete'),
    #     )

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

