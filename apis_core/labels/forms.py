from django import forms
#from autocomplete_light import shortcuts as al
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Div

from .autocomplete_light_registry import LabelAutocomplete
from .models import Label


class LabelForm(forms.ModelForm):
    isoCode = forms.CharField(required=True,
                              #widget=al.TextWidget('LabelAutocomplete'),
                              label="ISO 639-3")
    label = forms.CharField(required=True, help_text="The entities label or name.")

    class Meta:
        model = Label
        fields = ['temp_entity', 'label', 'isoCode']

    def __init__(self, *args, **kwargs):
        super(LabelForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    # self.helper.add_input(Submit('submit','Speichern'))
