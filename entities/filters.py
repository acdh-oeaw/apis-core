import django_filters
from .models import Person, Place, Institution, Event, Work
from django.db.models import Q
from django.conf import settings
from django.contrib.contenttypes.models import ContentType


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
    class GenericListFilter(django_filters.FilterSet):
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
            res = []
            orig_value = value
            for n in ['name', 'label__label']:
                value = orig_value
                f = '{}__'.format(n)
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                else:
                    f += 'i'
                if value.startswith('*') and value.endswith('*'):
                    f += 'contains'
                    value = value[1:-1]
                elif value.startswith('*'):
                    f += 'endswith'
                    value = value[1:]
                elif value.endswith('*'):
                    f += 'startswith'
                    value = value[:-1]
                else:
                    f += 'exact'
                res.append(Q(**{f: value}))
            return queryset.filter(res[0] | res[1], label__label_type__name__in=alternate_names).distinct()

        def wildcard_filter(self, queryset, name, value):
            f = '{}__'.format(name)
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            else:
                f += 'i'
            if value.startswith('*') and value.endswith('*'):
                f += 'contains'
                value = value[1:-1]
            elif value.startswith('*'):
                f += 'endswith'
                value = value[1:]
            elif value.endswith('*'):
                f += 'startswith'
                value = value[:-1]
            else:
                f += 'exact'
            return queryset.filter(**{f: value})

        class Meta:
            model = ContentType.objects.get(app_label='entities', model=entity.lower()).model_class()
            if 'list_filters' in settings.APIS_ENTITIES[entity.title()].keys():
                fields = [x[0] for x in settings.APIS_ENTITIES[entity.title()]['list_filters']]
            else:
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
            super(GenericListFilter, self).__init__(*args, **kwargs)
            if 'list_filters' in settings.APIS_ENTITIES[entity.title()].keys():
                for f in settings.APIS_ENTITIES[entity.title()]['list_filters']:
                    print(self.filters[f[0]].widget.__class__)
                    #self.filters[f[0]].widget.__class__ = 'form-control'
                    for ff in f[1].keys():
                        setattr(self.filters[f[0]], ff, f[1][ff])

    return GenericListFilter


class PersonListFilter(django_filters.FilterSet):
    FILTER_CHOICES = (('', 'any'), ('male', 'male'), ('female', 'female'))
    name = django_filters.CharFilter(method='name_label_filter', label='Name')
    first_name = django_filters.CharFilter(lookup_expr='icontains', label='First Name')
    gender = django_filters.ChoiceFilter(choices=FILTER_CHOICES)
    start_date = django_filters.DateFilter(lookup_expr=['lt', 'gt', 'exact'], label='Date of birth')
    end_date = django_filters.DateFilter(lookup_expr=['lt', 'gt', 'exact'], label='Date of death')
    profession__name = django_filters.CharFilter(lookup_expr='icontains', label='Profession')

    class Meta:
        model = Person
        fields = ['name', 'first_name', 'gender', 'start_date', 'end_date', 'profession__name', 'collection']

    def name_label_filter(self, queryset, name, value):
        """
        Filter for including the alternative names in the names search. The types of labels included in the query are
        currently hardcoded in a list.
        
        :param queryset: queryset that the filters are applied on
        :param name: name of the attribute to filter on (not used as label types are hardcoded)
        :param value: value for the filter
        :return: filtered queryset
        """
        return queryset.filter(Q(name__icontains=value)|
                               Q(label__label__icontains=value, label__label_type__name__in=alternate_names)).distinct()


class PlaceListFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', label='Name')
    lng = django_filters.NumberFilter(lookup_expr=['lt', 'gt'], label='Longitude')
    lat = django_filters.NumberFilter(lookup_expr=['lt', 'gt'], label='Latitude')
    status = django_filters.CharFilter(lookup_expr=['icontains','exact', 'iexact'])

    class Meta:
        model = Place
        fields = ['name', 'status', 'lng', 'lat', 'collection']


class InstitutionListFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', label='Name')
    start_date = django_filters.DateFilter(
            lookup_expr=['lt', 'gt', 'exact'], label='Date of foundation')
    end_date = django_filters.DateFilter(lookup_expr=['lt', 'gt', 'exact'], label='Date of closing')

    class Meta:
        model = Institution
        fields = ['name', 'start_date', 'end_date', 'collection']


class EventListFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', label='Name')
    start_date = django_filters.DateFilter(
            lookup_expr=['lt', 'gt', 'exact'], label='Start date')
    end_date = django_filters.DateFilter(lookup_expr=['lt', 'gt', 'exact'], label='End date')
    kind__name = django_filters.CharFilter(lookup_expr='icontains', label='Kind')

    class Meta:
        model = Event
        fields = ['name', 'start_date', 'end_date', 'kind__name', 'collection']


class WorkListFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', label='Name')
    start_date = django_filters.DateFilter(
            lookup_expr=['lt', 'gt', 'exact'], label='Start date')
    end_date = django_filters.DateFilter(lookup_expr=['lt', 'gt', 'exact'], label='End date')
    kind__name = django_filters.CharFilter(lookup_expr='icontains', label='Kind')

    class Meta:
        model = Work
        fields = ['name', 'start_date', 'end_date', 'kind__name', 'collection']
