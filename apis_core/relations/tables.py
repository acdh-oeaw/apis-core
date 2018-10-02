import django_tables2 as tables
from django.contrib.contenttypes.models import ContentType
from django_tables2.utils import A

from .models import (PersonInstitution, PersonPlace, PersonPerson, PersonEvent, InstitutionEvent, PlaceEvent,
                     PersonWork, InstitutionWork, InstitutionPlace, PlaceWork, EventWork)
from labels.models import Label
from metainfo.models import Uri


empty_text_default = 'There are currently no relations'


def get_generic_relations_table(relation, entity, detail=None):
    print('table call: {} {}'.format(relation, entity))
    ct = ContentType.objects.get(app_label='relations', model=relation.lower())
    name = ct.name.split()
    if name[0] == name[1]:
        rel_ent = name[0]
    else:
        if name[1].lower() == entity.lower():
            rel_ent = name[0]
            rel_type = 'label_reverse'
        else:
            rel_ent = name[1]
            rel_type = 'label'

    class GenericRelationsTable(tables.Table):

        class Meta:
            empty_text = empty_text_default
            model = ct.model_class()
            fields = ['start_date', 'end_date']
            attrs = {
                "class": "table table-hover table-striped table-condensed",
                "id": name[0].title()[:2]+name[1].title()[:2]+"_conn"}

        def __init__(self, *args, entity='None', **kwargs):
            self.base_columns['delete'] = tables.TemplateColumn(
                template_name='delete_button_generic_ajax_form.html'
            )
            self.base_columns['related_'+rel_ent.lower()] = tables.LinkColumn(
                'entities:generic_entities_edit_view',
                args=[
                    rel_ent.lower(), A('related_{}.pk'.format(rel_ent.lower()))
                ])
            if name[0] == name[1]:
                self.base_columns['relation_type'] = tables.Column()
            else:
                self.base_columns['relation_type'] = tables.Column(
                    verbose_name='relation type', accessor='relation_type.{}'.format(rel_type))
            self.base_columns['edit'] = tables.TemplateColumn(
                template_name='edit_button_generic_ajax_form.html'
            )
            super(GenericRelationsTable, self).__init__(*args, **kwargs)
            self.sequence = (
                'delete', 'start_date', 'end_date', 'relation_type',
                'related_' + rel_ent.lower(), 'edit'
            )

    if detail:

        class GenericRelationsDetailTable(GenericRelationsTable):

            class Meta:
                empty_text = empty_text_default
                model = ct.model_class()
                fields = ['start_date', 'end_date']
                attrs = {
                    "class": "table table-hover table-striped table-condensed",
                    "id": name[0].title()[:2]+name[1].title()[:2]+"_conn"}

            def __init__(self, *args, entity='None', **kwargs):
                self.base_columns['related_'+rel_ent.lower()] = tables.LinkColumn(
                    'entities:generic_entities_detail_view',
                    args=[
                        rel_ent.lower(), A('related_{}.pk'.format(rel_ent.lower()))
                    ])
                if name[0] == name[1]:
                    self.base_columns['relation_type'] = tables.Column()
                else:
                    self.base_columns['relation_type'] = tables.Column(
                        verbose_name='relation type', accessor='relation_type.{}'.format(rel_type))
                super(GenericRelationsTable, self).__init__(*args, **kwargs)
                self.sequence = (
                    'start_date', 'end_date', 'relation_type', 'related_' + rel_ent.lower()
                )
        return GenericRelationsDetailTable
    else:
        return GenericRelationsTable


class PersonInstitutionTable(tables.Table):
    delete = tables.TemplateColumn(template_name='delete_button_persInstitution_ajax_form.html')
    related_institution = tables.LinkColumn('entities:institution_edit', args=[A('related_institution.pk')])
    related_person = tables.LinkColumn('entities:person_edit', args=[A('related_person.pk')])
    relation_type2 = tables.Column(verbose_name='relation type', accessor='relation_type.label_reverse')
    relation_type = tables.Column(verbose_name='relation type', accessor='relation_type.label')
    revision = tables.TemplateColumn(template_name='rev_button_persInst_ajax_form.html')
    edit = tables.TemplateColumn(template_name='edit_button_persInst_ajax_form.html')

    class Meta:
        empty_text = empty_text_default
        model = PersonInstitution
        fields = [
            'start_date', 'end_date',
            'relation_type', 'related_institution', 'related_person']
        sequence = ('delete', 'start_date', 'end_date', 'relation_type', 'relation_type2',
                    'related_institution', 'related_person')
        # add class="paleblue" to <table> tag
        attrs = {
            "class": "table table-hover table-striped table-condensed",
            "id": "PI_conn"}

    def __init__(self, *args, entity='Person', **kwargs):
        super(PersonInstitutionTable, self).__init__(*args, **kwargs)
        if entity == 'Person':
            self.exclude = ['related_person', 'relation_type2']
        elif entity == 'Institution':
            self.exclude = ['related_institution', 'relation_type']


class PersonPlaceTable(tables.Table):
    delete = tables.TemplateColumn(template_name='delete_button_persPlace_ajax_form.html')
    related_place = tables.LinkColumn('entities:place_edit', args=[A('related_place.pk')])
    related_person = tables.LinkColumn('entities:person_edit', args=[A('related_person.pk')])
    relation_type = tables.Column(verbose_name='relation type', accessor='relation_type.label')
    relation_type2 = tables.Column(verbose_name='relation type', accessor='relation_type.label_reverse')
    revision = tables.TemplateColumn(template_name='rev_button_persPlace_ajax_form.html')
    edit = tables.TemplateColumn(template_name='edit_button_persPlace_ajax_form.html')
    prefix = 'PPL-'

    class Meta:
        empty_text = empty_text_default
        model = PersonPlace
        fields = ['start_date', 'end_date', 'relation_type', 'related_place', 'related_person']
        sequence = ('delete', 'start_date', 'end_date', 'relation_type', 'relation_type2',
                    'related_place', 'related_person')
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed",
                "id": "PPL_conn"}

    def __init__(self, *args, entity='Person', **kwargs):
        super(PersonPlaceTable, self).__init__(*args, **kwargs)
        if entity == 'Person':
            self.exclude = ['related_person', 'relation_type2']
        elif entity == 'Place':
            self.exclude = ['related_place', 'relation_type']


class PersonPersonTable(tables.Table):
    delete = tables.TemplateColumn(template_name='delete_button_persPerson_ajax_form.html')
    related_person = tables.LinkColumn('entities:person_edit', args=[A('related_person.pk')])
    start_date = tables.DateColumn(verbose_name='start date')
    end_date = tables.DateColumn(verbose_name='end date')
    relation_type = tables.Column()
    revision = tables.TemplateColumn(template_name='rev_button_persPers_ajax_form.html')
    edit = tables.TemplateColumn(template_name='edit_button_persPers_ajax_form.html')

    class Meta:
        empty_text = empty_text_default
        attrs = {"class": "table table-hover table-striped table-condensed",
                "id": "PP_conn"}
        sequence = ('delete', 'start_date', 'end_date', 'relation_type',
                    'related_person')


class EntityDetailViewLabelTable(tables.Table):
    label2 = tables.Column(accessor='label')

    class Meta:
        empty_text = empty_text_default
        model = Label
        fields = ['isoCode_639_3', 'label_type']
        sequence = ('label2', 'label_type', 'isoCode_639_3')
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed",
                "id": "PL_conn"}



class EntityLabelTable(tables.Table):
    edit = tables.TemplateColumn(template_name='edit_button_persLabel_ajax_form.html')
    label2 = tables.Column(accessor='label')

    class Meta:
        empty_text = empty_text_default
        model = Label
        fields = ['isoCode_639_3', 'label_type']
        sequence = ('label2', 'label_type', 'isoCode_639_3')
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed",
                "id": "PL_conn"}


class PersonEventTable(tables.Table):
    delete = tables.TemplateColumn(template_name='delete_button_persEvent_ajax_form.html')
    related_event = tables.LinkColumn('entities:event_edit', args=[A('related_event.pk')])
    related_person = tables.LinkColumn('entities:person_edit', args=[A('related_person.pk')])
    relation_type = tables.Column(verbose_name='relation type', accessor='relation_type.label')
    relation_type2 = tables.Column(verbose_name='relation type', accessor='relation_type.label_reverse')
    revision = tables.TemplateColumn(template_name='rev_button_persEvent_ajax_form.html')
    edit = tables.TemplateColumn(template_name='edit_button_persEvent_ajax_form.html')
    prefix = 'PE-'

    class Meta:
        empty_text = empty_text_default
        model = PersonEvent
        fields = ['start_date', 'end_date', 'relation_type', 'related_event', 'related_person']
        sequence = ('delete', 'start_date', 'end_date', 'relation_type', 'relation_type2',
                    'related_event', 'related_person')
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed",
                 "id": "PEV_conn"}

    def __init__(self, *args, entity='Person', **kwargs):
        super(PersonEventTable, self).__init__(*args, **kwargs)
        if entity == 'Person':
            self.exclude = ['related_person', 'relation_type2']
        elif entity == 'Event':
            self.exclude = ['related_event', 'relation_type']


class PersonWorkTable(tables.Table):
    delete = tables.TemplateColumn(template_name='delete_button_persWork_ajax_form.html')
    related_work = tables.LinkColumn('entities:work_edit', args=[A('related_work.pk')])
    related_person = tables.LinkColumn('entities:person_edit', args=[A('related_person.pk')])
    relation_type = tables.Column(verbose_name='relation type', accessor='relation_type.label')
    relation_type2 = tables.Column(verbose_name='relation type', accessor='relation_type.label_reverse')
    revision = tables.TemplateColumn(template_name='rev_button_persWork_ajax_form.html')
    edit = tables.TemplateColumn(template_name='edit_button_persWork_ajax_form.html')

    class Meta:
        empty_text = empty_text_default
        model = PersonWork
        fields = [
            'start_date', 'end_date',
            'relation_type', 'related_work', 'related_person']
        sequence = ('delete', 'start_date', 'end_date', 'relation_type', 'relation_type2',
                    'related_work', 'related_person')
        # add class="paleblue" to <table> tag
        attrs = {
            "class": "table table-hover table-striped table-condensed",
            "id": "PWRK_conn"}

    def __init__(self, *args, entity='Person', **kwargs):
        super(PersonWorkTable, self).__init__(*args, **kwargs)
        if entity == 'Person':
            self.exclude = ['related_person', 'relation_type2']
        elif entity == 'Work':
            self.exclude = ['related_work', 'relation_type']


class EntityUriTable(tables.Table):
    delete = tables.TemplateColumn(template_name='delete_button_Uri_ajax_form.html')

    class Meta:
        empty_text = empty_text_default
        model = Uri
        fields = ['uri']
        sequence = ('delete', 'uri')
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed",
                 "id": "PURI_conn"}


############################################################################
############################################################################
#
#   Institution Tables
#
############################################################################
############################################################################


class InstitutionPlaceTable(tables.Table):
    delete = tables.TemplateColumn(template_name='delete_button_instPlace_ajax_form.html')
    related_place = tables.LinkColumn('entities:place_edit', args=[A('related_place.pk')])
    related_institution = tables.LinkColumn('entities:institution_edit', args=[A('related_institution.pk')])
    relation_type = tables.Column(verbose_name='relation type', accessor='relation_type.label')
    relation_type2 = tables.Column(verbose_name='relation type', accessor='relation_type.label_reverse')
    revision = tables.TemplateColumn(template_name='rev_button_instPlace_ajax_form.html')
    edit = tables.TemplateColumn(template_name='edit_button_instPlace_ajax_form.html')
    prefix = 'IPL-'

    class Meta:
        empty_text = empty_text_default
        model = InstitutionPlace
        fields = ['start_date', 'end_date', 'relation_type', 'related_place', 'related_institution']
        sequence = ('delete', 'start_date', 'end_date', 'relation_type', 'relation_type2',
                    'related_place', 'related_institution')
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed",
                "id": "IPL_conn"}

    def __init__(self, *args, entity='Institution', **kwargs):
        super(InstitutionPlaceTable, self).__init__(*args, **kwargs)
        if entity == 'Institution':
            self.exclude = ['related_institution', 'relation_type2']
        elif entity == 'Place':
            self.exclude = ['related_place', 'relation_type']


class InstitutionInstitutionTable(tables.Table):
    delete = tables.TemplateColumn(template_name='delete_button_instInst_ajax_form.html')
    related_institution = tables.LinkColumn('entities:institution_edit', args=[A('related_institution.pk')])
    start_date = tables.DateColumn(verbose_name='start date')
    end_date = tables.DateColumn(verbose_name='end date')
    relation_type = tables.Column()
    revision = tables.TemplateColumn(template_name='rev_button_instInst_ajax_form.html')
    edit = tables.TemplateColumn(template_name='edit_button_instInst_ajax_form.html')

    class Meta:
        empty_text = empty_text_default
        attrs = {"class": "table table-hover table-striped table-condensed",
                 "id": "II_conn"}
        sequence = ('delete', 'start_date', 'end_date', 'relation_type',
                    'related_institution')


class InstitutionEventTable(tables.Table):
    delete = tables.TemplateColumn(template_name='delete_button_instEvent_ajax_form.html')
    related_event = tables.LinkColumn('entities:event_edit', args=[A('related_event.pk')])
    related_institution = tables.LinkColumn('entities:institution_edit', args=[A('related_institution.pk')])
    relation_type = tables.Column(verbose_name='relation type', accessor='relation_type.label')
    relation_type2 = tables.Column(verbose_name='relation type', accessor='relation_type.label_reverse')
    revision = tables.TemplateColumn(template_name='rev_button_instEvent_ajax_form.html')
    edit = tables.TemplateColumn(template_name='edit_button_instEvent_ajax_form.html')
    prefix = 'IEV-'

    class Meta:
        empty_text = empty_text_default
        model = InstitutionEvent
        fields = ['start_date', 'end_date', 'relation_type', 'related_event', 'related_institution']
        sequence = ('delete','start_date', 'end_date', 'relation_type', 'relation_type2',
                    'related_event', 'related_institution', 'edit')
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed",
                 "id": "IEV_conn"}

    def __init__(self, *args, entity='Institution', **kwargs):
        super(InstitutionEventTable, self).__init__(*args, **kwargs)
        if entity == 'Institution':
            self.exclude = ['related_institution', 'relation_type2']
        elif entity == 'Event':
            self.exclude = ['related_event', 'relation_type']


class InstitutionWorkTable(tables.Table):
    delete = tables.TemplateColumn(template_name='delete_button_instWork_ajax_form.html')
    related_work = tables.LinkColumn('entities:work_edit', args=[A('related_work.pk')])
    related_institution = tables.LinkColumn('entities:institution_edit', args=[A('related_institution.pk')])
    relation_type = tables.Column(verbose_name='relation type', accessor='relation_type.label')
    relation_type2 = tables.Column(verbose_name='relation type', accessor='relation_type.label_reverse')
    revision = tables.TemplateColumn(template_name='rev_button_instWork_ajax_form.html')
    edit = tables.TemplateColumn(template_name='edit_button_instWork_ajax_form.html')

    class Meta:
        empty_text = empty_text_default
        model = InstitutionWork
        fields = [
            'start_date', 'end_date',
            'relation_type', 'related_work', 'related_institution']
        sequence = ('delete', 'start_date', 'end_date', 'relation_type', 'relation_type2',
                    'related_work', 'related_institution')
        # add class="paleblue" to <table> tag
        attrs = {
            "class": "table table-hover table-striped table-condensed",
            "id": "IWRK_conn"}

    def __init__(self, *args, entity='Institution', **kwargs):
        super(InstitutionWorkTable, self).__init__(*args, **kwargs)
        if entity == 'Institution':
            self.exclude = ['related_institution', 'relation_type2']
        elif entity == 'Work':
            self.exclude = ['related_work', 'relation_type']


############################################################################
############################################################################
#
#   Place Tables
#
############################################################################
############################################################################


class PlaceEventTable(tables.Table):
    delete = tables.TemplateColumn(template_name='delete_button_placeEvent_ajax_form.html')
    related_event = tables.LinkColumn('entities:event_edit', args=[A('related_event.pk')])
    related_place = tables.LinkColumn('entities:place_edit', args=[A('related_place.pk')])
    relation_type = tables.Column(verbose_name='relation type', accessor='relation_type.label')
    relation_type2 = tables.Column(verbose_name='relation type', accessor='relation_type.label_reverse')
    revision = tables.TemplateColumn(template_name='rev_button_placeEvent_ajax_form.html')
    edit = tables.TemplateColumn(template_name='edit_button_placeEvent_ajax_form.html')
    prefix = 'PLEV-'

    class Meta:
        empty_text = empty_text_default
        model = PlaceEvent
        fields = ['start_date', 'end_date', 'relation_type', 'related_event', 'related_place']
        sequence = ('delete', 'start_date', 'end_date', 'relation_type', 'relation_type2',
                    'related_event', 'related_place', 'edit')
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed",
                 "id": "PLEV_conn"}

    def __init__(self, *args, entity='Place', **kwargs):
        super(PlaceEventTable, self).__init__(*args, **kwargs)
        if entity == 'Place':
            self.exclude = ['related_place', 'relation_type2']
        elif entity == 'Event':
            self.exclude = ['related_event', 'relation_type']


class PlacePlaceTable(tables.Table):
    delete = tables.TemplateColumn(template_name='delete_button_placePlace_ajax_form.html')
    related_place = tables.LinkColumn('entities:place_edit', args=[A('related_place.pk')])
    start_date = tables.DateColumn(verbose_name='start date')
    end_date = tables.DateColumn(verbose_name='end date')
    relation_type = tables.Column()
    revision = tables.TemplateColumn(template_name='rev_button_placePlace_ajax_form.html')
    edit = tables.TemplateColumn(template_name='edit_button_placePlace_ajax_form.html')

    class Meta:
        empty_text = empty_text_default
        attrs = {"class": "table table-hover table-striped table-condensed",
                "id": "PP_conn"}
        sequence = ('delete', 'start_date', 'end_date', 'relation_type',
                    'related_place')


class PlaceWorkTable(tables.Table):
    delete = tables.TemplateColumn(template_name='delete_button_placeWork_ajax_form.html')
    related_work = tables.LinkColumn('entities:work_edit', args=[A('related_work.pk')])
    related_place = tables.LinkColumn('entities:place_edit', args=[A('related_place.pk')])
    relation_type = tables.Column(verbose_name='relation type', accessor='relation_type.label')
    relation_type2 = tables.Column(verbose_name='relation type', accessor='relation_type.label_reverse')
    revision = tables.TemplateColumn(template_name='rev_button_placeWork_ajax_form.html')
    edit = tables.TemplateColumn(template_name='edit_button_placeWork_ajax_form.html')

    class Meta:
        empty_text = empty_text_default
        model = PlaceWork
        fields = [
            'start_date', 'end_date',
            'relation_type', 'related_work', 'related_place']
        sequence = ('delete', 'start_date', 'end_date', 'relation_type', 'relation_type2',
                    'related_work', 'related_place')
        # add class="paleblue" to <table> tag
        attrs = {
            "class": "table table-hover table-striped table-condensed",
            "id": "PWRK_conn"}

    def __init__(self, *args, entity='Place', **kwargs):
        super(PlaceWorkTable, self).__init__(*args, **kwargs)
        if entity == 'Place':
            self.exclude = ['related_place', 'relation_type2']
        elif entity == 'Work':
            self.exclude = ['related_work', 'relation_type']


############################################################################
############################################################################
#
#   Event Tables
#
############################################################################
############################################################################


class EventWorkTable(tables.Table):
    delete = tables.TemplateColumn(template_name='delete_button_eventWork_ajax_form.html')
    related_work = tables.LinkColumn('entities:work_edit', args=[A('related_work.pk')])
    related_event = tables.LinkColumn('entities:event_edit', args=[A('related_event.pk')])
    relation_type = tables.Column(verbose_name='relation type', accessor='relation_type.label')
    relation_type2 = tables.Column(verbose_name='relation type', accessor='relation_type.label_reverse')
    revision = tables.TemplateColumn(template_name='rev_button_eventWork_ajax_form.html')
    edit = tables.TemplateColumn(template_name='edit_button_eventWork_ajax_form.html')

    class Meta:
        empty_text = empty_text_default
        model = EventWork
        fields = [
            'start_date', 'end_date',
            'relation_type', 'related_work', 'related_event']
        sequence = ('delete', 'start_date', 'end_date', 'relation_type', 'relation_type2',
                    'related_work', 'related_event')
        # add class="paleblue" to <table> tag
        attrs = {
            "class": "table table-hover table-striped table-condensed",
            "id": "EWRK_conn"}

    def __init__(self, *args, entity='Event', **kwargs):
        super(EventWorkTable, self).__init__(*args, **kwargs)
        if entity == 'Event':
            self.exclude = ['related_event', 'relation_type2']
        elif entity == 'Work':
            self.exclude = ['related_work', 'relation_type']
