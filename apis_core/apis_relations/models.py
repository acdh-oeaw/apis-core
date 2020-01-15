from django.contrib.contenttypes.models import ContentType
from django.db import models
#from reversion import revisions as reversion
import reversion
from django.db.models import Q
import operator
import pdb
import inspect
import sys

from apis_core.apis_entities.models import Person, Place, Institution, Event, Work
from apis_core.apis_metainfo.models import TempEntityClass
from apis_core.apis_vocabularies.models import (PersonPlaceRelation, PersonPersonRelation,
    PersonInstitutionRelation, PersonEventRelation, PersonWorkRelation,
    InstitutionInstitutionRelation, InstitutionPlaceRelation,
    InstitutionEventRelation, PlacePlaceRelation, PlaceEventRelation,
    PlaceWorkRelation, EventEventRelation, EventWorkRelation,
    WorkWorkRelation, InstitutionWorkRelation)


#######################################################################
#
# Custom Managers
#
#######################################################################


class AnnotationRelationLinkManager(models.Manager):
    """Manager used to retrieve only those relations that are highlighted in the texts.
    Reads out the ``annotation_project`` and ``users_show_highlighter`` session variables and provides a filter.
    Needs a :class:`django.request` object in order to read out the ``session`` variable.

    *Example:*
    ::

        relation = PersonPlace.objects.filter(related_place='Wien').filter_ann_project(request=request)

    Returns only those relations that are connected with an annotation that fits the session variables or are not
    connected to any annotation at all.
    """
    def filter_ann_proj(self, request=None, ann_proj=1, include_all=True):
        """The filter function provided by the manager class.

        :param request: `django.request` object
        :return: queryset that contains only objects that are shown in the highlighted text or those not connected
            to an annotation at all.
        """
        users_show = None
        if request:
            ann_proj = request.session.get('annotation_project', 1)
            if not ann_proj:
                ann_proj = 1
            users_show = request.session.get('users_show_highlighter', None)
        query = Q(annotation__annotation_project_id=ann_proj)
        qs = super(AnnotationRelationLinkManager, self).get_queryset()
        if users_show is not None:
            query.add(Q(annotation__user_added_id__in=users_show), Q.AND)
        if include_all:
            query.add(Q(annotation__annotation_project__isnull=True), Q.OR)
        return qs.filter(query)


#######################################################################
#
# AbstractRelation
#
#######################################################################


class AbstractRelation(TempEntityClass):
    """
    Abstract super class which encapsulates common logic between the different relations and provides various methods
    relating to either all or specific relations.
    """

    annotation_links = AnnotationRelationLinkManager()

    class Meta:
        abstract = True



    # Methods dealing with individual data retrievals of instances
    ####################################################################################################################

    def __str__(self):
        return "{} ({}) {}".format(self.get_related_entity_instanceA(), self.relation_type, self.get_related_entity_instanceB())


    def get_web_object(self):

        nameA = self.get_related_entity_instanceA().name
        nameB = self.get_related_entity_instanceB().name

        if self.get_related_entity_classA() == Person:
            nameA += ", "
            if self.get_related_entity_instanceA().first_name is None:
                nameA += "-"
            else:
                nameA += self.get_related_entity_instanceA().first_name

        if self.get_related_entity_classB() == Person:
            nameB += ", "
            if self.get_related_entity_instanceB().first_name is None:
                nameB += "-"
            else:
                nameB += self.get_related_entity_instanceB().first_name

        result = {
            'relation_pk': self.pk,
            'relation_type': self.relation_type.name,
            self.get_related_entity_field_nameA(): nameA,
            self.get_related_entity_field_nameB(): nameB,
            'start_date': self.start_date_written,
            'end_date': self.end_date_written}
        return result


    def get_table_dict(self, entity):
        """Dict for the tabels in the html view

        :param entity: Object of type :class:`entities.models.Place`; Used to determine which Place is the main antity
            and which one the related.
        :return:
        """
        if self.get_related_entity_instanceA() == entity:
            rel_other_key = self.get_related_entity_field_nameB()[:-1]
            rel_other_value = self.get_related_entity_instanceB()
            rel_type = self.relation_type.label
        elif self.get_related_entity_instanceB() == entity:
            rel_other_key = self.get_related_entity_field_nameA()[:-1]
            rel_other_value = self.get_related_entity_instanceA()
            rel_type = self.relation_type.label_reverse
        else:
            raise Exception("Did not find corresponding entity. Wiring of current relation to current entity is faulty.")

        result = {
            'relation_pk': self.pk,
            'relation_type': rel_type,
            rel_other_key: rel_other_value,
            'start_date_written': self.start_date_written,
            'end_date_written': self.end_date_written,
            'start_date': self.start_date,
            'end_date': self.end_date}
        return result



    # Various Methods enabling convenient shortcuts between entities, relations, fields, etc
    ####################################################################################################################


    # Methods dealing with all relations
    ####################################################################################################################


    _all_relation_classes = None
    _all_relation_names = None


    @classmethod
    def get_all_relation_classes(cls):
        """
        Instantiates both lists: '_all_relation_classes' and '_all_relation_names'

        :return: list of all python classes of the relations defined within this models' module
        """

        # check if not yet instantiated
        if cls._all_relation_classes == None:
            # if not, then instantiate the private lists

            relation_classes = []
            relation_names = []

            # using python's reflective logic, the following loop iterates over all classes of this current module.
            for relation_name, relation_class in inspect.getmembers(
                    sys.modules[__name__], inspect.isclass):

                # check for python classes not to be used.
                if \
                        relation_class.__module__ == "apis_core.apis_relations.models" and \
                        relation_class.__name__ != "AnnotationRelationLinkManager" and \
                        relation_class.__name__ != "AbstractRelation":

                    relation_classes.append(relation_class)
                    relation_names.append(relation_name.lower())

            cls._all_relation_classes = relation_classes
            cls._all_relation_names = relation_names

        return cls._all_relation_classes


    @classmethod
    def get_all_relation_names(cls):
        """
        :return: list of all class names in lower case of the relations defined within this models' module
        """

        if cls._all_relation_classes == None:

            # The instantion logic of relation_names list is coupled to the instantiation logic of the relation_classes
            # list done in the method 'get_all_relation_classes'; hence just calling that is sufficient.
            cls.get_all_relation_classes()

        return cls._all_relation_names



    # Methods dealing with related relations and entities
    ####################################################################################################################


    _relation_classes_of_entity_class = {}
    _relation_names_of_entity_class = {}


    @classmethod
    def get_relation_classes_of_entity_class(cls, entity_class):
        """
        :param entity_class : class of an entity for which the related relations should be returned
        :return: a list of relation classes that are related to the entity class

        E.g. AbstractRelation.get_relation_classes_of_entity_class( Person )
        -> [ PersonEvent, PersonInstitution, PersonPerson, PersonPlace, PersonWork ]
        """

        return cls._relation_classes_of_entity_class[entity_class]


    @classmethod
    def add_relation_class_of_entity_class(cls, entity_class):
        """
        Adds the given entity class to a list which is later retrieved via a dictionary, where the entity class
        defines the key and the list of related relation classes as its values.

        :param entity_class: the class for which the related relation (the current cls) will be saved into a respective list.
        :return: None
        """

        # get the list of the class dictionary, create if not yet exists.
        relation_class_list = cls._relation_classes_of_entity_class.get(entity_class, [])
        # append the current relation class to the list.
        relation_class_list.append(cls)
        # save into the dictionary, which uses the entity class as key and the extended list above as value.
        cls._relation_classes_of_entity_class[entity_class] = relation_class_list


    @classmethod
    def get_relation_field_names_of_entity_class(cls, entity_class):
        """
        :param entity_class : class of an entity for which the related relation class field names should be returned
        :return: a list of relation class field names that are related to the entity class

        E.g. AbstractRelation.get_relation_names_of_entity_class( Person )
        -> [ personevent_set, personinstitution_set, related_personA, related_personB, personplace_set, personwork_set ]
        """

        return cls._relation_names_of_entity_class[entity_class]


    @classmethod
    def add_relation_name_of_entity_class(cls, relation_name, entity_class):
        """
        Adds the given entity class to a list which is later retrieved via a dictionary, where the entity class
        defines the key and the list of related relation classes as its values.

        :param entity_class: the class for which the related relation (the current cls) will be saved into a respective list.
        :return: None
        """

        # get the list of the class dictionary, create if not yet exists.
        relation_names_list = cls._relation_names_of_entity_class.get(entity_class, [])
        # append the current relation field name to the list.
        relation_names_list.append(relation_name)
        # save into the dictionary, which uses the entity class as key and the extended list above as value.
        cls._relation_names_of_entity_class[entity_class] = relation_names_list


    def get_related_entity_instanceA(self):
        """
        This method only works on the relation instance of a given relation class.
        There it returns the instance of an entity on the 'A' side of the given relation instance.

        Note that if your IDE complains about expecting a 'str' instead of 'None' this happens because
        the method 'get_related_entity_field_nameA()' is only implemented and overridden at runtime in the
        function 'generate_all_fields' in the class 'EntityRelationFieldGenerator'.

        :return: An entity instance related to the current relation instance
        """
        return getattr( self, self.get_related_entity_field_nameA() )


    def get_related_entity_instanceB(self):
        """
        This method only works on the relation instance of a given relation class.
        There it returns the instance of an entity on the 'B' side of the given relation instance.

        Note that if your IDE complains about expecting a 'str' instead of 'None' this happens because
        the method 'get_related_entity_field_nameB()' is only implemented and overridden at runtime in the
        function 'generate_all_fields' in the class 'EntityRelationFieldGenerator'.

        :return: An entity instance related to the current relation instance
        """
        return getattr( self, self.get_related_entity_field_nameB() )



    # method stumps
    ####################################################################################################################
    # These stumps merely serve as placeholders so that both IDE and developers know that these methods exist.
    # They are implemented programmatically in the function 'generate_all_fields' in the class 'EntityRelationFieldGenerator'.


    @classmethod
    def get_related_entity_classA(cls):
        """
        :return: the python class of the A side of the current relation class or instance
        E.g. PersonWork -> Person
        """
        return None

    @classmethod
    def get_related_entity_classB(cls):
        """
        :return: the python class of the B side of the current relation class or instance
        E.g. PersonWork -> Work
        """
        return None

    @classmethod
    def get_related_entity_field_nameA(cls):
        """
        :return: the name of the field of the A side of the current relation class or instance
        E.g. PersonWork -> "related_person"
        """
        return None

    @classmethod
    def get_related_entity_field_nameB(cls):
        """
        :return: the name of the field of the B side of the current relation class or instance
        E.g. PersonWork -> "related_work"
        """
        return None




#######################################################################
#
# Person - ... - Relation
#
#######################################################################


@reversion.register(follow=['tempentityclass_ptr'])
class PersonPerson(AbstractRelation):

    pass


@reversion.register(follow=['tempentityclass_ptr'])
class PersonPlace(AbstractRelation):

    pass


@reversion.register(follow=['tempentityclass_ptr'])
class PersonInstitution(AbstractRelation):

    pass


@reversion.register(follow=['tempentityclass_ptr'])
class PersonEvent(AbstractRelation):

    pass


@reversion.register(follow=['tempentityclass_ptr'])
class PersonWork(AbstractRelation):

    pass


#######################################################################
#
#   Institution - ... - Relation
#
#######################################################################


@reversion.register(follow=['tempentityclass_ptr'])
class InstitutionInstitution(AbstractRelation):

    pass


@reversion.register(follow=['tempentityclass_ptr'])
class InstitutionPlace(AbstractRelation):

    pass


@reversion.register(follow=['tempentityclass_ptr'])
class InstitutionEvent(AbstractRelation):

    pass


@reversion.register(follow=['tempentityclass_ptr'])
class InstitutionWork(AbstractRelation):

    pass


#######################################################################
#
#   Place - ... - Relation
#
#######################################################################


@reversion.register(follow=['tempentityclass_ptr'])
class PlacePlace(AbstractRelation):

    pass


@reversion.register(follow=['tempentityclass_ptr'])
class PlaceEvent(AbstractRelation):

    pass


@reversion.register(follow=['tempentityclass_ptr'])
class PlaceWork(AbstractRelation):

    pass


#######################################################################
#
#   Event - ... - Relation
#
#######################################################################


@reversion.register(follow=['tempentityclass_ptr'])
class EventEvent(AbstractRelation):

    pass


@reversion.register(follow=['tempentityclass_ptr'])
class EventWork(AbstractRelation):

    pass


#######################################################################
#
#   Work - ... - Relation
#
#######################################################################


@reversion.register(follow=['tempentityclass_ptr'])
class WorkWork(AbstractRelation):

    pass
