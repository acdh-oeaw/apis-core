from crispy_forms.helper import FormHelper
from django import forms

from .models import Label


# TODO __sresch__ : inspect if this should be removed or adapted
# since this class seems redundant as the same functionality is provided in apis_relations/forms.py in class EntityLabelForm there
#
# This class LabelForm here is only refered to in apis_labels/views.py which would be loaded by the respective urls in apis_labels/urls.py
# However none of these urls seem to work when called in the browser
class LabelForm(forms.ModelForm):
    isoCode = forms.CharField(
        required=True,
        label="ISO 639-3"
    )
    label = forms.CharField(required=True, help_text="The entities label or name.")

    class Meta:
        model = Label
        fields = ['label', 'isoCode_639_3', 'label_type']

    def __init__(self, *args, **kwargs):
        super(LabelForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
