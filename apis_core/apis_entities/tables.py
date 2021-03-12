import django_tables2 as tables
from django.utils.safestring import mark_safe
from django_tables2.utils import A

from apis_core.apis_entities.models import AbstractEntity
from apis_core.apis_metainfo.tables import (
    generic_order_start_date_written,
    generic_order_end_date_written,
    generic_render_start_date_written,
    generic_render_end_date_written
)

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

        def render_name(self, record, value):
            if value == "":
                return "(No name provided)"
            else:
                return value

        # reuse the logic for ordering and rendering *_date_written
        # Important: The names of these class variables must correspond to the column field name,
        # e.g. for start_date_written, the methods must be named order_start_date_written and render_start_date_written
        order_start_date_written = generic_order_start_date_written
        order_end_date_written = generic_order_end_date_written
        render_start_date_written = generic_render_start_date_written
        render_end_date_written = generic_render_end_date_written

        if edit_v:
            name = tables.LinkColumn(
                'apis:apis_entities:generic_entities_edit_view',
                args=[entity.lower(), A('pk')],
                empty_values=[]
            )
        else:
            name = tables.LinkColumn(
                'apis:apis_entities:generic_entities_detail_view',
                args=[entity.lower(), A('pk')],
                empty_values=[]
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

        class Meta:
            model = AbstractEntity.get_entity_class_of_name(entity_name=entity)

            fields = default_cols
            attrs = {"class": "table table-hover table-striped table-condensed"}

            # quick ensurance if column is indeed a field of this entity
            for col in default_cols:
                if not hasattr(model, col):
                    raise Exception(
                        f"Could not find field in entity: {entity}\n"
                        f"of column (probably defined in 'table_fields' settings): {col}\n"
                    )

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    return GenericEntitiesTable


