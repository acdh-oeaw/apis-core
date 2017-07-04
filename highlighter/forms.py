from django import forms
import autocomplete_light.shortcuts as al
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.layout import Submit
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Group
from django.db.models.fields import BLANK_CHOICE_DASH

from relations.forms import PersonPlaceForm, PersonInstitutionForm
from metainfo.models import Collection
from .models import AnnotationProject
from vocabularies.models import TextType


class PersonPlaceFormHighlighter(PersonPlaceForm):

    def __init__(self, *args, **kwargs):
        super(PersonPlaceFormHighlighter, self).__init__(*args, **kwargs)
        self.fields['HL_start'] = forms.IntegerField(widget=forms.HiddenInput)
        self.fields['HL_end'] = forms.IntegerField(widget=forms.HiddenInput)


class PersonInstitutionFormHighlighter(PersonInstitutionForm):

    def __init__(self, *args, **kwargs):
        super(PersonInstitutionFormHighlighter, self).__init__(*args, **kwargs)
        self.fields['HL_start'] = forms.IntegerField(widget=forms.HiddenInput)
        self.fields['HL_end'] = forms.IntegerField(widget=forms.HiddenInput)


class LinkHighlighterForm(forms.Form):

    relation = forms.CharField(label='Relation', widget=al.TextWidget('PersonAutocomplete'))


class SelectAnnotationProject(forms.Form):
    project = forms.ChoiceField(label=False, required=False)
    users_show = forms.MultipleChoiceField(label=False, required=False)
    #show_all = forms.BooleanField(label='Show all?')

    def __init__(self, *args, **kwargs):
        choices_type = ContentType.objects.filter(app_label__in=['Entities', 'Relations']).values_list('pk', 'model')
        set_ann_proj = kwargs.pop('set_ann_proj', False)
        entity_types_highlighter = kwargs.pop('entity_types_highlighter', False)
        users_show = kwargs.pop('users_show_highlighter', False)
        super().__init__(*args, **kwargs)
        CHOICES = AnnotationProject.objects.all()
        choices_user = User.objects.all()
        self.fields['project'] = forms.ChoiceField(
            choices=tuple((x.pk, x.name) for x in CHOICES),
            label=False)
        self.fields['users_show'] = forms.MultipleChoiceField(
            choices=tuple((x.pk, x.username) for x in choices_user),
            label=False)
        self.fields['types'] = forms.MultipleChoiceField(required=False, choices=choices_type, label=False)
        self.helper = FormHelper()
        self.helper.form_id = 'InitAnnotationProject'
        self.helper.form_class = 'form-inline'
        self.helper.form_method = 'GET'
        self.initial['project'] = set_ann_proj
        self.initial['types'] = entity_types_highlighter
        self.initial['users_show'] = users_show
        self.helper.add_input(Submit('Update', 'Update'))


class SelectAnnotatorAgreement(forms.Form):
    choices_metrics = (('Do_alpha', 'Disagreement Alpha Coefficient'),
                       ('multi_kappa', 'Multi Kappa (Davies and Fleiss 1982)'),
                       ('alpha', 'Krippendorff 1980'),
                       ('avg_Ao', 'Average observed agreement'),
                       ('S', 'Bennett, Albert and Goldstein 1954'),
                       ('pi', 'Scott 1955; here, multi-pi.'),
                       ('kappa', 'Kappa (Cohen 1960)'),
                       ('weighted_kappa', 'Weighted Kappa (Cohen 1968)'))
    choices_format_string = (('start_end_text', 'String & Annotation'),
                             ('start_end_text_ent', 'String, Annotation & Entity type'),
                             ('start_end_text_ent_entid', 'String, Annotation, Entity type & ID'),
                             ('start_end_text_rel_ent_entid', 'String, Annotation, Entity type, ID & relation type'))
    metrics = forms.ChoiceField(label='Metrics', choices=choices_metrics, required=True)
    format_string = forms.ChoiceField(label='Format Annotation', choices=choices_format_string, required=True)
    user_group = forms.ChoiceField(label='User group', required=False)
    gold_standard = forms.ChoiceField(label='Gold standard', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices_groups = Group.objects.all()
        choices_users = User.objects.all()
        self.fields['user_group'] = forms.ChoiceField(
            choices=BLANK_CHOICE_DASH+list((x.pk, x.name) for x in choices_groups),
            required=False)
        self.fields['gold_standard'] = forms.ChoiceField(
            choices=BLANK_CHOICE_DASH+list((x.pk, x.username) for x in choices_users),
            required=False)
        self.helper = FormHelper()
        self.helper.form_id = 'SelectAnnotatorAgreement'
        self.helper.form_class = 'form-inline'
        self.helper.form_method = 'GET'
        self.helper.add_input(Submit('Update', 'Update'))


class SelectAnnotatorAgreementCollection(SelectAnnotatorAgreement):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['anno_proj'] = forms.ChoiceField(
            label='Annotation Project',
            choices=list((x.pk, x.name) for x in AnnotationProject.objects.all()),
            required=True)
        self.fields['collection'] = forms.ChoiceField(
            choices=BLANK_CHOICE_DASH + list((x.pk, x.name) for x in Collection.objects.all()),
            required=False)
        self.fields['kind_instance'] = forms.ChoiceField(label='Entity kind Collection',
            choices=BLANK_CHOICE_DASH + list((x.pk, x.name) for x in ContentType.objects.filter(app_label="entities")),
            required=False)
        self.fields['text_type'] = forms.MultipleChoiceField(
            choices=BLANK_CHOICE_DASH + list((x.pk, x.name) for x in TextType.objects.all()),
            required=False)
        self.helper.form_id = 'SelectAnnotatorAgreementCollection'
        self.helper.form_class = 'form'
        self.helper.form_method = 'POST'
        self.order_fields(('metrics', 'anno_proj', 'format_string', 'user_group',
                                'gold_standard', 'collection', 'kind_instance', 'text_type'))

