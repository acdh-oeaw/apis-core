import django_tables2 as tables
from django_tables2.utils import A

from . models import *


class UriTable(tables.Table):
    id = tables.LinkColumn()

    class Meta:
        model = Uri
        sequence = ('id',)
        attrs = {"class": "table table-responsive table-hover"}
