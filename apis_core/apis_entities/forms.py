# -*- coding: utf-8 -*-
from dal import autocomplete
from .fields import ListSelect2
from django import forms
from django.urls import reverse_lazy
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.layout import Layout
from crispy_forms.bootstrap import Accordion, AccordionGroup
from django.forms import ModelMultipleChoiceField
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from django.db.models.fields import BLANK_CHOICE_DASH
from django.contrib.contenttypes.models import ContentType
from django.core.validators import URLValidator
from django.conf import settings

from .models import Person, Place, Institution, Event, Work
from apis_core.apis_vocabularies.models import TextType
from apis_core.apis_metainfo.models import Text, Uri

from apis_core.helper_functions.RDFparsers import GenericRDFParser

if 'apis_highlighter' in settings.INSTALLED_APPS:
    from apis_highlighter.models import AnnotationProject


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
            model = ContentType.objects.get(
                app_label='apis_entities', model=entity.lower()).model_class()
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
            attrs = {'data-placeholder': 'Type to get suggestions',
                     'data-minimum-input-length': 3,
                     'data-html': True}
            for f in self.fields.keys():
                if type(self.fields[f]) == ModelMultipleChoiceField:
                    v_name_p = str(self.fields[f].queryset.model.__name__)
                    if ContentType.objects.get(app_label__in=[
                        'apis_entities',
                        'apis_metainfo',
                        'apis_relations',
                        'apis_vocabularies',
                        'apis_labels'
                    ], model=v_name_p.lower()).app_label.lower() == 'apis_vocabularies':
                        self.fields[f].widget = autocomplete.Select2Multiple(
                            url=reverse(
                                'apis:apis_vocabularies:generic_vocabularies_autocomplete',
                                kwargs={
                                    'vocab': v_name_p.lower(),
                                    'direct': 'normal'
                                    }
                                ),
                            attrs=attrs)
                        if self.instance:
                            res = []
                            try:
                                for x in getattr(self.instance, f).all():
                                    res.append((x.pk, x.name))
                            except ValueError:
                                pass
                            self.fields[f].choices = res
                            self.fields[f].initial = res
                if f not in acc_grp2:
                    acc_grp1.append(f)

            self.helper.layout = Layout(
                Accordion(
                    acc_grp1,
                    acc_grp2
                    )
            )
            self.fields['status'].required = False
            self.fields['collection'].required = False
            self.fields['start_date_written'].required = False
            self.fields['end_date_written'].required = False
    return GenericEntitiesForm


class GenericEntitiesStanbolForm(forms.Form):
    def save(self, *args, **kwargs):
        cd = self.cleaned_data
        entity = GenericRDFParser(cd['entity'], self.entity.title()).get_or_create()
        return entity

    def __init__(self, entity, *args, **kwargs):
        attrs = {'data-placeholder': 'Type to get suggestions',
                 'data-minimum-input-length': 3,
                 'data-html': True,
                 'style': 'width: auto'}
        ent_merge_pk = kwargs.pop('ent_merge_pk', False)
        super(GenericEntitiesStanbolForm, self).__init__(*args, **kwargs)
        self.entity = entity
        self.helper = FormHelper()
        form_kwargs = {'entity': entity}
        url = reverse(
            'apis:apis_entities:generic_entities_autocomplete', args=[entity.title(), 'remove']
        )
        label = 'Create {} from reference resources'.format(entity.title())
        button_label = 'Create'
        if ent_merge_pk:
            form_kwargs['ent_merge_pk'] = ent_merge_pk
            url = reverse('apis:apis_entities:generic_entities_autocomplete', args=[entity.title()])
            label = 'Search for {0} in reference resources or db'.format(entity.title())
            button_label = 'Merge'
        self.helper.form_action = reverse(
            'apis:apis_entities:generic_entities_stanbol_create', kwargs=form_kwargs
        )
        self.helper.add_input(Submit('submit', button_label))
        self.fields['entity'] = autocomplete.Select2ListCreateChoiceField(
                label=label,
                widget=autocomplete.ListSelect2(
                    url=url,
                    attrs=attrs),
                validators=[URLValidator])


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
                for t in instance.text.all():
                    if 'text_'+str(t.kind.pk) in self.fields.keys():
                        self.fields['text_'+str(t.kind.pk)].initial = t.text
        except:
            pass


class PersonResolveUriForm(forms.Form):
    # person = forms.CharField(label=False, widget=al.TextWidget('PersonAutocomplete'))
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


class NetworkVizFilterForm(forms.Form):
    # select_relation = forms.ChoiceField(choices=choices)
    # search_source = forms.CharField(widget=al.ChoiceWidget('DB_PersonAutocomplete'), required=False)
    # search_source = forms.CharField(required=False)
    # select_kind = forms.CharField(widget=al.ChoiceWidget('VCPersonPlaceAutocomplete'), required=False)
    # search_target = forms.CharField(required=False)
    # search_target = forms.CharField(widget=al.ChoiceWidget('DB_PlaceAutocomplete'), required=False)
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
        attrs = {'data-placeholder': 'Type to get suggestions',
                 'data-minimum-input-length': 3,
                 'data-html': True,}
        super(NetworkVizFilterForm, self).__init__(*args, **kwargs)
        self.fields['select_relation'] = forms.ChoiceField(
            label='Relation type',
            choices=list(('-'.join(x.name.split()), x.name) for x in ContentType.objects.filter(app_label='apis_relations')),
            help_text="Include only relations related to this annotation project \
            (See the include general relations checkbox)")
        self.fields['select_relation'].initial = ('person-place', 'person place')
        self.fields['search_source'] = autocomplete.Select2ListCreateChoiceField(
                                        label='Search source',
                                        widget=ListSelect2(
                                            url=reverse('apis:apis_entities:generic_network_entities_autocomplete',
                                                        kwargs={'entity': 'person'}),
                                            attrs=attrs))
        self.fields['search_target'] = autocomplete.Select2ListCreateChoiceField(
                                        label='Search target',
                                        widget=ListSelect2(
                                            url=reverse('apis:apis_entities:generic_network_entities_autocomplete',
                                                        kwargs={'entity': 'place'}),
                                            attrs=attrs))
        self.fields['select_kind'] = autocomplete.Select2ListCreateChoiceField(
                                        label='Select kind',
                                        widget=ListSelect2(
                                            url=reverse('apis:apis_vocabularies:generic_vocabularies_autocomplete',
                                                        kwargs={'vocab': 'personplacerelation',
                                                                'direct': 'normal'}),
                                            attrs=attrs))
        if 'apis_highlighter' in settings.INSTALLED_APPS:
            self.fields['annotation_proj'] = forms.ChoiceField(
                label='Annotation Project',
                choices=BLANK_CHOICE_DASH + list((x.pk, x.name) for x in AnnotationProject.objects.all()),
                required=False,
                help_text="Include only relations related to this annotation project \
                (See the include general relations checkbox)")
        self.helper = FormHelper()
        self.helper.form_class = 'FilterNodesForm'
        self.helper.form_action = 'apis:NetJson-list'
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
