import django_filters
from apis_core.apis_vocabularies.models import WorkWorkRelation
from django.db.models import Q

from apis_core.apis_entities.models import *
from apis_core.apis_labels.models import Label


# TODO __sresch__ : Turn this class and its filter classes into singleton patterns to ensure no redundant instantiations
class EntityFilterHandler():

    _entity_filter_dict = {}

    @classmethod
    def get_filter(cls, entity):
        return cls._entity_filter_dict[entity]


    # TODO __sresch__ : make the various filters conjunctive with each other instead of disjunctive as they are now
    class GenericListFilter(django_filters.FilterSet):


        def construct_lookup_from_wildcard(self, value):

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


        def string_exact_filter(self, queryset, name, value):
            return queryset.filter(name__exact=value)


        def string_icontains_filter(self, queryset, name, value):
            return queryset.filter(name__icontains=value)


        def string_wildcard_filter(self, queryset, name, value):
            lookup, value = self.construct_lookup_from_wildcard(value)
            return queryset.filter(**{name + lookup : value})



        def name_filter(self, queryset, name, value):

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


        name = django_filters.CharFilter(method="name_filter")
        start_date = django_filters.DateFromToRangeFilter()
        end_date = django_filters.DateFromToRangeFilter()
        related_entity_name = django_filters.CharFilter(method="related_entity_name_filter", label="related_entity_name")
        related_relationtype_name = django_filters.CharFilter(method="related_relationtype_name_filter", label="related_relationtype_name")
        collection = django_filters.ModelMultipleChoiceFilter(queryset=Collection.objects.all())

        # TODO __sresch__ : find a way to get a dropdown of available RelationTypes. This underneath does not work
        # related_relationtype_name = django_filters.ModelChoiceFilter(
        #     label="related_relationtype_name",
        #     queryset=WorkWorkRelation.objects.all()
        # )




    class PersonListFilter(GenericListFilter):

        gender = django_filters.ChoiceFilter(choices=(('', 'any'), ('male', 'male'), ('female', 'female')))
        profession__name = django_filters.CharFilter(method="string_wildcard_filter")
        name = django_filters.CharFilter(method="person_name_filter")

        class Meta:
            model = Person
            fields = []



        def person_name_filter(self, queryset, name, value):

            queryset_standard_name=self.name_filter(queryset, name, value)
            lookup, value = self.construct_lookup_from_wildcard(value)
            queryset_first_name=queryset.filter(**{"first_name"+lookup : value})

            # TODO __sresch__ : to fix, union of the two querysets throw exception
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
            fields = []



    class InstitutionListFilter(GenericListFilter):

        class Meta:
            model = Institution
            fields = []




    class EventListFilter(GenericListFilter):

        class Meta:
            model = Event
            fields = []




    class WorkListFilter(GenericListFilter):

        kind = django_filters.ModelChoiceFilter(queryset=WorkType.objects.all())

        class Meta:
            model = Work
            fields = []




    _entity_filter_dict["person"] = PersonListFilter
    _entity_filter_dict["place"] = PlaceListFilter
    _entity_filter_dict["institution"] = InstitutionListFilter
    _entity_filter_dict["event"] = EventListFilter
    _entity_filter_dict["work"] = WorkListFilter






def get_list_filter_of_entity(entity):

    return EntityFilterHandler.get_filter(entity.lower())