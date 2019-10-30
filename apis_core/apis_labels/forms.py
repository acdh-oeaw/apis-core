from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Div

from .models import Label


class LabelForm(forms.ModelForm):
    isoCode = forms.CharField(
        required=True,
        label="ISO 639-3"
    )
    label = forms.CharField(required=True, help_text="The entities label or name.")

    class Meta:
        model = Label
        fields = ['temp_entity', 'label', 'isoCode']

    def __init__(self, *args, **kwargs):
        super(LabelForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
