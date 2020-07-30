#!/usr/bin/python
# -*- coding: utf-8 -*-

from crispy_forms.helper import FormHelper
from django import forms

from apis_core.apis_entities.models import Place
from apis_core.apis_labels.models import Label
from apis_core.helper_functions import DateParser
from apis_core.helper_functions.RDFParser import RDFParser


##############################################
# Generic
##############################################

class EntityLabelForm(forms.ModelForm):

    class Meta:
        model = Label
        fields = ['label', 'isoCode_639_3', 'label_type', 'start_date_written', 'end_date_written']

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        if instance:
            x = Label.objects.get(pk=instance)
            x.label = cd['label']
            x.isoCode_639_3 = cd['isoCode_639_3']
            x.label_type = cd['label_type']
            x.start_date_written = cd['start_date_written']
            x.end_date_written = cd['end_date_written']
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

        instance = getattr(self, 'instance', None)
        if instance != None:

            if instance.start_date_written:
                self.fields['start_date_written'].help_text = DateParser.get_date_help_text_from_dates(
                    single_date=instance.start_date,
                    single_start_date=instance.start_start_date,
                    single_end_date=instance.start_end_date,
                    single_date_written=instance.start_date_written,
                )
            else:
                self.fields['start_date_written'].help_text = DateParser.get_date_help_text_default()

            if instance.end_date_written:
                self.fields['end_date_written'].help_text = DateParser.get_date_help_text_from_dates(
                    single_date=instance.end_date,
                    single_start_date=instance.end_start_date,
                    single_end_date=instance.end_end_date,
                    single_date_written=instance.end_date_written,
                )
            else:
                self.fields['end_date_written'].help_text = DateParser.get_date_help_text_default()

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

class PlaceLabelForm(EntityLabelForm):
    pass


##############################################
# Events
##############################################


class EventLabelForm(EntityLabelForm):
    pass


##############################################
# Entities Base Forms
#############################################


class PlaceEntityForm(forms.Form):
    # place = forms.CharField(label='Place', widget=al.TextWidget('OrtAutocomplete'))
    place_uri = forms.CharField(required=False, widget=forms.HiddenInput())

    def save(self, *args, **kwargs):
        cd = self.cleaned_data
        pl = Place.get_or_create_uri(cd['place_uri'])
        if not pl:
            pl = RDFParser(cd['place_uri'], 'Place').get_or_create()
        return pl
