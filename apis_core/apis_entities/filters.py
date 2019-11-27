import django_filters
from django.db.models import Q
from apis_core.apis_entities.models import *
from django.conf import settings
from django.db.models import QuerySet

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
        """
        Searches through the all name fields of all related entities
        """

        lookup, value = self.construct_lookup_from_wildcard(value)

        queryset_list = []

        # The following loop creates filtered querysets for each related entity field
        #   e.g. queryset.filter( person_set__name=value ) and queryset.filter( place_set__name=value )
        # Later these separate querysets are unionized and returned. This is done in contrast to filtering on the
        # queryset only once with multiple Q objects which themselves are disjunctively joined
        #   e.g. queryset.filter( Q(person_set__name=value) | Q(place_set__name=value) )
        # since it turned out that doing it with Q objects decreases performance dramatically.
        for related_entity_field_name in queryset.model.get_related_entity_field_names():
            queryset_list.append(
                queryset.filter(
                    **{related_entity_field_name + "__name" + lookup: value} ) )

        # unionize the separate querysets and order them (distinct is not necessary since it is included in union method)
        return QuerySet.union(*queryset_list).order_by("name")



    def related_relationtype_name_filter(self, queryset, name, value):
        """
        Searches through the all name fields of all related relation types
        """

        lookup, value = self.construct_lookup_from_wildcard(value)

        queryset_list = []

        # The following loop creates filtered querysets for each related entity field
        #   e.g. queryset.filter( person_relationtype_set__name=value ) and queryset.filter( place_relationtype_set__name=value )
        # Later these separate querysets are unionized and returned. This is done in contrast to filtering on the
        # queryset only once with multiple Q objects which themselves are disjunctively joined
        #   e.g. queryset.filter( Q(person_relationtype_set__name=value) | Q(place_relationtype_set__name=value) )
        # since it turned out that doing it with Q objects decreases performance dramatically.
        for relationtype_field_name in queryset.model.get_related_relationtype_field_names():
            queryset_list.append(
                queryset.filter(
                    **{relationtype_field_name + "__name" + lookup: value} ) )

        # unionize the separate querysets and order them (distinct is not necessary since it is included in union method)
        return QuerySet.union(*queryset_list).order_by("name")



    def related_arbitrary_model_name(self, queryset, name, value):
        """
        Searches through an arbitrarily related model on its name field.

        Note that this works only if
            * the related model has a field 'name'
            * the filter using this method has the same name as the field of the model on which the filter is applied.
                (E.g. the field 'profession' on a person relates to another model: the professiontype. Here the filter on a person
                must also be called 'profession' as the field 'profession' exists within the person model and is then used to search in.
                Using this example of professions, such a lookup would be generated: Person.objects.filter(profession__name__... ) )
        """

        lookup_detail, value = self.construct_lookup_from_wildcard(value)

        # name variable is the name of the filter and needs the corresponding field within the model
        return queryset.filter( **{ name + "__name" + lookup_detail : value } )






#######################################################################
#
#   Overriding Entity filter classes
#
#######################################################################


class PersonListFilter(GenericListFilter):

    gender = django_filters.ChoiceFilter(choices=(('', 'any'), ('male', 'male'), ('female', 'female')))
    profession = django_filters.CharFilter(method="related_arbitrary_model_name")
    title = django_filters.CharFilter(method="related_arbitrary_model_name")
    name = django_filters.CharFilter(method="person_name_filter", label="Name or Label of person")


    # TODO __sresch__ : look into how the meta class can be inherited from the superclass so that the Meta class' exclude attribute must not be defined multiple times
    class Meta:
        model = Person
        # exclude all hardcoded fields or nothing, however this exclude is only defined here as a temporary measure in
        # order to load all filters of all model fields by default so that they are available in the first place.
        # Later those which are not referenced in the settings file will be removed again
        exclude = getattr(settings, 'APIS_RELATIONS_FILTER_EXCLUDE', [])


    def person_name_filter(self, queryset, name, value):

        lookup, value = self.construct_lookup_from_wildcard(value)

        queryset_related_label=queryset.filter(**{"label__label"+lookup : value})
        queryset_self_name=queryset.filter(**{name+lookup : value})
        queryset_first_name=queryset.filter(**{"first_name"+lookup : value})

        return QuerySet.union(queryset_related_label, queryset_self_name, queryset_first_name)




class PlaceListFilter(GenericListFilter):

    # TODO __sresch__ : decide on margin tolerance of input, for now the number must be precise
    lng = django_filters.NumberFilter(label='Longitude')
    lat = django_filters.NumberFilter(label='Latitude')

    class Meta:
        model = Place
        # exclude all hardcoded fields or nothing, however this exclude is only defined here as a temporary measure in
        # order to load all filters of all model fields by default so that they are available in the first place.
        # Later those which are not referenced in the settings file will be removed again
        exclude = getattr(settings, 'APIS_RELATIONS_FILTER_EXCLUDE', [])



class InstitutionListFilter(GenericListFilter):

    class Meta:
        model = Institution
        # exclude all hardcoded fields or nothing, however this exclude is only defined here as a temporary measure in
        # order to load all filters of all model fields by default so that they are available in the first place.
        # Later those which are not referenced in the settings file will be removed again
        exclude = getattr(settings, 'APIS_RELATIONS_FILTER_EXCLUDE', [])



class EventListFilter(GenericListFilter):

    class Meta:
        model = Event
        # exclude all hardcoded fields or nothing, however this exclude is only defined here as a temporary measure in
        # order to load all filters of all model fields by default so that they are available in the first place.
        # Later those which are not referenced in the settings file will be removed again
        exclude = getattr(settings, 'APIS_RELATIONS_FILTER_EXCLUDE', [])



class WorkListFilter(GenericListFilter):

    kind = django_filters.ModelChoiceFilter(queryset=WorkType.objects.all())

    class Meta:
        model = Work
        # exclude all hardcoded fields or nothing, however this exclude is only defined here as a temporary measure in
        # order to load all filters of all model fields by default so that they are available in the first place.
        # Later those which are not referenced in the settings file will be removed again
        exclude = getattr(settings, 'APIS_RELATIONS_FILTER_EXCLUDE', [])


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