from crispy_forms.bootstrap import Accordion, AccordionGroup
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout
from dal import autocomplete
from django import forms

from .models import *


class UriForm(forms.ModelForm):
    class Meta:
        model = Uri
        fields = "__all__"
        widgets = {
            'entity': autocomplete.ModelSelect2(
                url='apis_core:apis_metainfo-ac:apis_tempentity-autocomplete'),
            }

    def __init__(self, *args, **kwargs):
        super(UriForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-3'
        self.helper.field_class = 'col-md-9'
        self.helper.add_input(Submit('submit', 'save'),)


class UriFilterFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(UriFilterFormHelper, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_class = 'genericFilterForm'
        self.form_method = 'GET'
        self.helper.form_tag = False
        self.add_input(Submit('Filter', 'Search'))
        self.layout = Layout(
            Accordion(
                AccordionGroup(
                    'Filter',
                    'uri',
                    'domain',
                    'entity__name',
                    css_id="basic_search_fields"
                    ),
                )
            )
