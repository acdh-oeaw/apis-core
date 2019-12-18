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
#

class AbstractRelation(TempEntityClass):
    """
    Abstract super class which encapsulates common logic between the different relations and provides various methods
    relating to either all or a specific relations.
    """

    class Meta:
        abstract = True

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
        the method 'get_related_entity_field_nameA()' is only implemented and overridden at runtime in the
        function 'generated_relation_fields'.

        :return: An entity instance related to the current relation instance
        """
        return getattr( self, self.get_related_entity_field_nameA() )


    def get_related_entity_instanceB(self):
        """
        This method only works on the relation instance of a given relation class.
        There it returns the instance of an entity on the 'B' side of the given relation instance.

        Note that if your IDE complains about expecting a 'str' instead of 'None' this happens because
        the method 'get_related_entity_field_nameB()' is only implemented and overridden at runtime in the
        function 'generated_relation_fields'.

        :return: An entity instance related to the current relation instance
        """
        return getattr( self, self.get_related_entity_field_nameB() )



    # method stumps
    ####################################################################################################################
    # These stumps merely serve as placeholders so that both IDE and developers know that these methods exist.
    # They are implemented programmatically in the function 'generated_relation_fields'.


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
    """Defines and describes a relation between a Person and another Person

    :param int relation_type: Foreign Key to :class:`vocabularies.models.PersonPersonRelation`
    :param int related_personA: Foreign Key to :class:`entities.models.Person`
    :param int related_personB: Foreign Key to :class:`entities.models.Person`
    """

    relation_type = models.ForeignKey(PersonPersonRelation, blank=True,
                                      null=True, on_delete=models.SET_NULL)

    annotation_links = AnnotationRelationLinkManager()

    def __str__(self):
        return "{} ({}) {}".format(self.related_personA, self.relation_type, self.related_personB)

    def get_web_object(self):
        """Used in some html views.

        :return: Dict with object properties
        """
        if self.related_personA.first_name is None:
            self.related_personA.first_name = '-'
        if self.related_personB.first_name is None:
            self.related_personB.first_name = '-'
        result = {
            'relation_pk': self.pk,
            'relation_type': self.relation_type.name,
            'related_personA': self.related_personA.name+', '+self.related_personA.first_name,
            'related_personB': self.related_personB.name+', '+self.related_personB.first_name,
            'start_date': self.start_date_written,
            'end_date': self.end_date_written}
        return result

    def get_table_dict(self, entity):
        """
        Function that returns dict used in relation tables.

        :param entity: :class:`entities.models.Person` instance that is the starting point of the table.
        :return: dict
        """
        if self.related_personA == entity:
            rel_pers = self.related_personB
            rel_type = self.relation_type.label
        elif self.related_personB == entity:
            rel_pers = self.related_personA
            rel_type = self.relation_type.label_reverse
        result = {
            'pk': self.pk,
            'relation_type': rel_type,
            'related_person': rel_pers,
            'start_date_written': self.start_date_written,
            'end_date_written': self.end_date_written,
            'start_date': self.start_date,
            'end_date': self.end_date}
        return result


@reversion.register(follow=['tempentityclass_ptr'])
class PersonPlace(AbstractRelation):
    """Defines and describes a relation between a Person and a Place

    :param int relation_type: Foreign Key to :class:`vocabularies.models.PersonPlaceRelation`
    :param int related_person: Foreign Key to :class:`entities.models.Person`
    :param int related_place: Foreign Key to :class:`entities.models.Place`
    """

    relation_type = models.ForeignKey(PersonPlaceRelation, blank=True,
                                      null=True, on_delete=models.SET_NULL)

    annotation_links = AnnotationRelationLinkManager()

    def __str__(self):
        return "{} ({}) {}".format(self.related_person, self.relation_type, self.related_place)

    def get_web_object(self):
        """Used in some html views.

        :return: Dict with object properties
        """

        if self.related_person.first_name is None:
            self.related_person.first_name = '-'
        result = {
            'relation_pk': self.pk,
            'relation_type': self.relation_type.name,
            'related_person': self.related_person.name+', '+self.related_person.first_name,
            'related_place': self.related_place.name,
            'start_date': self.start_date_written,
            'end_date': self.end_date_written}
        return result


@reversion.register(follow=['tempentityclass_ptr'])
class PersonInstitution(AbstractRelation):
    """ Defines and describes a relation between a Person and a Institution

    :param int relation_type: Foreign Key to :class:`vocabularies.models.PersonInstitutionRelation`
    :param int related_person: Foreign Key to :class:`entities.models.Person`
    :param int related_institution: Foreign Key to :class:`entities.models.Institution`
    """

    relation_type = models.ForeignKey(PersonInstitutionRelation, blank=True,
                                      null=True, on_delete=models.SET_NULL)

    annotation_links = AnnotationRelationLinkManager()

    def __str__(self):
        return "{} ({}) {}".format(
            self.related_person, self.relation_type, self.related_institution)

    def get_web_object(self):

        if self.related_person.first_name is None:
            self.related_person.first_name = '-'
        result = {
            'relation_pk': self.pk,
            'relation_type': self.relation_type.name,
            'related_person': self.related_person.name+', '+self.related_person.first_name,
            'related_institution': self.related_institution.name,
            'start_date': self.start_date_written,
            'end_date': self.end_date_written}
        return result


@reversion.register(follow=['tempentityclass_ptr'])
class PersonEvent(AbstractRelation):
    """ Defines and describes a relation bewteen a Person and an Event

    :param int relation_type: Foreign Key to :class:`vocabularies.models.PersonEventRelation`
    :param int related_person: Foreign Key to :class:`entities.models.Person`
    :param int related_event: Foreign Key to :class:`entities.models.Event`
    """

    relation_type = models.ForeignKey(PersonEventRelation, blank=True,
                                      null=True, on_delete=models.SET_NULL)

    annotation_links = AnnotationRelationLinkManager()

    def __str__(self):
        return "{} ({}) {}".format(self.related_person, self.relation_type, self.related_event)

    def get_web_object(self):

        if self.related_person.first_name is None:
            self.related_person.first_name = '-'
        result = {
            'relation_pk': self.pk,
            'relation_type': self.relation_type.name,
            'related_person': self.related_person.name+', '+self.related_person.first_name,
            'related_event': self.related_event.name,
            'start_date': self.start_date_written,
            'end_date': self.end_date_written}
        return result


@reversion.register(follow=['tempentityclass_ptr'])
class PersonWork(AbstractRelation):
    """ Defines and describes a relation between a Person and a Work

    :param int relation_type: Foreign Key to :class:`vocabularies.models.PersonWorkRelation`
    :param int related_person: Foreign Key to :class:`entities.models.Person`
    :param int related_work: Foreign Key to :class:`entities.models.Work`
    """

    relation_type = models.ForeignKey(PersonWorkRelation, blank=True, null=True,
                                      on_delete=models.SET_NULL)

    annotation_links = AnnotationRelationLinkManager()

    def __str__(self):
        return "{} ({}) {}".format(self.related_person, self.relation_type, self.related_work)

    def get_web_object(self):

        if self.related_person.first_name is None:
            self.related_person.first_name = '-'
        result = {
            'relation_pk': self.pk,
            'relation_type': self.relation_type.name,
            'related_person': self.related_person.name+', '+self.related_person.first_name,
            'related_work': self.related_work.name,
            'start_date': self.start_date_written,
            'end_date': self.end_date_written}
        return result


#######################################################################
#
#   Institution - ... - Relation
#
#######################################################################


@reversion.register(follow=['tempentityclass_ptr'])
class InstitutionInstitution(AbstractRelation):
    """ Defines and describes a relation between two Institutions

    :param int relation_type: Foreign Key to :class:`vocabularies.models.InstitutionInstitutionRelation`
    :param int related_institutionA: Foreign Key to :class:`entities.models.Institution`
    :param int related_institutionB: Foreign Key to :class:`entities.models.Institution`
    """

    relation_type = models.ForeignKey(InstitutionInstitutionRelation,
                                      blank=True, null=True,
                                      on_delete=models.SET_NULL)

    annotation_links = AnnotationRelationLinkManager()

    def __str__(self):
        return "{} ({}) {}".format(
            self.related_institutionA, self.relation_type, self.related_institutionB)

    def get_web_object(self):
        result = {
            'relation_pk': self.pk,
            'relation_type': self.relation_type.name,
            'related_institutionA': self.related_institutionA.name,
            'related_institutionB': self.related_institutionB.name,
            'start_date': self.start_date_written,
            'end_date': self.end_date_written}
        return result

    def get_table_dict(self, entity):
        if self.related_institutionA == entity:
            rel_inst = self.related_institutionB
            rel_type = self.relation_type.label
        elif self.related_institutionB == entity:
            rel_inst = self.related_institutionA
            rel_type = self.relation_type.label_reverse
        result = {
            'relation_pk': self.pk,
            'relation_type': rel_type,
            'related_institution': rel_inst,
            'start_date_written': self.start_date_written,
            'end_date_written': self.end_date_written,
            'start_date': self.start_date,
            'end_date': self.end_date}
        return result


@reversion.register(follow=['tempentityclass_ptr'])
class InstitutionPlace(AbstractRelation):
    """Describes a relation bewteen an Institution  and a Place

    :param int relation_type: Foreign Key to :class:`vocabularies.models.InstitutionPlaceRelation`
    :param int related_institution: Foreign Key to :class:`entities.models.Institution`
    :param int related_place: Foreign Key to :class:`entities.models.Place`
    """

    relation_type = models.ForeignKey(
        InstitutionPlaceRelation, blank=True, null=True,
        on_delete=models.SET_NULL)

    annotation_links = AnnotationRelationLinkManager()

    def __str__(self):
        return "{} ({}) {}".format(
            self.related_institution, self.relation_type, self.related_place)

    def get_web_object(self):
        result = {
            'relation_pk': self.pk,
            'relation_type': self.relation_type.name,
            'related_institution': self.related_institution.name,
            'related_place': self.related_place.name,
            'start_date': self.start_date_written,
            'end_date': self.end_date_written}
        return result


@reversion.register(follow=['tempentityclass_ptr'])
class InstitutionEvent(AbstractRelation):
    """Describes a relation bewteen an Institution and an Event

    :param int relation_type: Foreign Key to :class:`vocabularies.models.InstitutionEventRelation`
    :param int related_institution: Foreign Key to :class:`entities.models.Institution`
    :param int related_event: Foreign Key to :class:`entities.models.Event`
    """

    relation_type = models.ForeignKey(InstitutionEventRelation, blank=True,
                                      null=True, on_delete=models.SET_NULL)

    annotation_links = AnnotationRelationLinkManager()

    def __str__(self):
        return "{} ({}) {}".format(
            self.related_institution, self.relation_type, self.related_event)

    def get_web_object(self):
        result = {
            'relation_pk': self.pk,
            'relation_type': self.relation_type.name,
            'related_institution': self.related_institution.name,
            'related_event': self.related_event.name,
            'start_date': self.start_date_written,
            'end_date': self.end_date_written}
        return result


@reversion.register(follow=['tempentityclass_ptr'])
class InstitutionWork(AbstractRelation):
    """Describes a relation bewteen an Institution and a Work

    :param int relation_type: Foreign Key to :class:`vocabularies.models.InstitutionWorkRelation`
    :param int related_institution: Foreign Key to :class:`entities.models.Institution`
    :param int related_work: Foreign Key to :class:`entities.models.Work`
    """

    relation_type = models.ForeignKey(InstitutionWorkRelation, blank=True,
                                      null=True, on_delete=models.SET_NULL)

    annotation_links = AnnotationRelationLinkManager()

    def __str__(self):
        return "{} ({}) {}".format(
            self.related_institution, self.relation_type, self.related_work)

    def get_web_object(self):
        result = {
            'relation_pk': self.pk,
            'relation_type': self.relation_type.name,
            'related_institution': self.related_institution.name,
            'related_work': self.related_work.name,
            'start_date': self.start_date_written,
            'end_date': self.end_date_written}
        return result



#######################################################################
#
#   Place - ... - Relation
#
#######################################################################


@reversion.register(follow=['tempentityclass_ptr'])
class PlacePlace(AbstractRelation):
    """Describes a relation bewteen an Place  and a Place

    :param int relation_type: Foreign Key to :class:`vocabularies.models.PlacePlaceRelation`
    :param int related_placeA: Foreign Key to :class:`entities.models.Place`
    :param int related_placeB: Foreign Key to :class:`entities.models.Place`
    """

    relation_type = models.ForeignKey(PlacePlaceRelation, blank=True, null=True,
                                      on_delete=models.SET_NULL)

    annotation_links = AnnotationRelationLinkManager()

    def __str__(self):
        return "{} ({}) {}".format(self.related_placeA, self.relation_type, self.related_placeB)

    def get_table_dict(self, entity):
        """Dict for the tabels in the html view

        :param entity: Object of type :class:`entities.models.Place`; Used to determine which Place is the main antity
            and which one the related.
        :return:
        """
        if self.related_placeA == entity:
            rel_place = self.related_placeB
            rel_type = self.relation_type.label
        elif self.related_placeB == entity:
            rel_place = self.related_placeA
            rel_type = self.relation_type.label_reverse
        result = {
            'relation_pk': self.pk,
            'relation_type': rel_type,
            'related_place': rel_place,
            'start_date_written': self.start_date_written,
            'end_date_written': self.end_date_written,
            'start_date': self.start_date,
            'end_date': self.end_date}
        return result

    def get_web_object(self):
        """Used in some html views.

        :return: Dict with object properties
        """
        result = {
            'relation_pk': self.pk,
            'relation_type': self.relation_type.name,
            'related_placeA': self.related_placeA.name,
            'related_placeB': self.related_placeB.name,
            'start_date': self.start_date_written,
            'end_date': self.end_date_written}
        return result


@reversion.register(follow=['tempentityclass_ptr'])
class PlaceEvent(AbstractRelation):
    """Describes a relation between an Place and an Event

    :param int relation_type: Foreign Key to :class:`vocabularies.models.PlaceEventRelation`
    :param int related_place: Foreign Key to :class:`entities.models.Place`
    :param int related_event: Foreign Key to :class:`entities.models.Event`
    """

    relation_type = models.ForeignKey(PlaceEventRelation, blank=True, null=True,
                                      on_delete=models.SET_NULL)

    annotation_links = AnnotationRelationLinkManager()

    def __str__(self):
        return "{} ({}) {}".format(
            self.related_place, self.relation_type, self.related_event)

    def get_web_object(self):
        """Function that returns a dict that is used in html views.

        :return: dict of attributes
        """
        result = {
            'relation_pk': self.pk,
            'relation_type': self.relation_type.name,
            'related_place': self.related_place.name,
            'related_event': self.related_event.name,
            'start_date': self.start_date_written,
            'end_date': self.end_date_written}
        return result


@reversion.register(follow=['tempentityclass_ptr'])
class PlaceWork(AbstractRelation):
    """Describes a relation between an Place and a Work

    :param int relation_type: Foreign Key to :class:`vocabularies.models.PlaceWorkRelation`
    :param int related_place: Foreign Key to :class:`entities.models.Place`
    :param int related_Work: Foreign Key to :class:`entities.models.Work`
    """

    relation_type = models.ForeignKey(PlaceWorkRelation, blank=True, null=True,
                                      on_delete=models.SET_NULL)

    annotation_links = AnnotationRelationLinkManager()

    def __str__(self):
        return "{} ({}) {}".format(
            self.related_place, self.relation_type, self.related_work)

    def get_web_object(self):
        """Function that returns a dict that is used in html views.

        :return: dict of attributes
        """
        result = {
            'relation_pk': self.pk,
            'relation_type': self.relation_type.name,
            'related_place': self.related_place.name,
            'related_work': self.related_work.name,
            'start_date': self.start_date_written,
            'end_date': self.end_date_written}
        return result


#######################################################################
#
#   Event - ... - Relation
#
#######################################################################


@reversion.register(follow=['tempentityclass_ptr'])
class EventEvent(AbstractRelation):
    """Describes a relation between an Event and an Event

    :param int relation_type: Foreign Key to :class:`vocabularies.models.EventEventRelation`
    :param int related_eventA: Foreign Key to :class:`entities.models.Event`
    :param int related_eventB: Foreign Key to :class:`entities.models.Event`
    """

    relation_type = models.ForeignKey(EventEventRelation, blank=True, null=True,
                                      on_delete=models.SET_NULL)

    annotation_links = AnnotationRelationLinkManager()

    def __str__(self):
        return "{} ({}) {}".format(self.related_eventA, self.relation_type, self.related_eventB)

    def get_table_dict(self, entity):
        """Dict for the tabels in the html view

        :param entity: Object of type :class:`entities.models.Event`; Used to determine which Event is the main antity
            and which one the related.
        :return:
        """
        if self.related_eventA == entity:
            rel_event = self.related_eventB
            rel_type = self.relation_type.label
        elif self.related_eventB == entity:
            rel_event = self.related_eventA
            rel_type = self.relation_type.label_reverse
        result = {
            'relation_pk': self.pk,
            'relation_type': rel_type,
            'related_event': rel_event,
            'start_date_written': self.start_date_written,
            'end_date_written': self.end_date_written,
            'start_date': self.start_date,
            'end_date': self.end_date}
        return result

    def get_web_object(self):
        """Used in some html views.

        :return: Dict with object properties
        """
        result = {
            'relation_pk': self.pk,
            'relation_type': self.relation_type.name,
            'related_eventA': self.related_eventA.name,
            'related_eventB': self.related_eventB.name,
            'start_date': self.start_date_written,
            'end_date': self.end_date_written}
        return result



@reversion.register(follow=['tempentityclass_ptr'])
class EventWork(AbstractRelation):
    """Describes a relation between an Event and a Work

    :param int relation_type: Foreign Key to :class:`vocabularies.models.EventWorkRelation`
    :param int related_event: Foreign Key to :class:`entities.models.Event`
    :param int related_work: Foreign Key to :class:`entities.models.Work`
    """

    relation_type = models.ForeignKey(EventWorkRelation, blank=True, null=True,
                                      on_delete=models.SET_NULL)

    annotation_links = AnnotationRelationLinkManager()

    def __str__(self):
        return "{} ({}) {}".format(
            self.related_event, self.relation_type, self.related_work)

    def get_web_object(self):
        """Function that returns a dict that is used in html views.

        :return: dict of attributes
        """
        result = {
            'relation_pk': self.pk,
            'relation_type': self.relation_type.name,
            'related_event': self.related_event.name,
            'related_work': self.related_work.name,
            'start_date': self.start_date_written,
            'end_date': self.end_date_written}
        return result


#######################################################################
#
#   Event - ... - Relation
#
#######################################################################


@reversion.register(follow=['tempentityclass_ptr'])
class WorkWork(AbstractRelation):
    """Describes a relation between an Work and a Work

    :param int relation_type: Foreign Key to :class:`vocabularies.models.WorkWorkRelation`
    :param int related_workA: Foreign Key to :class:`entities.models.Work`
    :param int related_workB: Foreign Key to :class:`entities.models.Work`
    """

    relation_type = models.ForeignKey(WorkWorkRelation, blank=True, null=True,
                                      on_delete=models.SET_NULL)

    annotation_links = AnnotationRelationLinkManager()

    def __str__(self):
        return "{} ({}) {}".format(self.related_workA, self.relation_type, self.related_workB)

    def get_table_dict(self, entity):
        """Dict for the tabels in the html view

        :param entity: Object of type :class:`entities.models.Place`; Used to determine which Place is the main antity
            and which one the related.
        :return:
        """
        if self.related_workA == entity:
            rel_work = self.related_workB
            rel_type = self.relation_type.label
        elif self.related_workB == entity:
            rel_work = self.related_workA
            rel_type = self.relation_type.label_reverse
        result = {
            'relation_pk': self.pk,
            'relation_type': rel_type,
            'related_work': rel_work,
            'start_date_written': self.start_date_written,
            'end_date_written': self.end_date_written,
            'start_date': self.start_date,
            'end_date': self.end_date}
        return result

    def get_web_object(self):
        """Used in some html views.

        :return: Dict with object properties
        """
        result = {
            'relation_pk': self.pk,
            'relation_type': self.relation_type.name,
            'related_workA': self.related_workA.name,
            'related_workB': self.related_workB.name,
            'start_date': self.start_date_written,
            'end_date': self.end_date_written}
        return result


def generate_relation_fields():
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

    # Iterate over all entity classes, twice, so that all relations between all entity classes are covered.
    for entity_class_a in AbstractEntity.get_all_entity_classes():
        for entity_class_b in AbstractEntity.get_all_entity_classes():
            # Additionally iterate over all relation classes, manually defined within this current module.
            for relation_class in AbstractRelation.get_all_relation_classes():

                # Generate the names of current relation and its relation fields to other entities.
                relation_class_name = relation_class.__name__.lower()
                entity_class_a_name = entity_class_a.__name__.lower()
                entity_class_b_name = entity_class_b.__name__.lower()

                # Check if the two current entity classes align correctly with an existing relation class from this module.
                if entity_class_a_name + entity_class_b_name == relation_class_name:

                    if entity_class_a != entity_class_b:
                        # If the classes are different, then the related field names need to be set accordingly.
                        #  E.g. for PersonWork: related_person, and related_work

                        relation_field_name_a = "related_" + entity_class_a_name
                        relation_field_name_b = "related_" + entity_class_b_name

                        # To stick to common Django ORM Syntax, set the field name in the related entity class to
                        # the current relation name and add '_set' to it (since going from the entity one would have
                        # multiple relation instances possibly.)
                        relation_field_name_from_entity = entity_class_a_name + entity_class_b_name + "_set"

                        # Create the related entity field A.
                        models.ForeignKey(
                            to=entity_class_a,
                            blank=True,
                            null=True,
                            on_delete=models.CASCADE,
                            related_name=relation_field_name_from_entity
                        ).contribute_to_class(relation_class, relation_field_name_a)

                        # Create the related entity field B.
                        models.ForeignKey(
                            to=entity_class_b,
                            blank=True,
                            null=True,
                            on_delete=models.CASCADE,
                            related_name=relation_field_name_from_entity
                        ).contribute_to_class(relation_class, relation_field_name_b)


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
                        relation_class.add_relation_name_of_entity_class(relation_name=relation_field_name_from_entity, entity_class=entity_class_a)
                        relation_class.add_relation_name_of_entity_class(relation_name=relation_field_name_from_entity, entity_class=entity_class_b)

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
                        relation_field_name_from_entity_a = relation_field_name_b
                        relation_field_name_from_entity_b = relation_field_name_a

                        # TODO __sresch__ : use this related name for consistency reasons once most code breaking parts due to this change are identified.
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
                            related_name=relation_field_name_from_entity_a
                        ).contribute_to_class(relation_class, relation_field_name_a)

                        # Create the related entity field B.
                        models.ForeignKey(
                            to=entity_class,
                            blank=True,
                            null=True,
                            on_delete=models.CASCADE,
                            related_name=relation_field_name_from_entity_b
                        ).contribute_to_class(relation_class, relation_field_name_b)


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
                        relation_class.add_relation_name_of_entity_class(relation_name=relation_field_name_from_entity_a, entity_class=entity_class)
                        relation_class.add_relation_name_of_entity_class(relation_name=relation_field_name_from_entity_b, entity_class=entity_class)

                    # if entity_class_a_name + entity_class_b_name == relation_class_name
                    # equals to True, then for entity_class_a and entity_class_b, their respective relation class
                    # has been found, thus interrupt the loop going through these relation classes.
                    break


generate_relation_fields()

