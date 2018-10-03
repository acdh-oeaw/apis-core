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
from apis_core.apis_entities.models import Place, Institution, Person, Event, Work
from apis_core.apis_metainfo.models import Uri, Text
from apis_core.apis_vocabularies.models import (PersonInstitutionRelation, PersonPlaceRelation, InstitutionPlaceRelation,
                                 PersonEventRelation, InstitutionEventRelation, PlaceEventRelation,
                                 InstitutionInstitutionRelation, PersonPersonRelation)
from apis_core.apis_labels.models import Label
from apis_core.helper_functions.RDFparsers import GenericRDFParser
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
