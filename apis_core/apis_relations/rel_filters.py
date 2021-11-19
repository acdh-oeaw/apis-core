import django_filters
from dal import autocomplete
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.urls import reverse
import operator
from functools import reduce

from .models import AbstractRelation


# TODO __sresch__ : Change this whole module according to the same logic as in apis_core/apis_entities/filters.py

def get_excluded_fields(model):
    modelname = model.__name__
    base_list = getattr(settings, "APIS_RELATIONS_FILTER_EXCLUDE", [])
    rel_model_conf = getattr(settings, "APIS_RELATIONS", {})
    if "exclude" in rel_model_conf.keys():
        if isinstance(rel_model_conf["exclude"], list):
            base_list.extend(rel_model_conf["exclude"])
    if modelname in rel_model_conf.keys():
        if "exclude" in rel_model_conf[modelname].keys():
            if isinstance(rel_model_conf[modelname]["exclude"], list):
                base_list.extend(rel_model_conf[modelname]["exclude"])
    return set(base_list)


def get_included_fields(model):
    modelname = model.__name__
    rel_model_conf = getattr(settings, "APIS_RELATIONS", {})
    if modelname in rel_model_conf.keys():
        return rel_model_conf[modelname].get("include", False)
    else:
        return False



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


def get_filters(model, exclude=False, include=False, include_parents=False):
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
    if include:
        filters = [x for x in filters if x in include]
    elif exclude:
        for x in exclude:
            if x.startswith("*") and not x.endswith("*"):
                filters = [f for f in filters if not f.lower().endswith(x[1:].lower())]
            elif x.startswith("*") and x.endswith("*"):
                filters = [f for f in filters if not x[1:-1].lower() in f]
            elif not x.startswith("*") and x.endswith("*"):
                filters = [f for f in filters if not f.lower().startswith(x[:-1].lower())]
            else:
                filters = [f for f in filters if not x.lower() == f.lower()]
    return filters


def get_generic_relation_filter(entity):
    class GenericListFilter(django_filters.FilterSet):
        #search = django_filters.CharFilter(method='search_filter_method')

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

        def search_filter_method(self, queryset, name, value):
            cls = queryset.model.__name__
            sett_filters = getattr(settings, "APIS_RELATIONS", {})
            if cls.lower() in sett_filters.keys():
                filter_attr = sett_filters[cls.lower()].get("search", ["name"])
                query = reduce(operator.or_, [ Q(**{attr: value}) for attr in filter_attr ] )


        class Meta:
            model = AbstractRelation.get_relation_class_of_name(entity)
            fields = get_filters(
                model,
                exclude=get_excluded_fields(model),
                include=get_included_fields(model),
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
                    if ContentType.objects.filter(app_label='apis_entities', model=current_model_name).count() > 0:
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
                    elif ContentType.objects.filter(app_label='apis_vocabularies', model=current_model_name).count() > 0:
                        self.filters[x] = django_filters.ModelMultipleChoiceFilter(
                            field_name=x,
                            queryset=current_qs,
                            widget=autocomplete.ModelSelect2Multiple(
                                url=reverse(
                                    'apis:apis_vocabularies:generic_vocabularies_autocomplete',
                                    kwargs={
                                        'vocab': current_model_name,
                                        'direct': 'normal'
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
