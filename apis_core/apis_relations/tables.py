import django_tables2 as tables
from django.contrib.contenttypes.models import ContentType
from django_tables2.utils import A

from .models import (
    PersonInstitution, PersonPlace, PersonPerson, PersonEvent, InstitutionEvent, PlaceEvent,
    PersonWork, InstitutionWork, InstitutionPlace, PlaceWork, EventWork
)
from apis_core.apis_labels.models import Label
from apis_core.apis_metainfo.models import Uri


empty_text_default = 'There are currently no relations'


def get_generic_relation_listview_table(relation):
    ct = ContentType.objects.get(app_label='apis_relations', model=relation.lower())
    relation_model_class = ct.model_class()
    model_fields = relation_model_class._meta.get_fields(include_parents=False)
    field_names = [x.name for x in model_fields[1:]]
    all_field_names = field_names + ['start_date', 'end_date']

    class GenericRelationListViewTable(tables.Table):

        class Meta:
            model = relation_model_class
            fields = all_field_names
            attrs = {"class": "table table-hover table-striped table-condensed"}

        def __init__(self, *args, **kwargs):
            ent_first = all_field_names[1]
            ent_second = all_field_names[2]
            self.base_columns[all_field_names[1]] = tables.LinkColumn()
            self.base_columns[all_field_names[2]] = tables.LinkColumn()
            super(GenericRelationListViewTable, self).__init__(*args, **kwargs)

    return GenericRelationListViewTable


def get_generic_relations_table(relation, entity, detail=None):
    ct = ContentType.objects.get(app_label='apis_relations', model=relation.lower())
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
                template_name='apis_relations/delete_button_generic_ajax_form.html'
            )
            self.base_columns['related_'+rel_ent.lower()] = tables.LinkColumn(
                'apis:apis_entities:generic_entities_edit_view',
                args=[
                    rel_ent.lower(), A('related_{}.pk'.format(rel_ent.lower()))
                ])
            if name[0] == name[1]:
                self.base_columns['relation_type'] = tables.Column()
            else:
                self.base_columns['relation_type'] = tables.Column(
                    verbose_name='relation type', accessor='relation_type.{}'.format(rel_type))
            self.base_columns['edit'] = tables.TemplateColumn(
                template_name='apis_relations/edit_button_generic_ajax_form.html'
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
                    'apis:apis_entities:generic_entities_detail_view',
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


class EntityUriTable(tables.Table):
    delete = tables.TemplateColumn(template_name='apis_relations/delete_button_Uri_ajax_form.html')

    class Meta:
        empty_text = empty_text_default
        model = Uri
        fields = ['uri']
        sequence = ('delete', 'uri')
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed",
                 "id": "PURI_conn"}


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
    edit = tables.TemplateColumn(template_name='apis_relations/edit_button_persLabel_ajax_form.html')
    label2 = tables.Column(accessor='label')

    class Meta:
        empty_text = empty_text_default
        model = Label
        fields = ['isoCode_639_3', 'label_type']
        sequence = ('label2', 'label_type', 'isoCode_639_3')
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed",
                "id": "PL_conn"}
