import django_tables2 as tables
from django.db.models import F
from django.utils.html import format_html

from .models import Uri


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



def helper_render_date(value, var_date, var_start_date, var_end_date):
    """
    helper function to avoid duplicated code. It checks the various sub-dates of a model's date field for them being None
    or having values. If a field is None then check for the next, and if all are None, return '—' inditcating no value.

    If there are values, use them as mouse overlay helptext to inform the user about the parsing result behind a written
    date field.

    :param value: str : the *_date_written (either start_date_written or end_date_written) field of an entity or relation
    :param var_date: datetime : either the precisely parsed date or the average in between two dates when *_date_written is a range
    :param var_start_date: datetime : The sub-date of var_date, indicating the start date of the range
    :param var_end_date: datetime : The sub-date of var_date, indicating the end date of the range
    :return: html string : which has the value of the written date and the parsed dates as mouse overlay helptext
    """


    # Various if-else branches checking which of the date fields are not None and should be used

    if var_start_date != None and var_end_date != None:

        overlay_help_text = str(var_start_date) + " - " + str(var_end_date)

    elif var_date != None:

        overlay_help_text = str(var_date)

    else:

        return "—"

    return format_html("<abbr title='" + overlay_help_text + "'>" + value + "</b>")


# Again this function serves a generic purpose and must be assigned as class method to django-tables2 tables.Table class
# The whole logic is very similare to the generic_order_* functions above, so see their comments for more details.
def generic_render_start_date_written(self, record, value):

    return helper_render_date(
        value = value,
        var_date = record.start_date,
        var_start_date = record.start_start_date,
        var_end_date = record.start_end_date
    )


def generic_render_end_date_written(self, record, value):

    return helper_render_date(
        value = value,
        var_date = record.end_date,
        var_start_date = record.end_start_date,
        var_end_date = record.end_end_date
    )




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
