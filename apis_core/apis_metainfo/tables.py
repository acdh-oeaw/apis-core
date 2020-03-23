import django_tables2 as tables
from django.db.models import F
from . models import Uri



# generic order_FOO methods for start_date_written and end_date_written to be used in all kinds of tables where a queryset is loaded
# whose model has start_date_written and end_date_written. These methods order the *_date_written by their corresponding
# parsed date objects.
#
# In order to use them in a table using django-tables2, the table class must be assigned *_date_written columns
# (either through fields in Meta inner class or through custom Column() definitions).
# Important however is that the names between the columns and the order methods are correlated to each other.
#
# The django-tables2 plugin searches for each column through the table class for corresponding order_* and render_* methods
# E.g. to define custom ordering and rendering for a field column 'name' the table class must have
# 'order_name' and 'render_name' methods. This approach is called order_FOO and render_FOO by django-tables2.
#
# So in order to use these functions here, define within the table class
# 1.) the respective column
# 2.) a correspondingly named method for each column
# 3.) assign to this method one of the two functions below
#
# In the case of e.g. start_date_written,
# the table class thus must have a method / class variable 'order_start_date_written = generic_order_start_date_written'

def generic_order_start_date_written(self, queryset, is_descending):
    if is_descending:
        queryset = queryset.order_by(F("start_date").desc(nulls_last=True)) #nulls_last=True puts null values behind non-null values
    else:
        queryset = queryset.order_by(F("start_date").asc(nulls_last=True))

    return (queryset, True)


def generic_order_end_date_written(self, queryset, is_descending):
    if is_descending:
        queryset = queryset.order_by(F("end_date").desc(nulls_last=True))
    else:
        queryset = queryset.order_by(F("end_date").asc(nulls_last=True))

    return (queryset, True)



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
