import django_filters
from django.db.models import Q
from apis_core.apis_entities.models import *
from django.conf import settings

# The following classes define the filter sets respective to their models.
# Also by what was enabled in the global settings file (or disabled by not explicitley enabling it).
# Hence by default all filters of all model's fields (automatically generated) and all filters manually defined below
# are at first created and then deleted by what was enabled in the settings file
#
# There is a few overrides happening here, which are in order:
# 1.) The filters defined in GenericListFilter
# 2.) The filters automatically defined in model specific ListFilters (by stating exclude = [] in the Meta class)
# 3.) The filters manually defined in model specific ListFilters (by manual field definitions in the Filter class itself)
# If anything is redefined in a step further it overrides the field from the step before
#
# Additionally, in the global settings file:
# The filters defined there can provide a dictionary which can have a "method" or "label" key-value pair
# where then such a key-value from the settings is overriding the respective key-value of a filter defined in this module
# (e.g. using a different method)

# TODO __sresch__ : Turn the logic of returing a filter object into a singleton pattern to avoid redundant instantiations
# TODO __sresch__ : use the order of list of filter fields in settings
# TODO __sresch__ : make the various filters conjunctive with each other instead of disjunctive as they are now


#######################################################################
#
#   Generic super class for sharing filters accross all entities
#
#######################################################################

class GenericListFilter(django_filters.FilterSet):

    name = django_filters.CharFilter(method="name_label_filter", label="Name or Label")
    collection = django_filters.ModelMultipleChoiceFilter(queryset=Collection.objects.all())

    # TODO __sresch__ : look into how the date values can be intercepted so that they can be parsed with the same logic as in edit forms
    start_date = django_filters.DateFromToRangeFilter()
    end_date = django_filters.DateFromToRangeFilter()

    # TODO __sresch__ : look into how to change these into auto-complete fields
    related_entity_name = django_filters.CharFilter(method="related_entity_name_filter", label="related entity")
    related_relationtype_name = django_filters.CharFilter(method="related_relationtype_name_filter", label="relationtype")


    def __init__(self, *args, **kwargs):

        # call super init foremost to create dictionary of filters which will be processed further below
        super().__init__(*args, **kwargs)

        def eliminate_unused_filters(default_filter_dict):
            """
            Method to read in from the settings file which filters should be enabled / disabled and if there are
            methods or labels to override the default ones.

            :param default_filter_dict: the default filter dictionary created on filter class instantiation
                (which comprises filters defined: in GenericListFilter, in specific model ListFilter and their defaults)

            :return: a new dictionary which is a subset of the input dictionary and only contains the filters which
                are referenced in the settings file (and if there were methods or labels also referenced, using them)
            """

            enabled_filters = settings.APIS_ENTITIES[self.Meta.model.__name__]["list_filters"]

            filter_dict_tmp = {}

            for enabled_filter in enabled_filters:

                if type(enabled_filter) == str and enabled_filter in default_filter_dict:
                    # If string then just use it, if a filter with such a name is already defined

                    filter_dict_tmp[enabled_filter] = default_filter_dict[enabled_filter]


                elif type(enabled_filter) == dict:
                    # if a dictionary, then look further into if there is a method or label which overrides the defaults

                    enabled_filter_key = list(enabled_filter.keys())[0]

                    if enabled_filter_key in default_filter_dict:

                        # get the dictionary which contains potential method or label overrides
                        enabled_filter_settings_dict = enabled_filter[enabled_filter_key]

                        if "method" in enabled_filter_settings_dict:
                            default_filter_dict[enabled_filter_key].method = enabled_filter_settings_dict["method"]

                        if "label" in enabled_filter_settings_dict:
                            default_filter_dict[enabled_filter_key].label = enabled_filter_settings_dict["label"]

                        filter_dict_tmp[enabled_filter_key] = default_filter_dict[enabled_filter_key]

                    else:
                        raise ValueError("Expected either str or dict as type for an individual filter in the settings file.",
                                "\nGot instead:", type(enabled_filter))

            return filter_dict_tmp

        self.filters = eliminate_unused_filters(self.filters)



    def construct_lookup_from_wildcard(self, value):
        """
        Parses user input for wildcards and returns a tuple containing the interpreted django lookup string and the trimmed value
        E.g.
            "*example" -> ("__iendswith", "example")
            "example*" -> ("__istartswith", "example")
            "*example*" -> ("__icontains", "example")
            ""example"" -> ("__exact", "example")

        :param value : str : text to be parsed for *
        :return: (lookup : str, value : str)
        """

        search_startswith = False
        search_endswith = False

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
            return "__exact", value


    def string_wildcard_filter(self, queryset, name, value):
        lookup, value = self.construct_lookup_from_wildcard(value)
        return queryset.filter(**{name + lookup : value})



    def name_label_filter(self, queryset, name, value):
        # TODO __sresch__ : include alternative names queries

        lookup, value = self.construct_lookup_from_wildcard(value)

        queryset_related_label=queryset.filter(**{"label__label"+lookup : value})
        queryset_self_name=queryset.filter(**{name+lookup : value})

        return queryset_related_label.union(queryset_self_name).distinct().order_by("name")



    def related_entity_name_filter(self, queryset, name, value):

        lookup, value = self.construct_lookup_from_wildcard(value)

        q_args = Q()

        for entity_field_name in queryset.model.get_related_entity_field_names():

            q_args = q_args | Q(**{entity_field_name + "__name"+lookup : value})

        return queryset.filter(q_args).distinct().order_by("name")



    def related_relationtype_name_filter(self, queryset, name, value):

        lookup_detail, value = self.construct_lookup_from_wildcard(value)

        q_args = Q()

        for relationtype_field_name in queryset.model.get_related_relationtype_field_names():

            base_lookup = relationtype_field_name + "__name" + lookup_detail
            q_args = q_args | Q(**{base_lookup : value})

        return queryset.filter(q_args).distinct().order_by("name")




#######################################################################
#
#   Overriding Entity filter classes
#
#######################################################################


class PersonListFilter(GenericListFilter):

    gender = django_filters.ChoiceFilter(choices=(('', 'any'), ('male', 'male'), ('female', 'female')))
    profession = django_filters.CharFilter(method="string_wildcard_filter")
    title = django_filters.CharFilter(method="string_wildcard_filter")
    name = django_filters.CharFilter(method="person_name_filter", label="Name or Label of person")

    class Meta:
        model = Person
        # exclude nothings means to load all fields of given model and use them as filters respective to their type
        exclude = []


    def person_name_filter(self, queryset, name, value):

        queryset_standard_name=self.name_label_filter(queryset, name, value)

        # TODO __sresch__ : Look into why the commented code below does not work. Union of the two querysets throws an exception for some reason.
        # lookup, value = self.construct_lookup_from_wildcard(value)
        #
        # queryset_first_name=queryset.filter(**{"first_name"+lookup : value})
        #
        # result_qs = queryset_standard_name.union(queryset_first_name)
        # return result_qs
        #
        # until the above is fixed, return this queryset
        return queryset_standard_name




class PlaceListFilter(GenericListFilter):

    # TODO __sresch__ : decide on margin tolerance of input, for now the number must be precise
    lng = django_filters.NumberFilter(label='Longitude')
    lat = django_filters.NumberFilter(label='Latitude')

    class Meta:
        model = Place
        # exclude nothings means to load all fields of given model and use them as filters respective to their type
        exclude = []



class InstitutionListFilter(GenericListFilter):

    class Meta:
        model = Institution
        # exclude nothings means to load all fields of given model and use them as filters respective to their type
        exclude = []



class EventListFilter(GenericListFilter):

    class Meta:
        model = Event
        # exclude nothings means to load all fields of given model and use them as filters respective to their type
        exclude = []



class WorkListFilter(GenericListFilter):

    kind = django_filters.ModelChoiceFilter(queryset=WorkType.objects.all())

    class Meta:
        model = Work
        # exclude nothings means to load all fields of given model and use them as filters respective to their type
        exclude = []


def get_list_filter_of_entity(entity):
    """
    Main method to be called somewhere else in the codebase in order to get the FilterClass respective to the entity string input

    :param entity: str: type of entity
    :return: Entity specific FilterClass
    """

    el = entity.lower()

    if el == "person":
        return PersonListFilter

    elif el == "place":
        return PlaceListFilter

    elif el == "institution":
        return InstitutionListFilter

    elif el == "event":
        return EventListFilter

    elif el == "work":
        return WorkListFilter

    else:
        raise ValueError("Could not find respective filter for given entity type:", el)