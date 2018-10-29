import django_tables2 as tables
from django_tables2.utils import A
from .models import Person, Place, Institution, Event, Work
from django.contrib.contenttypes.models import ContentType
from django.conf import settings


def get_entities_table(entity, edit_v):

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
            id = tables.LinkColumn()
        export_formats = [
            'csv',
            'json',
            'xls',
            'xlsx',
        ]

        class Meta:
            model = ContentType.objects.get(
                app_label__startswith='apis_', model=entity.lower()).model_class()
            if 'table_fields' in settings.APIS_ENTITIES[entity.title()]:
                fields = settings.APIS_ENTITIES[entity.title()]['table_fields']
            else:
                exclude = (
                    'MetaInfo',
                    'collection',
                    'references',
                    'notes',
                    'review',
                    'start_date',
                    'end_date',
                    'source',
                    'tempentityclass_ptr',
                )
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
