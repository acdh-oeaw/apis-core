import django_filters
from dal import autocomplete
from django.forms import ModelMultipleChoiceField
from django.urls import reverse

from .models import Person, Place, Institution, Event, Work
from django.db.models import Q
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

# TODO __sresch__ where is this used?
django_filters.filters.LOOKUP_TYPES = [
    ('', '---------'),
    ('icontains', 'Contains (case insensitive)'),
    ('exact', 'Is equal to'),
    ('iexact', 'Is equal to (case insensitive)'),
    ('not_exact', 'Is not equal to'),
    ('lt', 'Lesser than/before'),
    ('gt', 'Greater than/after'),
    ('gte', 'Greater than or equal to'),
    ('lte', 'Lesser than or equal to'),
    ('startswith', 'Starts with'),
    ('endswith', 'Ends with'),
    ('contains', 'Contains'),
    ('not_contains', 'Does not contain'),
]


def get_generic_list_filter(entity):

    # TODO __sresch__ : consider moving this class outside of the function call to avoid redundant class definitions
    class GenericListFilter(django_filters.FilterSet):

        def construct_lookup(self, value):
            """
            Parses user input for wildcards and returns the respective django lookup string and the trimmed value
            E.g.
                "*example" -> "__iendswith", "example"
                "example*" -> "__istartswith", "example"
                "*example*" -> "__icontains", "example"
                ""example"" -> "__exact", "example"

            :param value : str : text to be parsed for *
            :return: (lookup : str, value : str)
            """

            search_startswith = False
            search_endswith = False

            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                return "__exact", value[1:-1]

            if value.startswith("*"):
                value = value[1:]
                search_startswith = True

            if value.endswith("*"):
                value = value[:-1]
                search_endswith = True

            if search_startswith and not search_endswith:
                return "__iendswith", value

            elif not search_startswith and search_endswith:
                return "__istartswith", value

            elif search_startswith and search_endswith:
                return "__icontains", value

            else:
                return "__iexact", value


        def default_text_filter(self, queryset, name, value):

            lookup, value = self.construct_lookup(value)

            return queryset.filter(**{name+lookup : value}).distinct().order_by("name")



        def name_label_filter(self, queryset, name, value):
            """
            Filter for including the alternative names in the names search. The types of labels included in the query are
            currently hardcoded in a list.

            :param queryset: queryset that the filters are applied on
            :param name: name of the attribute to filter on (not used as label types are hardcoded)
            :param value: value for the filter
            :return: filtered queryset
            """
            alternate_names = getattr(settings, "APIS_ALTERNATE_NAMES", ['alternative name'])
            orig_value = value
            q_args = Q()

            for n in ['name', 'label__label']:
                value = orig_value

                lookup, value = self.construct_lookup(value)
                f = n + lookup

                if n == 'label__label':
                    q_args |= Q(**{f: value, 'label__label_type__name__in': alternate_names})
                else:
                    q_args |= Q(**{f: value})

            return queryset.filter( q_args ).distinct().order_by("name")



        def related_entity_name_filter(self, queryset, name, value):

            lookup, value = self.construct_lookup(value)

            q_args = Q()

            for entity_field_name in queryset.model.get_related_entity_field_names():
                q_args = q_args | Q(**{entity_field_name + "__name" + lookup: value})

            return queryset.filter(q_args).distinct().order_by("name")



        def related_relationtype_name_filter(self, queryset, name, value):

            lookup, value = self.construct_lookup(value)

            q_args = Q()

            for relationtype_field_name in queryset.model.get_related_relationtype_field_names():
                base_lookup = relationtype_field_name + "__name" + lookup
                q_args = q_args | Q(**{base_lookup: value})

            return queryset.filter(q_args).distinct().order_by("name")


        # TODO __sresch__ To my knowledge it's not possible to define such custom filter fields via settings, hence they are manually defined here
        related_entity_name = django_filters.CharFilter(method="related_entity_name_filter", label="any related entity name")
        related_relationtype_name = django_filters.CharFilter(method="related_relationtype_name_filter", label="any related relationtype name")


        class Meta:
            model = ContentType.objects.get(
                app_label__startswith='apis_', model=entity.lower()).model_class()

            try:
                if 'list_filters' in settings.APIS_ENTITIES[entity.title()].keys():
                    fields = [
                        x[0] for x in settings.APIS_ENTITIES[entity.title()]['list_filters']
                    ]
            except KeyError:
                exclude = ('MetaInfo',
                           'collection',
                           'references',
                           'notes',
                           'review',
                           'start_date_written',
                           'end_date_written',
                           'source',
                           'tempentityclass_ptr',
                           'id',
                           'annotation_set_relation',
                           'text')

        def __init__(self, *args, **kwargs):
            attrs = {'data-placeholder': 'Type to get suggestions',
                     'data-minimum-input-length': 3,
                     'data-html': True}
            super(GenericListFilter, self).__init__(*args, **kwargs)
            try:
                if 'list_filters' in settings.APIS_ENTITIES[entity.title()].keys():
                    for f in settings.APIS_ENTITIES[entity.title()]['list_filters']:
                        for ff in f[1].keys():
                            setattr(self.filters[f[0]], ff, f[1][ff])
            except KeyError as ex:
                print(ex)
            for f in self.filters.keys():
                if type(self.filters[f].field) == ModelMultipleChoiceField:
                    v_name_p = str(self.filters[f].queryset.model.__name__)
                    if ContentType.objects.get(app_label__in=[
                        'apis_entities', 'apis_metainfo', 'apis_relations',
                        'apis_vocabularies', 'apis_labels'
                    ], model=v_name_p.lower()).app_label.lower() == 'vocabularies':
                        self.filters[f].field.widget = autocomplete.Select2Multiple(
                            url=reverse('vocabularies:generic_vocabularies_autocomplete', kwargs={
                                'vocab': v_name_p.lower(),
                                'direct': 'normal'
                            }),
                            attrs=attrs)


    return GenericListFilter


# TODO __sresch__ : remove these classes once sure that they will not be needed
#
# class PersonListFilter(django_filters.FilterSet):
#     FILTER_CHOICES = (('', 'any'), ('male', 'male'), ('female', 'female'))
#     name = django_filters.CharFilter(method='name_label_filter', label='Name')
#     first_name = django_filters.CharFilter(lookup_expr='icontains', label='First Name')
#     gender = django_filters.ChoiceFilter(choices=FILTER_CHOICES)
#     start_date = django_filters.DateFilter(label='Date of birth') # Todo: add a datefilter that allows to filter for ranges
#     end_date = django_filters.DateFilter(label='Date of death')
#     profession__name = django_filters.CharFilter(lookup_expr='icontains', label='Profession')
#
#     class Meta:
#         model = Person
#         fields = ['name', 'first_name', 'gender', 'start_date', 'end_date', 'profession__name', 'collection']
#
#     def name_label_filter(self, queryset, name, value):
#         """
#         Filter for including the alternative names in the names search. The types of labels included in the query are
#         currently hardcoded in a list.
#
#         :param queryset: queryset that the filters are applied on
#         :param name: name of the attribute to filter on (not used as label types are hardcoded)
#         :param value: value for the filter
#         :return: filtered queryset
#         """
#         return queryset.filter(Q(name__icontains=value)|
#                                Q(label__label__icontains=value, label__label_type__name__in=alternate_names)).distinct()
#
#
# class PlaceListFilter(django_filters.FilterSet):
#     name = django_filters.CharFilter(lookup_expr='icontains', label='Name')
#     lng = django_filters.NumberFilter(label='Longitude') # Todo: add filters that allow ranges
#     lat = django_filters.NumberFilter(label='Latitude')
#     status = django_filters.CharFilter(lookup_expr='icontains')
#
#     class Meta:
#         model = Place
#         fields = ['name', 'status', 'lng', 'lat', 'collection']
#
#
# class InstitutionListFilter(django_filters.FilterSet):
#     name = django_filters.CharFilter(lookup_expr='icontains', label='Name')
#     start_date = django_filters.DateFilter(label='Date of foundation')
#     end_date = django_filters.DateFilter(label='Date of closing')
#
#     class Meta:
#         model = Institution
#         fields = ['name', 'start_date', 'end_date', 'collection']
#
#
# class EventListFilter(django_filters.FilterSet):
#     name = django_filters.CharFilter(lookup_expr='icontains', label='Name')
#     start_date = django_filters.DateFilter(label='Start date')
#     end_date = django_filters.DateFilter(label='End date')
#     kind__name = django_filters.CharFilter(lookup_expr='icontains', label='Kind')
#
#     class Meta:
#         model = Event
#         fields = ['name', 'start_date', 'end_date', 'kind__name', 'collection']
#
#
# class WorkListFilter(django_filters.FilterSet):
#     name = django_filters.CharFilter(lookup_expr='icontains', label='Name')
#     start_date = django_filters.DateFilter(label='Start date')
#     end_date = django_filters.DateFilter(label='End date')
#     kind__name = django_filters.CharFilter(lookup_expr='icontains', label='Kind')
#
#     class Meta:
#         model = Work
#         fields = ['name', 'start_date', 'end_date', 'kind__name', 'collection']
