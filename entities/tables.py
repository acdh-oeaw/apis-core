import django_tables2 as tables
from django_tables2.utils import A
from .models import Person, Place, Institution, Event, Work


class PersonTable(tables.Table):
    name = tables.LinkColumn('entities:person_edit', args=[A('pk')])

    class Meta:
        model = Person
        fields = ['name', 'first_name', 'start_date', 'end_date']
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed"}


class PlaceTable(tables.Table):
    name = tables.LinkColumn('entities:place_edit', args=[A('pk')])

    class Meta:
        model = Place
        fields = ['name', 'status', 'lng', 'lat']
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed"}


class InstitutionTable(tables.Table):
    name = tables.LinkColumn('entities:institution_edit', args=[A('pk')])

    class Meta:
        model = Institution
        fields = ['name', 'start_date', 'end_date', 'kind']
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed"}


class EventTable(tables.Table):
    name = tables.LinkColumn('entities:event_edit', args=[A('pk')])

    class Meta:
        model = Event
        fields = ['name', 'start_date', 'end_date', 'kind']
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed"}


class WorkTable(tables.Table):
    name = tables.LinkColumn('entities:work_edit', args=[A('pk')])

    class Meta:
        model = Work
        fields = ['name', 'start_date', 'end_date', 'kind']
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed"}
