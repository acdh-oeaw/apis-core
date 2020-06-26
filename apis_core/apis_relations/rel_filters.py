import django_filters
from dal import autocomplete
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.urls import reverse

from .models import AbstractRelation


# TODO __sresch__ : Change this whole module according to the same logic as in apis_core/apis_entities/filters.py

def get_excluded_fields(model):
    modelname = model.__name__
    base_list = getattr(settings, "APIS_RELATIONS_FILTER_EXCLUDE", [])
    rel_model_conf = getattr(settings, "APIS_RELATIONS", {})
    try:
        additional_excludes = rel_model_conf[modelname]
    except KeyError:
        return set(base_list)
    if additional_excludes:
        try:
            exclude = base_list + additional_excludes['exclude']
            return set(exclude)
        except KeyError:
            return set(base_list)
    else:
        return set(base_list)


FIELD_TO_FILTER = {
    "ForeignKey": "MultipleChoiceFilter",
    "ManyToManyField": "MultipleChoiceFilter",
    "TextField": "CharFilter",
    "CharField": "CharFilter",
    "DateField": "DateFromToRangeFilter",
    "BooleanField": "BooleanFilter"
}


def get_field_dicts(model, include_parents=False):
    fields = [
        {
            "f_name": x.name,
            "f_v_name": getattr(x, 'verbose_name', None),
            "f_help_text": getattr(x, 'helptext', None),
            "f_class_name": "{}".format(x.__class__.__name__),
            "f_model": getattr(x, 'related_model', None)
        } for x in model._meta.get_fields(include_parents=include_parents)
    ]
    return fields


def get_filters(model, exclude=[], include_parents=False):
    filters = []
    field_dicts = get_field_dicts(model, include_parents=include_parents)
    for x in field_dicts:
        filters.append(x['f_name'])
        if x['f_model']:
            rel_fields = get_field_dicts(x['f_model'], include_parents)
            for y in rel_fields:
                if 'apis_relations' in "{}".format(y['f_model']):
                    pass
                else:
                    rel_field_name = "{}__{}".format(x['f_name'], y['f_name'])
                    filters.append(rel_field_name)
    if exclude:
        out = []
        for x in exclude:
            filters = [f for f in filters if x not in f]
    return filters


def get_generic_relation_filter(entity):
    class GenericListFilter(django_filters.FilterSet):
        def name_label_filter(self, queryset, name, value):
            """
            Filter for including the alternative names in the names search.\
            The types of labels included in the query are
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
            return queryset.filter(res[0] | res[1]).distinct()

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
            model = AbstractRelation.get_relation_class_of_name(entity)
            fields = get_filters(
                model,
                exclude=get_excluded_fields(model),
                include_parents=True
            )

        def __init__(self, *args, **kwargs):
            attrs = {'data-placeholder': 'Type to get suggestions',
                     'data-minimum-input-length': getattr(settings, "APIS_MIN_CHAR", 3),
                     'data-html': True}
            super(GenericListFilter, self).__init__(*args, **kwargs)
            for x in self.filters.keys():
                if type(self.filters[x].field).__name__ == "ModelChoiceField":
                    current_model_name = str(self.filters[x].queryset.model.__name__).lower()
                    current_qs = self.filters[x].queryset
                    if ContentType.objects.get(app_label__in=[
                        'apis_entities', 'apis_metainfo', 'apis_relations',
                        'apis_vocabularies', 'apis_labels'
                    ], model=current_model_name).app_label.lower() == 'apis_entities':
                        self.filters[x] = django_filters.ModelMultipleChoiceFilter(
                            field_name=x,
                            queryset=current_qs,
                            widget=autocomplete.ModelSelect2Multiple(
                                url=reverse(
                                    'apis:apis_entities:generic_network_entities_autocomplete',
                                    kwargs={
                                        'entity': current_model_name
                                    }
                                ),
                            )
                        )
                if type(self.filters[x].field).__name__ == "DateField":
                    self.filters[x] = django_filters.DateFromToRangeFilter(
                        field_name=x,
                    )
                if type(self.filters[x].field).__name__ == "CharField":
                    self.filters[x] = django_filters.CharFilter(
                        lookup_expr='icontains',
                        field_name=x,
                    )
                if type(self.filters[x].field).__name__ == "ModelMultipleChoiceField":
                    current_model_name = str(self.filters[x].queryset.model.__name__).lower()
                    current_qs = self.filters[x].queryset
                    self.filters[x] = django_filters.ModelMultipleChoiceFilter(
                        field_name=x,
                        queryset=current_qs,
                        widget=autocomplete.ModelSelect2Multiple(
                            url=reverse(
                                'apis:apis_entities:generic_network_entities_autocomplete',
                                kwargs={
                                    'entity': current_model_name
                                }
                            ),
                        )
                    )
    return GenericListFilter
