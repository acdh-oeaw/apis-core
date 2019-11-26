# -*- coding: utf-8 -*-
from dal import autocomplete
from .fields import ListSelect2, Select2Multiple, Select2
from django import forms
from django.urls import reverse_lazy
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.layout import Layout, Fieldset
from crispy_forms.bootstrap import Accordion, AccordionGroup
from django.forms import ModelMultipleChoiceField, ModelChoiceField
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from django.db.models.fields import BLANK_CHOICE_DASH
from django.contrib.contenttypes.models import ContentType
from django.core.validators import URLValidator
from django.conf import settings

from .models import Person, Place, Institution, Event, Work
from apis_core.apis_vocabularies.models import TextType
from apis_core.apis_metainfo.models import Text, Uri, Collection
from apis_core.apis_metainfo.forms import get_date_help_text_from_dates, get_date_help_text_default

from apis_core.helper_functions.RDFParser import RDFParser

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

    # TODO __sresch__ : consider moving this class outside of the function call to avoid redundant class definitions
    class GenericEntitiesForm(forms.ModelForm):
        class Meta:
            model = ContentType.objects.get(
                app_label='apis_entities', model=entity.lower()).model_class()

            exclude = [
                'start_date',
                'start_start_date',
                'start_end_date',
                'start_date_is_exact',
                'end_date',
                'end_start_date',
                'end_end_date',
                'end_date_is_exact',
                'text',
                'source',
            ]
            exclude.extend(model.get_related_entity_field_names())
            exclude.extend(model.get_related_relationtype_field_names())


        def __init__(self, *args, **kwargs):
            super(GenericEntitiesForm, self).__init__(*args, **kwargs)
            self.helper = FormHelper()
            self.helper.form_class = entity.title()+'Form'
            self.helper.form_tag = False
            self.helper.help_text_inline = True
            acc_grp1 = Fieldset('Metadata {}'.format(entity.title()))
            acc_grp2 = AccordionGroup(
                        'MetaInfo',
                        'references',
                        'notes',
                        'review')
            attrs = {'data-placeholder': 'Type to get suggestions',
                     'data-minimum-input-length': getattr(settings, "APIS_MIN_CHAR", 3),
                     'data-html': True}

            # list to catch all fields that will not be inserted into accordion group acc_grp2
            fields_list_unsorted = []

            for f in self.fields.keys():
                if isinstance(self.fields[f], (ModelMultipleChoiceField, ModelChoiceField)):
                    v_name_p = str(self.fields[f].queryset.model.__name__)
                    if isinstance(self.fields[f], ModelMultipleChoiceField):
                        widget1 = Select2Multiple
                    else:
                        widget1 = ListSelect2
                    if ContentType.objects.get(app_label__in=[
                        'apis_entities',
                        'apis_metainfo',
                        'apis_relations',
                        'apis_vocabularies',
                        'apis_labels'
                    ], model=v_name_p.lower()).app_label.lower() == 'apis_vocabularies':
                        self.fields[f].widget = widget1(
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
                            if isinstance(self.fields[f], ModelMultipleChoiceField):
                                try:
                                    for x in getattr(self.instance, f).all():
                                        res.append((x.pk, x.label))
                                except ValueError:
                                    pass
                                self.fields[f].initial = res
                                self.fields[f].choices = res
                            else:
                                try:
                                    res = getattr(self.instance, f)
                                    if res is not None:
                                        self.fields[f].initial = (res.pk, res.label)
                                        self.fields[f].choices = [(res.pk, res.label),]
                                except ValueError:
                                    res = ''
                if f not in acc_grp2:
                    # append to unsorted list, so that it can be sorted and afterwards attached to accordion group acc_grp1
                    fields_list_unsorted.append(f)


            def sort_fields_list(list_unsorted, entity_label):
                """
                Sorts a list of model fields according to a defined order.


                :param list_unsorted: list
                    The unsorted list of fields.

                :param entity_label: str
                    The string representation of entity type, necessary to find the entity-specific ordering (if it is defined)


                :return: list
                    The sorted list if entity-specific ordering was defined, the same unordered list if not.
                """

                fields_sort_preferences_per_entity = {
                    'Person': [
                        'name',
                        'first_name',
                        'gender',
                        'title',
                        'start_date_written',
                        'end_date_written',
                        'status',
                        'collection',
                    ],
                    'Event': [
                        'name',
                        'name_english',
                    ],
                    'Institution': [
                        'name',
                        'name_english',
                        'end_date_written',
                    ],
                    'Place': [
                        'name',
                        'name_english'
                    ]
                }

                if entity_label in fields_sort_preferences_per_entity:
                    # for this entity an ordering was defined, go trough it

                    sort_preferences = fields_sort_preferences_per_entity[entity_label]

                    # list of tuples to be sorted later
                    field_rank_pair_list = []

                    for field in list_unsorted:
                        try:
                            # if this succeeds, then the field has been given a priorites ordering above
                            field_rank_pair = (field, sort_preferences.index(field))

                        except Exception as e:
                            # if no ordering for the field was found, then give it 'Inf'
                            # so that it will be attached at the end.
                            field_rank_pair = (field, float('Inf'))

                        field_rank_pair_list.append(field_rank_pair)

                    # sort the list according to the second element in each tuple
                    # and then take the first elements from it and return as list
                    return [ t[0] for t in sorted(field_rank_pair_list, key=lambda x: x[1]) ]

                else:
                    # for this entity no ordering was defined, return unsorted list
                    return list_unsorted

            # sort field list, iterate over it and append each element to the accordion group
            for f in sort_fields_list(fields_list_unsorted, entity):
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


            # check if form loads an existing instance
            if 'instance' in kwargs:
                # instance exists, thus run the date parse check to inform the user about its results

                instance = kwargs['instance']

                self.fields['start_date_written'].help_text = get_date_help_text_from_dates(
                    instance.start_date,
                    instance.start_start_date,
                    instance.start_end_date,
                    instance.start_date_written
                )
                self.fields['end_date_written'].help_text = get_date_help_text_from_dates(
                    instance.end_date,
                    instance.end_start_date,
                    instance.end_end_date,
                    instance.end_date_written
                )

            else:
                # instance does not exist, load default help text into fields

                self.fields['start_date_written'].help_text = get_date_help_text_default()
                self.fields['end_date_written'].help_text = get_date_help_text_default()



        def save(self, *args, **kwargs):
            obj = super(GenericEntitiesForm, self).save(*args, **kwargs)
            if obj.collection.all().count() == 0:
                col_name = getattr(settings, 'APIS_DEFAULT_COLLECTION', 'manually created entity')
                col, created = Collection.objects.get_or_create(name=col_name)
                obj.collection.add(col)
            return obj

    return GenericEntitiesForm


class GenericEntitiesStanbolForm(forms.Form):
    def save(self, *args, **kwargs):
        cd = self.cleaned_data
        entity = RDFParser(cd['entity'], self.entity.title()).get_or_create()
        return entity

    def __init__(self, entity, *args, **kwargs):
        attrs = {'data-placeholder': 'Type to get suggestions',
                 'data-minimum-input-length': getattr(settings, "APIS_MIN_CHAR", 3),
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
                widget=ListSelect2(
                    url=url,
                    attrs=attrs),
                validators=[URLValidator])


class FullTextForm(forms.Form):

    def save(self, entity):
        cd = self.cleaned_data
        text = None
        for f in cd.keys():
            text_type = TextType.objects.get(pk=f.split('_')[1])
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
    ann_include_all = forms.BooleanField(
        required=False, label='Include general relations',
        help_text="""Not all relations are connected to an annotation.\
        If checked relations that are not attached to an annotation are include.\
        This setting is only used when an Annotation project is specified."""
    )
    start_date = forms.CharField(
        label='Start date',
        required=False,
        widget=forms.TextInput(
            attrs={
                'data-provide': 'datepicker',
                'data-date-format': 'dd.mm.yyyy'
            }
        )
    )
    end_date = forms.CharField(
        label='End date',
        required=False,
        widget=forms.TextInput(
            attrs={
                'data-provide': 'datepicker',
                'data-date-format': 'dd.mm.yyyy'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        rel_attrs = {
            'data-placeholder': 'Type to get suggestions',
            'data-minimum-input-length': getattr(settings, "APIS_MIN_CHAR", 3),
            'data-html': True
        }
        attrs = {
            'data-placeholder': 'Type to get suggestions',
            'data-minimum-input-length': getattr(settings, "APIS_MIN_CHAR", 3),
            'data-html': True
        }
        super(NetworkVizFilterForm, self).__init__(*args, **kwargs)
        self.fields['select_relation'] = forms.ChoiceField(
            label='Relation type',
            choices=list(('-'.join(x.name.split()), x.name) for x in ContentType.objects.filter(
                app_label='apis_relations')
            ),
            help_text="Include only relations related to this annotation project \
            (See the include general relations checkbox)")
        self.fields['select_relation'].initial = ('person-place', 'person place')
        self.fields['search_source'] = autocomplete.Select2ListCreateChoiceField(
            label='Search source',
            widget=ListSelect2(
                url=reverse(
                    'apis:apis_entities:generic_network_entities_autocomplete',
                    kwargs={
                        'entity': 'person'
                    }
                ),
                attrs=attrs
            )
        )
        self.fields['search_target'] = autocomplete.Select2ListCreateChoiceField(
            label='Search target',
            widget=ListSelect2(
                url=reverse(
                    'apis:apis_entities:generic_network_entities_autocomplete',
                    kwargs={
                        'entity': 'place'
                    }
                ),
                attrs=attrs
            )
        )
        self.fields['select_kind'] = autocomplete.Select2ListCreateChoiceField(
            label='Select kind',
            widget=ListSelect2(
                url=reverse(
                    'apis:apis_vocabularies:generic_vocabularies_autocomplete',
                    kwargs={
                        'vocab': 'personplacerelation',
                        'direct': 'normal'
                    }
                ),
                attrs=rel_attrs
            )
        )
        if 'apis_highlighter' in settings.INSTALLED_APPS:
            self.fields['annotation_proj'] = forms.ChoiceField(
                label='Annotation Project',
                choices=BLANK_CHOICE_DASH + list(
                    (x.pk, x.name) for x in AnnotationProject.objects.all()),
                required=False,
                help_text="Include only relations related to this annotation project \
                (See the include general relations checkbox)")
        self.helper = FormHelper()
        self.helper.form_class = 'FilterNodesForm'
        self.helper.form_action = reverse('apis:apis_core:NetJson-list')
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
