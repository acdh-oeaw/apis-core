import re

from django.contrib.contenttypes.models import ContentType
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.bootstrap import Accordion, AccordionGroup
import autocomplete_light.shortcuts as al
from django.utils.translation import ugettext_lazy as _

from metainfo.models import TempEntityClass, Uri
from helper_functions.RDFparsers import GenericRDFParser


class GenericRelationForm(forms.ModelForm):

    class Meta:
        model = TempEntityClass
        fields = ['start_date_written', 'end_date_written', 'references', 'notes']
        labels = {
            'start_date_written': _('Start'),
            'end_date_written': _('End'),
        }

    def save(self, site_instance, instance=None, commit=True):
        cd = self.cleaned_data
        if instance:
            x = self.relation_form.objects.get(pk=instance)
        else:
            x = self.relation_form()
        x.relation_type_id = cd['relation_type']
        x.start_date_written = cd['start_date_written']
        x.end_date_written = cd['end_date_written']
        x.notes = cd['notes']
        x.references = cd['references']
        setattr(x, self.rel_accessor[3], site_instance)
        target = ContentType.objects.get(app_label='entities', model=self.rel_accessor[0].lower()).model_class()
        t1 = target.get_or_create_uri(cd['target_uri'])
        if not t1:
            t1 = GenericRDFParser(cd['target_uri'], self.rel_accessor[0]).get_or_create()
        setattr(x, self.rel_accessor[2], t1)
        x.save()
        return x

    def __init__(self, siteID=None, *args, **kwargs):
        entity_type = kwargs.pop('entity_type')
        if type(entity_type) != str:
            entity_type = entity_type.__name__
        self.relation_form = kwargs.pop('relation_form')
        if type(self.relation_form) == str:
            self.relation_form = ContentType.objects.get(app_label='relations', model=self.relation_form.lower()).model_class()
        self.request = kwargs.pop('request', False)
        super(GenericRelationForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['relation_type'] = forms.CharField(label='Relation type', required=True)
        self.helper = FormHelper()
        self.helper.form_class = '{}Form'.format(str(self.relation_form))
        self.helper.form_tag = False
        lst_src_target = re.findall('[A-Z][^A-Z]*', self.relation_form.__name__)
        print(lst_src_target, entity_type)
        if lst_src_target[0] == lst_src_target[1]:
            if instance and instance.id:
                if getattr(instance, 'related_{}A_id'.format(lst_src_target[0].lower())) == int(siteID):
                    self.rel_accessor = (lst_src_target[1], True,
                                         'related_{}B'.format(lst_src_target[1].lower()),
                                         'related_{}A'.format(lst_src_target[0].lower()))
                else:
                    self.rel_accessor = (lst_src_target[1], False,
                                         'related_{}A'.format(lst_src_target[1].lower()),
                                         'related_{}B'.format(lst_src_target[0].lower()))
            else:
                self.rel_accessor = (lst_src_target[1], True,
                                     'related_{}B'.format(lst_src_target[1].lower()),
                                     'related_{}A'.format(lst_src_target[0].lower()))
            self.fields['relation_type'].widget = al.ChoiceWidget(
                'VC{}{}Autocomplete'.format(lst_src_target[0], lst_src_target[1]))
            self.fields['target'] = forms.CharField(label=lst_src_target[1],
                                                    widget=al.TextWidget('{}Autocomplete'.format(lst_src_target[1])))
            self.fields['target_uri'] = forms.CharField(required=False, widget=forms.HiddenInput())
        elif entity_type == lst_src_target[0]:
            self.rel_accessor = (lst_src_target[1], True,
                                 'related_{}'.format(lst_src_target[1].lower()),
                                 'related_{}'.format(lst_src_target[0].lower()))
            self.fields['relation_type'].widget = al.ChoiceWidget('VC{}{}Autocomplete'.format(lst_src_target[0], lst_src_target[1]))
            self.fields['target'] = forms.CharField(label=lst_src_target[1],
                                                    widget=al.TextWidget('{}Autocomplete'.format(lst_src_target[1])))
            self.fields['target_uri'] = forms.CharField(required=False, widget=forms.HiddenInput())
        elif entity_type == lst_src_target[1]:
            self.rel_accessor = (lst_src_target[0], False,
                                 'related_{}'.format(lst_src_target[0].lower()),
                                 'related_{}'.format(lst_src_target[1].lower()))
            self.fields['relation_type'].widget = al.ChoiceWidget(
                'VC{}{}ReverseAutocomplete'.format(lst_src_target[0], lst_src_target[1]))
            self.fields['target'] = forms.CharField(label=lst_src_target[0],
                                                    widget=al.TextWidget('{}Autocomplete'.format(lst_src_target[0])))
            self.fields['target_uri'] = forms.CharField(required=False, widget=forms.HiddenInput())
        else:
            print('no hit rel_accessor')
        if instance and instance.id:
            self.fields['target'].initial = str(getattr(instance, self.rel_accessor[2]))
            self.fields['target_uri'].initial = Uri.objects.filter(
                entity=getattr(instance, self.rel_accessor[2]))[0]
            if self.rel_accessor[1]:
                auto_acc = 'VC{}{}Autocomplete'.format(lst_src_target[0], lst_src_target[1])
                auto_choices = [instance.relation_type.label]
            else:
                auto_acc = 'VC{}{}ReverseAutocomplete'.format(lst_src_target[0], lst_src_target[1])
                auto_choices = [instance.relation_type.label_reverse]
            self.fields['relation_type'].widget = al.ChoiceWidget(
                auto_acc,
                extra_context={'values': [instance.relation_type.pk],
                               'choices': auto_choices})

        print('ent type: {}'.format(entity_type))
        self.helper.layout = Layout(
            'relation_type',
            'target',
            'target_uri',
            'start_date_written',
            'end_date_written',
            Accordion(
                AccordionGroup(
                    'Notes and References',
                    'notes',
                    'references',
                    active=False,
                    css_id="{}_notes_refs".format(self.relation_form.__name__))))