import django_filters
from django.db.models import Q
from apis_core.apis_entities.models import *
from django.conf import settings

# TODO __sresch__ : Turn the logic of returing a filter object into a singleton pattern
# TODO __sresch__ : use the order of list of filter fields in settings


# TODO __sresch__ : make the various filters conjunctive with each other instead of disjunctive as they are now
class GenericListFilter(django_filters.FilterSet):

    name = django_filters.CharFilter(method="name_label_filter", label="Name or Label")

    # TODO __sresch__ : look into how the date values can be intercepted so that they can be parsed with the same logic as in edit forms
    start_date = django_filters.DateFromToRangeFilter()
    end_date = django_filters.DateFromToRangeFilter()

    collection = django_filters.ModelMultipleChoiceFilter(queryset=Collection.objects.all())

    # TODO __sresch__ : look into how to change these into auto-complete fields
    related_entity_name = django_filters.CharFilter(method="related_entity_name_filter", label="related entity")
    related_relationtype_name = django_filters.CharFilter(method="related_relationtype_name_filter", label="relationtype")

    # TODO __sresch__ : find a way to get a dropdown of available RelationTypes. This underneath does not work
    # related_relationtype_name = django_filters.ModelChoiceFilter(
    #     label="related_relationtype_name",
    #     queryset=WorkWorkRelation.objects.all()
    # )


    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        enabled_filters = settings.APIS_ENTITIES[self.Meta.model.__name__]["list_filters"]

        filters_dict_tmp = {}

        for filter_name, filter_object in self.filters.items():

            if filter_name in enabled_filters:

                filter_settings = enabled_filters[filter_name]

                if "method" in filter_settings:
                    filter_object.method = filter_settings["method"]

                if "label" in filter_settings:
                    filter_object.label = filter_settings["label"]

                filters_dict_tmp[filter_name] = filter_object

        self.filters = filters_dict_tmp



    def construct_lookup_from_wildcard(self, value):
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





class PersonListFilter(GenericListFilter):

    gender = django_filters.ChoiceFilter(choices=(('', 'any'), ('male', 'male'), ('female', 'female')))
    profession = django_filters.CharFilter(method="string_wildcard_filter")
    title = django_filters.CharFilter(method="string_wildcard_filter")
    name = django_filters.CharFilter(method="person_name_filter", label="Name or Label of person")

    class Meta:
        model = Person
        exclude = []


    def person_name_filter(self, queryset, name, value):

        queryset_standard_name=self.name_label_filter(queryset, name, value)

        # TODO __sresch__ : does not work, union of the two querysets throws exception
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

    # TODO __sresch__ : decide on margin tolerance of input, now the number must be precise
    lng = django_filters.NumberFilter(label='Longitude')
    lat = django_filters.NumberFilter(label='Latitude')

    class Meta:
        model = Place
        exclude = []



class InstitutionListFilter(GenericListFilter):

    class Meta:
        model = Institution
        exclude = []



class EventListFilter(GenericListFilter):

    class Meta:
        model = Event
        exclude = []



class WorkListFilter(GenericListFilter):

    kind = django_filters.ModelChoiceFilter(queryset=WorkType.objects.all())

    class Meta:
        model = Work
        exclude = []


def get_list_filter_of_entity(entity):

    entity_filter_dict = {
        "person": PersonListFilter,
        "place": PlaceListFilter,
        "institution": InstitutionListFilter,
        "event": EventListFilter,
        "work": WorkListFilter,
    }

    return entity_filter_dict[entity.lower()]