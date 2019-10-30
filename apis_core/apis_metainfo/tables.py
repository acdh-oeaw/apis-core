import django_tables2 as tables
from django_tables2.utils import A

from . models import *


class UriTable(tables.Table):
    id = tables.LinkColumn()
    entity = tables.TemplateColumn(
        "<a href='{{ record.entity.get_absolute_url }}'>{{ record.entity }}</a>",
        orderable=True, verbose_name="related Entity"
    )
    ent_type = tables.TemplateColumn(
        "{{ record.entity.get_child_class }}",
        orderable=False, verbose_name="Entity Type"
    )

    class Meta:
        model = Uri
        sequence = ('id', 'uri')
        attrs = {"class": "table table-responsive table-hover"}
