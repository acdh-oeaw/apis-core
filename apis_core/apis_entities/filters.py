import django_filters
from dal import autocomplete
from django.forms import ModelMultipleChoiceField
from django.urls import reverse

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
                if n == 'label__label':
                    res.append(Q(**{f: value, 'label__label_type__name__in': alternate_names}))
                else:
                    res.append(Q(**{f: value}))
            return queryset.filter(res[0] | res[1] ).distinct()

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
            except KeyError:
                pass
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


class PersonListFilter(django_filters.FilterSet):
    FILTER_CHOICES = (('', 'any'), ('male', 'male'), ('female', 'female'))
    name = django_filters.CharFilter(method='name_label_filter', label='Name')
    first_name = django_filters.CharFilter(lookup_expr='icontains', label='First Name')
    gender = django_filters.ChoiceFilter(choices=FILTER_CHOICES)
    start_date = django_filters.DateFilter(label='Date of birth') # Todo: add a datefilter that allows to filter for ranges
    end_date = django_filters.DateFilter(label='Date of death')
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
    lng = django_filters.NumberFilter(label='Longitude') # Todo: add filters that allow ranges
    lat = django_filters.NumberFilter(label='Latitude')
    status = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Place
        fields = ['name', 'status', 'lng', 'lat', 'collection']


class InstitutionListFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', label='Name')
    start_date = django_filters.DateFilter(label='Date of foundation')
    end_date = django_filters.DateFilter(label='Date of closing')

    class Meta:
        model = Institution
        fields = ['name', 'start_date', 'end_date', 'collection']


class EventListFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', label='Name')
    start_date = django_filters.DateFilter(label='Start date')
    end_date = django_filters.DateFilter(label='End date')
    kind__name = django_filters.CharFilter(lookup_expr='icontains', label='Kind')

    class Meta:
        model = Event
        fields = ['name', 'start_date', 'end_date', 'kind__name', 'collection']


class WorkListFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', label='Name')
    start_date = django_filters.DateFilter(label='Start date')
    end_date = django_filters.DateFilter(label='End date')
    kind__name = django_filters.CharFilter(lookup_expr='icontains', label='Kind')

    class Meta:
        model = Work
        fields = ['name', 'start_date', 'end_date', 'kind__name', 'collection']
