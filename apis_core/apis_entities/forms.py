# -*- coding: utf-8 -*-
from convertdate import julian

from dal import autocomplete
from .fields import ListSelect2, Select2Multiple
from django import forms
from django.urls import reverse_lazy
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.layout import Layout, Fieldset
from crispy_forms.bootstrap import Accordion, AccordionGroup
from django.forms import ModelMultipleChoiceField
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from django.db.models.fields import BLANK_CHOICE_DASH
from django.contrib.contenttypes.models import ContentType
from django.core.validators import URLValidator
from django.conf import settings

from .models import Person, Place, Institution, Event, Passage
from apis_core.apis_vocabularies.models import TextType
from apis_core.apis_metainfo.models import Text, Uri, Collection

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
            exclude = [
                'start_date',
                'start_start_date',
                'start_end_date',
                'end_date',
                'end_start_date',
                'end_end_date',
                'text',
                'source',
            ]

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
                        self.fields[f].widget = Select2Multiple(
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

            if entity == 'Person':
                acc_grp1 = Fieldset('Metadata {}'.format(entity.title()))
                person_field_list = [
                    'name',
                    'first_name',
                    'gender',
                    'title',
                    'profession',
                    'start_date_written',
                    'end_date_written',
                    'status',
                    'collection',
                ]
                for x in person_field_list:
                    acc_grp1.append(x)

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


            # Loading dynamic help texts at date fields according to their parsing results

            # default
            help_text_default = "Dates are interpreted by defined rules. " \
                                "If this fails, an iso-date can be explicitly by inserting '&lt;YYYY-MM-DD&gt;'."

            # check if form loads an existing instance
            if 'instance' in kwargs:
                # instance exists, thus run the date parse check to inform the user about its results

                instance = kwargs['instance']

                def create_help_text(single_date, single_start_date, single_end_date, single_date_written):
                    """
                    function for creating string help text from parsed dates, to provide feedback to the user
                    about the parsing status of a given date field.

                    :param single_date: datetime :
                        the individual date point (gregorian)

                    :param single_start_date: datetime :
                        the start range of a date(gregorian)

                    :param single_end_date: datetime :
                        the endrange of a date(gregorian)

                    :param single_date_written: str :
                        the textual description of a date field (needed to check if empty or not)


                    :return help_text: str :
                        The text to be displayed underneath a date field, informing the user about the parsing result
                    """


                    # check which of the dates could be parsed to construct the relevant feedback text

                    help_text = ""
                    if single_date:
                        # single date could be parsed

                        help_text = "Date interpreted as: "

                        # convert gregorian database date format into julian for user layer
                        single_date_j = julian.from_gregorian(
                            year=single_date.year,
                            month=single_date.month,
                            day=single_date.day
                        )

                        if single_start_date or single_end_date:
                            # date has also start or end ranges, then ignore single date

                            if single_start_date:
                                # date has start range

                                # convert to julian
                                single_start_date_j = julian.from_gregorian(
                                    year=single_start_date.year,
                                    month=single_start_date.month,
                                    day=single_start_date.day
                                )
                                help_text += \
                                    str(single_start_date_j[0]) +"-"+ str(single_start_date_j[1]) +"-"+ str(single_start_date_j[2]) + \
                                    " until "
                            else:
                                # date has no start range, then write 'undefined'

                                help_text += "undefined start until "

                            if single_end_date:
                                # date has end range

                                # convert to julian
                                single_end_date_j = julian.from_gregorian(
                                    year=single_end_date.year,
                                    month=single_end_date.month,
                                    day=single_end_date.day
                                )
                                help_text += \
                                    str(single_end_date_j[0]) + "-" + str(single_end_date_j[1]) + "-" + str(single_end_date_j[2])
                            else:
                                # date has no start range, then write 'undefined'

                                help_text += "undefined end"

                        else:
                            # date has no start nor end range. Use single date then.

                            help_text += str(single_date_j[0]) +"-"+ str(single_date_j[1]) +"-"+ str(single_date_j[2])

                    elif single_date_written is not None:
                        # date field is not empty but it could not be parsed either. Show parsing info and help text

                        help_text = "<b>Date could not be interpreted</b><br>" + help_text_default

                    else:
                        # date field is completely empty. Show help text only

                        help_text = help_text_default

                    return help_text

                # write results into help texts
                self.fields['start_date_written'].help_text = create_help_text(
                    instance.start_date,
                    instance.start_start_date,
                    instance.start_end_date,
                    instance.start_date_written
                )
                self.fields['end_date_written'].help_text = create_help_text(
                    instance.end_date,
                    instance.end_start_date,
                    instance.end_end_date,
                    instance.end_date_written
                )

            else:
                # instance does not exist, load default help text into fields

                self.fields['start_date_written'].help_text = help_text_default
                self.fields['end_date_written'].help_text = help_text_default



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
            'data-minimum-input-length': 0,
            'data-html': True
        }
        attrs = {
            'data-placeholder': 'Type to get suggestions',
            'data-minimum-input-length': 0,
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
        self.helper.form_action = reverse('apis:NetJson-list')
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
