import django_tables2 as tables
from django_tables2.utils import A
from django.conf import settings
from django.utils.safestring import mark_safe
from apis_core.apis_entities.models import AbstractEntity
from apis_core.apis_metainfo.tables import generic_order_start_date_written, generic_order_end_date_written

input_form = """
  <input type="checkbox" name="keep" value="{}" title="keep this"/> |
  <input type="checkbox" name="remove" value="{}" title="remove this"/>
"""


class MergeColumn(tables.Column):
    """ renders a column with to checkbox - used to select objects for merging """

    def __init__(self, *args, **kwargs):
        super(MergeColumn, self).__init__(*args, **kwargs)

    def render(self, value):
        return mark_safe(
            input_form.format(value, value)
        )


def get_entities_table(entity, edit_v, default_cols):

    if default_cols is None:
        default_cols = ['name', ]

    class GenericEntitiesTable(tables.Table):
        if edit_v:
            name = tables.LinkColumn(
                'apis:apis_entities:generic_entities_edit_view',
                args=[entity.lower(), A('pk')]
            )
        else:
            name = tables.LinkColumn(
                'apis:apis_entities:generic_entities_detail_view',
                args=[entity.lower(), A('pk')]
            )
        export_formats = [
            'csv',
            'json',
            'xls',
            'xlsx',
        ]
        if 'merge' in default_cols:
            merge = MergeColumn(verbose_name='keep | remove', accessor='pk')
        if 'id' in default_cols:
            id = tables.LinkColumn()

        # reuse the logic for ordering *_date_written by their parsed dates.
        # Important: The names of these class variables must correspond to the column field name
        order_start_date_written = generic_order_start_date_written
        order_end_date_written = generic_order_end_date_written

        class Meta:
            model = AbstractEntity.get_entity_class_of_name(entity_name=entity)

            fields = default_cols
            attrs = {"class": "table table-hover table-striped table-condensed"}


        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)


    return GenericEntitiesTable


