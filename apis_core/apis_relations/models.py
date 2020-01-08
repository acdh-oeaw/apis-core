from django.contrib.contenttypes.models import ContentType
from django.db import models
#from reversion import revisions as reversion
import reversion
from django.db.models import Q
import operator
import pdb
import inspect
import sys

from apis_core.apis_entities.models import Person, Place, Institution, Event, Passage, Publication
from apis_core.apis_metainfo.models import TempEntityClass
from apis_core.apis_vocabularies.models import (PersonPersonRelation, PersonPlaceRelation,
    PersonInstitutionRelation, PersonEventRelation, PersonPassageRelation, PersonPublicationRelation,
    InstitutionInstitutionRelation, InstitutionEventRelation, InstitutionPlaceRelation,
    InstitutionPassageRelation, InstitutionPublicationRelation, PlacePlaceRelation, PlaceEventRelation,
    PlacePassageRelation, PlacePublicationRelation, EventEventRelation, EventPassageRelation,
    EventPublicationRelation, PassagePassageRelation, PassagePublicationRelation, PublicationPublicationRelation)


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
#

class AbstractRelation(TempEntityClass):
    """
    Abstract super class which encapsulates common logic between the different relations and provides various methods
    relating to either all or specific relations.
    """

    # TODO __sresch__ : Consider moving the annotation manager into this class and remove it from all subclasses
    # annotation_links = AnnotationRelationLinkManager()

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

    # private class variables used for saving both class dependent and class independent information
    # for more convenient retrieval later on.
    # Initially defined as empty lists, they will be properly instantiated on their first call

    _all_relation_classes = None
    _all_relation_names = None
    _relation_classes_of_entity_class = {}
    _relation_names_of_entity_class = {}


    # Methods dealing with all relations
    ####################################################################################################################


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
        the method 'get_related_entity_field_nameA()' is not implemented before runtime and will be overridden at runtime
        within the function 'generate_relation_fields'.

        :return: An entity instance related to the current relation instance
        """
        return getattr( self, self.get_related_entity_field_nameA() )


    def get_related_entity_instanceB(self):
        """
        This method only works on the relation instance of a given relation class.
        There it returns the instance of an entity on the 'B' side of the given relation instance.

        Note that if your IDE complains about expecting a 'str' instead of 'None' this happens because
        the method 'get_related_entity_field_nameB()' is not implemented before runtime and will be overridden at runtime
        within the function 'generate_relation_fields'.

        :return: An entity instance related to the current relation instance
        """
        return getattr( self, self.get_related_entity_field_nameB() )



    # method stumps
    ####################################################################################################################
    # These stumps merely serve as placeholders so that both IDE and developers know that these methods exist.
    # They are implemented programmatically in the function 'generate_relation_fields'.


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



    # meta logic which wires everything together programmatically
    ####################################################################################################################

    @classmethod
    def generate_relation_fields(cls):
        """
        This function goes through every relation automatically and creates the relation fields to their respective entity
        classes.

        The wiring is done by going reflectively through the python code and finding in the respective model modules the relevant classes.

        Django's ContentType interface could not be used since this relies on full class declaration before calling any models,
        however since we want to define attributes of models during their declaration, this was not possible and thus python's
        own code inspection had to be used.

        E.g. for PersonWork these fields are auto-generated: related_person, and related_work.
        for PersonPerson: related_personA, and related_personB

        This function is called just below.

        :return: None
        """

        # functions to create classmethods on the relation classes, so that these methods can be called both on
        # the class level as well as on the instance level.

        def create_function_get_related_entity_class(related_entity_class):
            """
            :param related_entity_class: the class which the generated class method shall return
            :return: an anonymous function which is assigned as method with a label respective to relation and entity classes.
            """
            return classmethod(lambda cls: related_entity_class)

        def create_function_get_related_entity_field_name(related_entity_field_name):
            """
            :param related_entity_field_name: the name of the related entity which the generated class method shall return
            :return: an anonymous function which is assigned as method with a label respective to relation and entity classes.
            """
            return classmethod(lambda cls: related_entity_field_name)

        # TODO __sresch__ : check for best practice on local imports vs circularity problems.
        from apis_core.apis_entities.models import AbstractEntity
        from apis_core.apis_vocabularies.models import AbstractRelationType

        # all the classes which are to be iterated over, also in the case of relation and relationtype they are sorted to ensure their proper alignment
        entity_classes = AbstractEntity.get_all_entity_classes()
        relation_classes = cls.get_all_relation_classes()
        relation_classes.sort(key=lambda x : x.__name__)
        relationtype_classes = AbstractRelationType.get_all_relationtype_classes()
        relationtype_classes.sort(key=lambda x : x.__name__)

        # Iterate over all entity classes, twice, so that all relations between all entity classes are covered.
        for entity_class_a in AbstractEntity.get_all_entity_classes():
            for entity_class_b in AbstractEntity.get_all_entity_classes():

                # relation_class_name = relation_class.__name__.lower()
                entity_class_a_name = entity_class_a.__name__.lower()
                entity_class_b_name = entity_class_b.__name__.lower()

                # inner loop iterating over each of the relation_class and relationtype at the same time, which were sorted before
                # in order to align the relation_class and relationtype_class with each other.
                for relation_class, relationtype_class in zip(relation_classes, relationtype_classes):

                    relation_class_name = relation_class.__name__.lower()
                    relationtype_class_name = relationtype_class.__name__.lower()

                    # Ensure that relation_class and relationtype_class are indeed talking about the same relation
                    # If this error is thrown then it would indicate misaligment in the models themselves
                    # which would be a critical violation of the models.
                    if relation_class_name not in relationtype_class_name:
                        raise Exception(
                            "Mismatch found between Relation and RelationType class:\n" +
                            str(relation_class) + " and " + str(relationtype_class) + "!"
                            "\nMaybe for the given Relation class there does not exist a corresponding RelationType class (or vice versa)?"
                        )

                    # Check if current relation related to both entities
                    # Note that this way two entites are checked twice, such as person - place and place - person
                    # but however in the relation model only one of these two exists. Thus the right one is picked.
                    if entity_class_a_name + entity_class_b_name == relation_class_name:

                        if entity_class_a != entity_class_b:
                            # If the classes are different, then the related field names need to be set accordingly.
                            #  E.g. for PersonWork: related_person, and related_work

                            relation_field_name_a = "related_" + entity_class_a_name
                            relation_field_name_b = "related_" + entity_class_b_name

                            # To stick to common Django ORM Syntax, set the field name in the related entity class to
                            # the current relation name and add '_set' to it (since going from the entity one would have
                            # multiple relation instances possibly.)
                            relation_field_name_in_other_class = entity_class_a_name + entity_class_b_name + "_set"

                            # Create the related entity field A.
                            models.ForeignKey(
                                to=entity_class_a,
                                blank=True,
                                null=True,
                                on_delete=models.CASCADE,
                                related_name=relation_field_name_in_other_class
                            ).contribute_to_class(relation_class, relation_field_name_a)

                            # Create the related entity field B.
                            models.ForeignKey(
                                to=entity_class_b,
                                blank=True,
                                null=True,
                                on_delete=models.CASCADE,
                                related_name=relation_field_name_in_other_class
                            ).contribute_to_class(relation_class, relation_field_name_b)

                            # Create the related relaiontype field
                            models.ForeignKey(
                                to=relationtype_class,
                                blank=True,
                                null=True,
                                on_delete=models.CASCADE,
                                related_name=relation_field_name_in_other_class
                            ).contribute_to_class(relation_class, "relation_type")


                            # Implemented the following methods programmatically by setting the respective relations,
                            # entity class references, names, etc.
                            # Note that these methods are first defined as stumps within AbstractRelation for documentation
                            # purposes.

                            relation_class.get_related_entity_classA = \
                                create_function_get_related_entity_class( entity_class_a )

                            relation_class.get_related_entity_classB = \
                                create_function_get_related_entity_class( entity_class_b )

                            relation_class.get_related_entity_field_nameA = \
                                create_function_get_related_entity_field_name( relation_field_name_a )

                            relation_class.get_related_entity_field_nameB = \
                                create_function_get_related_entity_field_name( relation_field_name_b )

                            relation_class.add_relation_class_of_entity_class(entity_class_a)
                            relation_class.add_relation_class_of_entity_class(entity_class_b)
                            relation_class.add_relation_name_of_entity_class(relation_name=relation_field_name_in_other_class, entity_class=entity_class_a)
                            relation_class.add_relation_name_of_entity_class(relation_name=relation_field_name_in_other_class, entity_class=entity_class_b)

                        else:
                            # If the classes are not different, then the related field names need to be set accordingly.
                            #  E.g. for PersonPerson: related_personA, and related_personB

                            entity_class_name = entity_class_a_name
                            entity_class = entity_class_a
                            relation_field_name_a = "related_" + entity_class_name + "A"
                            relation_field_name_b = "related_" + entity_class_name + "B"

                            # Within APIS it was manually set that from a given entity which relates to a relation containing
                            # the same entity class twice (e.g. PersonPerson), within the given entity class the
                            # field's name was 'related_<entity>A', and 'related_<entity>B' (e.g. Person.related_personA).
                            # This is not consistent with the other relation fields of a given entity
                            # (e.g. for PersonWork, in Person and Work, it would refer to the relation via 'personwork_set').
                            #
                            # This should be changed, but it would result in crashes where code would not be adapted.
                            #
                            # So, for now, in order to not break APIS and to keep downwards-compatibility, the same fields are
                            # generated as before.
                            relation_field_name_in_other_class_a = relation_field_name_b
                            relation_field_name_in_other_class_b = relation_field_name_a
                            relation_field_name_in_other_class = entity_class_a_name + entity_class_b_name + "_set"

                            # TODO __sresch__ : use the following related name for consistency reasons once most code breaking parts due to this change are identified.
                            #
                            # Unfortuantely it does not seem possible to have an Entity refer to a symmetric relation with
                            # only the relation name (E.g. that both Person A and Person B would refer to the PersonPerson relation
                            # via 'personperson_set'). So later it will be changed to 'personpersonA_set', and 'personpersonB_set'
                            # to be a bit more consistent with other usages. So, uncomment the following once breaking parts
                            # are identified and prepared for it.
                            #
                            # relation_field_name_from_entity_a = entity_class_name * 2 + "B_set"
                            # relation_field_name_from_entity_b = entity_class_name * 2 + "A_set"

                            # Create the related entity field A.
                            models.ForeignKey(
                                to=entity_class,
                                blank=True,
                                null=True,
                                on_delete=models.CASCADE,
                                related_name=relation_field_name_in_other_class_a
                            ).contribute_to_class(relation_class, relation_field_name_a)

                            # Create the related entity field B.
                            models.ForeignKey(
                                to=entity_class,
                                blank=True,
                                null=True,
                                on_delete=models.CASCADE,
                                related_name=relation_field_name_in_other_class_b
                            ).contribute_to_class(relation_class, relation_field_name_b)

                            # Create the related relaiontype field
                            models.ForeignKey(
                                to=relationtype_class,
                                blank=True,
                                null=True,
                                on_delete=models.CASCADE,
                                related_name=relation_field_name_in_other_class
                            ).contribute_to_class(relation_class, "relation_type")


                            # Implemented the following methods programmatically by setting the respective relations,
                            # entity class references, names, etc.
                            # Note that these methods are first defined as stumps within AbstractRelation for documentation
                            # purposes.

                            relation_class.get_related_entity_classA = \
                                create_function_get_related_entity_class( entity_class )

                            relation_class.get_related_entity_classB = \
                                create_function_get_related_entity_class( entity_class )

                            relation_class.get_related_entity_field_nameA = \
                                create_function_get_related_entity_field_name( relation_field_name_a )

                            relation_class.get_related_entity_field_nameB = \
                                create_function_get_related_entity_field_name( relation_field_name_b )

                            relation_class.add_relation_class_of_entity_class(entity_class)
                            relation_class.add_relation_name_of_entity_class(relation_name=relation_field_name_in_other_class_a, entity_class=entity_class)
                            relation_class.add_relation_name_of_entity_class(relation_name=relation_field_name_in_other_class_b, entity_class=entity_class)


                        # if entity_class_a_name + entity_class_b_name == relation_class_name
                        # equals to True, then for entity_class_a and entity_class_b, their respective relation class
                        # has been found, thus interrupt the loop going through these relation classes.
                        break







#######################################################################
#
# Person - ... - Relation
#
#######################################################################


@reversion.register(follow=['tempentityclass_ptr'])
class PersonPerson(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()


@reversion.register(follow=['tempentityclass_ptr'])
class PersonPlace(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()


# PlacePerson = PersonPlace TODO __sresch__

@reversion.register(follow=['tempentityclass_ptr'])
class PersonInstitution(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()


@reversion.register(follow=['tempentityclass_ptr'])
class PersonEvent(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()


@reversion.register(follow=['tempentityclass_ptr'])
class PersonPassage(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()


@reversion.register(follow=['tempentityclass_ptr'])
class PersonPublication(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()



#######################################################################
#
#   Institution - ... - Relation
#
#######################################################################


@reversion.register(follow=['tempentityclass_ptr'])
class InstitutionInstitution(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()


@reversion.register(follow=['tempentityclass_ptr'])
class InstitutionPlace(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()


@reversion.register(follow=['tempentityclass_ptr'])
class InstitutionEvent(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()


@reversion.register(follow=['tempentityclass_ptr'])
class InstitutionPassage(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()


@reversion.register(follow=['tempentityclass_ptr'])
class InstitutionPublication(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()



#######################################################################
#
#   Place - ... - Relation
#
#######################################################################


@reversion.register(follow=['tempentityclass_ptr'])
class PlacePlace(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()


@reversion.register(follow=['tempentityclass_ptr'])
class PlaceEvent(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()


@reversion.register(follow=['tempentityclass_ptr'])
class PlacePassage(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()


@reversion.register(follow=['tempentityclass_ptr'])
class PlacePublication(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()



#######################################################################
#
#   Event - ... - Relation
#
#######################################################################


@reversion.register(follow=['tempentityclass_ptr'])
class EventEvent(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()


@reversion.register(follow=['tempentityclass_ptr'])
class EventPassage(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()


@reversion.register(follow=['tempentityclass_ptr'])
class EventPublication(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()


#######################################################################
#
#   Passage - ... - Relation
#
#######################################################################


@reversion.register(follow=['tempentityclass_ptr'])
class PassagePassage(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()


@reversion.register(follow=['tempentityclass_ptr'])
class PassagePublication(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()


#######################################################################
#
#   Publication - ... - Relation
#
#######################################################################


@reversion.register(follow=['tempentityclass_ptr'])
class PublicationPublication(AbstractRelation):

    annotation_links = AnnotationRelationLinkManager()




# Call the meta logic method here, after all relevant relation classes have been defined above
AbstractRelation.generate_relation_fields()

