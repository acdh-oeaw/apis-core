import django_tables2 as tables
from django_tables2.utils import A
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.utils.safestring import mark_safe
from django.db import models
from django.db.models import Subquery, OuterRef, F, Q
from apis_core.apis_vocabularies.models import PersonPublicationRelation
from apis_core.apis_vocabularies.models import PassagePublicationRelation
from apis_core.apis_entities.models import AbstractEntity
from apis_core.apis_metainfo.tables import (
    generic_order_start_date_written,
    generic_order_end_date_written,
    generic_render_start_date_written,
    generic_render_end_date_written
)
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


class UrheberColumn(tables.Column):
    """
    A custom column showing the author (Urheber) of either a passage or a publication as desired in the SOLA project.
    In both cases traversal must be done and the right relation type selected for,
    in order to show the person instance who is the author.
    """

    def __init__(self, *args, **kwargs):
        """
        In the init method, get the relevant relation types first and reuse them as to to make only one db call.
        These will be used later for filtering in the 'render' and 'order' method.
        """

        # The relevant author relation between a publication and a person
        urheber_person_publication_relation = PersonPublicationRelation.objects.filter(name="ist Urheber von")
        if len(urheber_person_publication_relation) == 1:
            self.urheber_person_publication_relation = urheber_person_publication_relation[0]
        else:
            self.urheber_person_publication_relation = None

        # The relevant 'containing' relation between a passage and a publication
        # (to use the publication and then again to find the author of the publication)
        ist_enthalten_passage_publication_relation = PassagePublicationRelation.objects.filter(name="ist enthalten in")
        if len(ist_enthalten_passage_publication_relation) == 1:
            self.ist_enthalten_passage_publication_relation = ist_enthalten_passage_publication_relation[0]
        else:
            self.ist_enthalten_passage_publication_relation = None

        super().__init__(*args, **kwargs)


    def render(self, record):
        """
        Render method of how individual row cells of the table are to be displayed.

        :param record: the entity instance which' data will be used to populate the current table row
        :return: a string representing the value for this author column
        """

        if hasattr(record, "urheber"):
            # If the 'order' method was called before, the queryset got already annotated and no further querying towards
            # the respective author of a passage or publication is necessary. Thus only reuse the annotation 'urheber'

            if record.urheber != None:
                # passage or publication has an author
                return record.urheber

            else:
                # passage or publication has no author
                return "-"

        else:
            # The 'order' method was not yet called. Hence do manual traversal for each row here.
            # Quite inefficient as for each row a database connection is called, but I did not find another
            # possibility.
            # Should it be possible, then encapsulating the annotation logic from the 'order' method into a dedicated method
            # would be better. Because then the annotation would be done in one db call and the 'render' and 'order' method
            # would simply use these annotations.
            # TODO : Check if it's possible to annotate the queryset with an urheber column before method 'render' or 'order' are called and how these methods can access the annotated queryset


            # Differentiate the traversal logic between publication and passage
            if record.__class__.__name__ == "Publication":

                urheber = Person.objects.filter(
                    publication_relationtype_set=self.urheber_person_publication_relation,
                    publication_set=record
                 )

                result_string = ", ".join([str(p.name) for p in urheber])

                return result_string

            elif record.__class__.__name__ == "Passage":

                urheber = Person.objects.filter(
                    publication_relationtype_set=self.urheber_person_publication_relation,
                    publication_set__passage_set=record
                )

                result_string = ", ".join([str(p.name) for p in urheber])

                return result_string

            else:
                raise Exception("UrheberColumn is only supposed to be used on publication or passage table.")


    def order(self, queryset, is_descending):
        """
        Custom method to order the whole table on the author of a passage or a publication
        """

        # The following logic uses Subquery. I would have prefered to use F() for more intuitional code such as:
        # Publication.objects.annotate(urheber=F("person_set__name"))
        #
        # but I could not get filter on the F select working, weirdly enough aggregates and filters on them work, such as:
        #  Publication.objects.annotate(urheber_count=Count("person_set__name", filter=Q(person_set__name__icontains="a")))
        #
        # Though I suspect that performance-wise there would be no relevant difference between F and Subquery usage.

        # The subqueries work in such a way that the relevant column returned by the subquery is saved into the annotation
        # 'urheber' which becomes a first class citizen field such as any other model field within the original queryset.
        # Thus it can be easily called or ordered upon.
        #
        # If this method is called before 'render' above, then the 'render' method would make use of these annotations here
        # since they are being passed this modified queryset. Then no further db calls are needed anymore.

        if queryset.model.__name__ == "Publication":

            queryset = queryset.annotate(
                urheber=Subquery( # the name of the field the results of the subquery are saved into
                    Person.objects.filter(
                        publication_relationtype_set=self.urheber_person_publication_relation,
                        publication_set=OuterRef("pk") # the field upon which the subquery joins the outer query
                    ).values("name")[:1], # take only one author since a CharField requires only one value TODO : Maybe this can be modified so that multiple are returend
                    output_field=models.CharField() # create a full CharField on the queryset for easy ordering and retrieval
                )
            )

        elif queryset.model.__name__ == "Passage":

            # comments on parameters, see above
            queryset = queryset.annotate(
                urheber=Subquery(
                    Person.objects.filter(
                        publication_relationtype_set=self.urheber_person_publication_relation,
                        publication_set__passage_set=OuterRef("pk"),
                        publication_set__passage_relationtype_set=self.ist_enthalten_passage_publication_relation,
                    ).values("name")[:1],
                    output_field=models.CharField()
                )
            )

        else:
            raise Exception("UrheberColumn is only supposed to be used on publication or passage table.")

        # Differentiate betweem given sort order
        if is_descending:
            queryset = queryset.order_by(F("urheber").desc(nulls_last=True))
        else:
            queryset = queryset.order_by(F("urheber").asc(nulls_last=True))

        return (queryset, True)


def get_entities_table(entity, edit_v, default_cols):

    if default_cols is None:
        default_cols = ['name', ]

    class GenericEntitiesTable(tables.Table):

        # reuse the logic for ordering and rendering *_date_written
        # Important: The names of these class variables must correspond to the column field name,
        # e.g. for start_date_written, the methods must be named order_start_date_written and render_start_date_written
        order_start_date_written = generic_order_start_date_written
        order_end_date_written = generic_order_end_date_written
        render_start_date_written = generic_render_start_date_written
        render_end_date_written = generic_render_end_date_written

        if entity == "Passage" or entity == "Publication":
            urheber_col = UrheberColumn(empty_values=(), verbose_name="Urheber")

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
            model = AbstractEntity.get_entity_class_of_name(entity_name=entity)

            fields = default_cols
            attrs = {"class": "table table-hover table-striped table-condensed"}


        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)


    return GenericEntitiesTable
