import django_tables2 as tables
from django_tables2.utils import A
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.utils.safestring import mark_safe

from .models import Person, Place, Institution, Event, Work

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


def get_entities_table(entity, edit_v, default_cols=['name', ]):

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

        class Meta:
            model = ContentType.objects.get(
                app_label__startswith='apis_', model=entity.lower()).model_class()
            fields = default_cols
            attrs = {"class": "table table-hover table-striped table-condensed"}
    return GenericEntitiesTable


class PersonTable(tables.Table):
    name = tables.LinkColumn('apis:apis_entities:person_edit', args=[A('pk')])

    class Meta:
        model = Person
        fields = ['name', 'first_name', 'start_date', 'end_date']
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed"}


class PlaceTable(tables.Table):
    name = tables.LinkColumn('apis:apis_entities:place_edit', args=[A('pk')])

    class Meta:
        model = Place
        fields = ['name', 'status', 'lng', 'lat']
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed"}


class InstitutionTable(tables.Table):
    name = tables.LinkColumn('apis:apis_entities:institution_edit', args=[A('pk')])

    class Meta:
        model = Institution
        fields = ['name', 'start_date', 'end_date', 'kind']
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed"}


class EventTable(tables.Table):
    name = tables.LinkColumn('apis:apis_entities:event_edit', args=[A('pk')])

    class Meta:
        model = Event
        fields = ['name', 'start_date', 'end_date', 'kind']
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed"}


class WorkTable(tables.Table):
    name = tables.LinkColumn('apis:apis_entities:work_edit', args=[A('pk')])

    class Meta:
        model = Work
        fields = ['name', 'start_date', 'end_date', 'kind']
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed"}
