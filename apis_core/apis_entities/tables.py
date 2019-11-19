import django_tables2 as tables
from django.db.models import Q
from django_tables2.utils import A
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.utils.safestring import mark_safe


from .models import Person, Place, Institution, Event, Passage

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

        if entity.lower() == "passage" or entity.lower() == "publication":
            person_set = tables.Column(verbose_name="Urheber")

        class Meta:
            model = ContentType.objects.get(
                app_label__startswith='apis_', model=entity.lower()).model_class()

            fields = None

            # TODO __sresch__ : prototype for now; implement this better
            if model.__name__ == "Passage" or model.__name__ == "Publication":
                fields = ['person_set'] + default_cols
            else:
                fields = default_cols
            attrs = {"class": "table table-hover table-striped table-condensed"}

        # TODO __sresch__ : prototype for now; implement this better
        def render_person_set(self, record):

            from apis_core.apis_vocabularies.models import PersonPublicationRelation
            from apis_core.apis_vocabularies.models import PassagePublicationRelation

            urheber_relation = PersonPublicationRelation.objects.get(name="ist Urheber von")

            if record.__class__.__name__ == "Publication":

                urheber = record.person_set.filter( Q(publication_relationtype_set=urheber_relation) & Q(publication_set=record))

                result_string = ", ".join([str(p.name) for p in urheber])

                return result_string

            elif record.__class__.__name__ == "Passage":

                pubs = record.publication_set.all()

                urheber_list = []

                for pub in pubs:
                    urheber = pub.person_set.filter( Q(publication_relationtype_set=urheber_relation) & Q(publication_set=pub))
                    urheber_list.extend(list(urheber.all()))

                result_string = ", ".join([str(p.name) for p in urheber_list])

                return result_string

            else:

                return "-"


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


class PassageTable(tables.Table):
    name = tables.LinkColumn('apis:apis_entities:passage_edit', args=[A('pk')])

    class Meta:
        model = Passage
        fields = ['name', 'start_date', 'end_date', 'kind']
        # add class="paleblue" to <table> tag
        attrs = {"class": "table table-hover table-striped table-condensed"}
