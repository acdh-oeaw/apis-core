from django.db import models
#from reversion import revisions as reversion
import reversion
from django.db.models import Q
import operator
import pdb

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
# Person - ... - Relation
#
#######################################################################


@reversion.register(follow=['tempentityclass_ptr'])
class PersonPerson(TempEntityClass):
    """Defines and describes a relation between a Person and another Person

    :param int relation_type: Foreign Key to :class:`vocabularies.models.PersonPersonRelation`
    :param int related_personA: Foreign Key to :class:`entities.models.Person`
    :param int related_personB: Foreign Key to :class:`entities.models.Person`
    """

    relation_type = models.ForeignKey(PersonPersonRelation, blank=True,
                                      null=True, on_delete=models.SET_NULL)
    related_personA = models.ForeignKey(
        Person, blank=True, null=True, related_name="related_personA",
        on_delete=models.CASCADE)
    related_personB = models.ForeignKey(
        Person, blank=True, null=True, related_name="related_personB",
        on_delete=models.CASCADE)
    objects = models.Manager()
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
            rel_type = self.relation_type.name
        elif self.related_personB == entity:
            rel_pers = self.related_personA
            rel_type = self.relation_type.name_reverse
        result = {
            'pk': self.pk,
            'relation_type': rel_type,
            'related_person': rel_pers,
            'start_date': self.start_date,
            'end_date': self.end_date}
        return result


@reversion.register(follow=['tempentityclass_ptr'])
class PersonPlace(TempEntityClass):
    """Defines and describes a relation between a Person and a Place

    :param int relation_type: Foreign Key to :class:`vocabularies.models.PersonPlaceRelation`
    :param int related_person: Foreign Key to :class:`entities.models.Person`
    :param int related_place: Foreign Key to :class:`entities.models.Place`
    """

    relation_type = models.ForeignKey(PersonPlaceRelation, blank=True,
                                      null=True, on_delete=models.SET_NULL)
    related_person = models.ForeignKey(
        Person, blank=True, null=True, on_delete=models.CASCADE)
    related_place = models.ForeignKey(
        Place, blank=True, null=True, on_delete=models.CASCADE)
    objects = models.Manager()
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
class PersonInstitution(TempEntityClass):
    """ Defines and describes a relation between a Person and a Institution

    :param int relation_type: Foreign Key to :class:`vocabularies.models.PersonInstitutionRelation`
    :param int related_person: Foreign Key to :class:`entities.models.Person`
    :param int related_institution: Foreign Key to :class:`entities.models.Institution`
    """

    relation_type = models.ForeignKey(PersonInstitutionRelation, blank=True,
                                      null=True, on_delete=models.SET_NULL)
    related_person = models.ForeignKey(
        Person, blank=True, null=True, on_delete=models.CASCADE)
    related_institution = models.ForeignKey(
        Institution, blank=True, null=True, on_delete=models.CASCADE)
    objects = models.Manager()
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
class PersonEvent(TempEntityClass):
    """ Defines and describes a relation bewteen a Person and an Event

    :param int relation_type: Foreign Key to :class:`vocabularies.models.PersonEventRelation`
    :param int related_person: Foreign Key to :class:`entities.models.Person`
    :param int related_event: Foreign Key to :class:`entities.models.Event`
    """

    relation_type = models.ForeignKey(PersonEventRelation, blank=True,
                                      null=True, on_delete=models.SET_NULL)
    related_person = models.ForeignKey(
        Person, blank=True, null=True, on_delete=models.CASCADE)
    related_event = models.ForeignKey(
        Event, blank=True, null=True, on_delete=models.CASCADE)
    objects = models.Manager()
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
class PersonWork(TempEntityClass):
    """ Defines and describes a relation between a Person and a Work

    :param int relation_type: Foreign Key to :class:`vocabularies.models.PersonWorkRelation`
    :param int related_person: Foreign Key to :class:`entities.models.Person`
    :param int related_work: Foreign Key to :class:`entities.models.Work`
    """

    relation_type = models.ForeignKey(PersonWorkRelation, blank=True, null=True,
                                      on_delete=models.SET_NULL)
    related_person = models.ForeignKey(
        Person, blank=True, null=True, on_delete=models.CASCADE)
    related_work = models.ForeignKey(
        Work, blank=True, null=True, on_delete=models.CASCADE)
    objects = models.Manager()
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
class InstitutionInstitution(TempEntityClass):
    """ Defines and describes a relation between two Institutions

    :param int relation_type: Foreign Key to :class:`vocabularies.models.InstitutionInstitutionRelation`
    :param int related_institutionA: Foreign Key to :class:`entities.models.Institution`
    :param int related_institutionB: Foreign Key to :class:`entities.models.Institution`
    """

    relation_type = models.ForeignKey(InstitutionInstitutionRelation,
                                      blank=True, null=True,
                                      on_delete=models.SET_NULL)
    related_institutionA = models.ForeignKey(
        Institution, blank=True, null=True, related_name="related_institutionA",
        on_delete=models.CASCADE)
    related_institutionB = models.ForeignKey(
        Institution, blank=True, null=True, related_name="related_institutionB",
        on_delete=models.CASCADE)
    objects = models.Manager()
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
            rel_type = self.relation_type.name
        elif self.related_institutionB == entity:
            rel_inst = self.related_institutionA
            rel_type = self.relation_type.name_reverse
        result = {
            'relation_pk': self.pk,
            'relation_type': rel_type,
            'related_institution': rel_inst,
            'start_date': self.start_date,
            'end_date': self.end_date}
        return result


@reversion.register(follow=['tempentityclass_ptr'])
class InstitutionPlace(TempEntityClass):
    """Describes a relation bewteen an Institution  and a Place

    :param int relation_type: Foreign Key to :class:`vocabularies.models.InstitutionPlaceRelation`
    :param int related_institution: Foreign Key to :class:`entities.models.Institution`
    :param int related_place: Foreign Key to :class:`entities.models.Place`
    """

    relation_type = models.ForeignKey(
        InstitutionPlaceRelation, blank=True, null=True,
        on_delete=models.SET_NULL)
    related_institution = models.ForeignKey(
        Institution, blank=True, null=True, on_delete=models.CASCADE)
    related_place = models.ForeignKey(
        Place, blank=True, null=True, on_delete=models.CASCADE)
    objects = models.Manager()
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
class InstitutionEvent(TempEntityClass):
    """Describes a relation bewteen an Institution and an Event

    :param int relation_type: Foreign Key to :class:`vocabularies.models.InstitutionEventRelation`
    :param int related_institution: Foreign Key to :class:`entities.models.Institution`
    :param int related_event: Foreign Key to :class:`entities.models.Event`
    """

    relation_type = models.ForeignKey(InstitutionEventRelation, blank=True,
                                      null=True, on_delete=models.SET_NULL)
    related_institution = models.ForeignKey(
        Institution, blank=True, null=True, on_delete=models.CASCADE)
    related_event = models.ForeignKey(
        Event, blank=True, null=True, on_delete=models.CASCADE)
    objects = models.Manager()
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
class InstitutionWork(TempEntityClass):
    """Describes a relation bewteen an Institution and a Work

    :param int relation_type: Foreign Key to :class:`vocabularies.models.InstitutionWorkRelation`
    :param int related_institution: Foreign Key to :class:`entities.models.Institution`
    :param int related_work: Foreign Key to :class:`entities.models.Work`
    """

    relation_type = models.ForeignKey(InstitutionWorkRelation, blank=True,
                                      null=True, on_delete=models.SET_NULL)
    related_institution = models.ForeignKey(
        Institution, blank=True, null=True, on_delete=models.CASCADE)
    related_work = models.ForeignKey(
        Work, blank=True, null=True, on_delete=models.CASCADE)
    objects = models.Manager()
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
class PlacePlace(TempEntityClass):
    """Describes a relation bewteen an Place  and a Place

    :param int relation_type: Foreign Key to :class:`vocabularies.models.PlacePlaceRelation`
    :param int related_placeA: Foreign Key to :class:`entities.models.Place`
    :param int related_placeB: Foreign Key to :class:`entities.models.Place`
    """

    relation_type = models.ForeignKey(PlacePlaceRelation, blank=True, null=True,
                                      on_delete=models.SET_NULL)
    related_placeA = models.ForeignKey(
        Place, blank=True, null=True, related_name="related_placeA",
        on_delete=models.CASCADE)
    related_placeB = models.ForeignKey(
        Place, blank=True, null=True, related_name="related_placeB",
        on_delete=models.CASCADE)
    objects = models.Manager()
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
            rel_type = self.relation_type.name
        elif self.related_placeB == entity:
            rel_place = self.related_placeA
            rel_type = self.relation_type.name_reverse
        result = {
            'relation_pk': self.pk,
            'relation_type': rel_type,
            'related_place': rel_place,
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
class PlaceEvent(TempEntityClass):
    """Describes a relation between an Place and an Event

    :param int relation_type: Foreign Key to :class:`vocabularies.models.PlaceEventRelation`
    :param int related_place: Foreign Key to :class:`entities.models.Place`
    :param int related_event: Foreign Key to :class:`entities.models.Event`
    """

    relation_type = models.ForeignKey(PlaceEventRelation, blank=True, null=True,
                                      on_delete=models.SET_NULL)
    related_place = models.ForeignKey(
        Place, blank=True, null=True, on_delete=models.CASCADE)
    related_event = models.ForeignKey(
        Event, blank=True, null=True, on_delete=models.CASCADE)
    objects = models.Manager()
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
class PlaceWork(TempEntityClass):
    """Describes a relation between an Place and a Work

    :param int relation_type: Foreign Key to :class:`vocabularies.models.PlaceWorkRelation`
    :param int related_place: Foreign Key to :class:`entities.models.Place`
    :param int related_Work: Foreign Key to :class:`entities.models.Work`
    """

    relation_type = models.ForeignKey(PlaceWorkRelation, blank=True, null=True,
                                      on_delete=models.SET_NULL)
    related_place = models.ForeignKey(
        Place, blank=True, null=True, on_delete=models.CASCADE)
    related_work = models.ForeignKey(
        Work, blank=True, null=True, on_delete=models.CASCADE)
    objects = models.Manager()
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
class EventEvent(TempEntityClass):
    """Describes a relation between an Event and an Event

    :param int relation_type: Foreign Key to :class:`vocabularies.models.EventEventRelation`
    :param int related_eventA: Foreign Key to :class:`entities.models.Event`
    :param int related_eventB: Foreign Key to :class:`entities.models.Event`
    """

    relation_type = models.ForeignKey(EventEventRelation, blank=True, null=True,
                                      on_delete=models.SET_NULL)
    related_eventA = models.ForeignKey(
        Event, blank=True, null=True, related_name="related_eventA",
        on_delete=models.CASCADE)
    related_eventB = models.ForeignKey(
        Event, blank=True, null=True, related_name="related_eventB",
        on_delete=models.CASCADE)
    objects = models.Manager()
    annotation_links = AnnotationRelationLinkManager()

    def __str__(self):
        return "{} ({}) {}".format(
            self.related_event, self.relation_type, self.related_event)


@reversion.register(follow=['tempentityclass_ptr'])
class EventWork(TempEntityClass):
    """Describes a relation between an Event and a Work

    :param int relation_type: Foreign Key to :class:`vocabularies.models.EventWorkRelation`
    :param int related_event: Foreign Key to :class:`entities.models.Event`
    :param int related_work: Foreign Key to :class:`entities.models.Work`
    """

    relation_type = models.ForeignKey(EventWorkRelation, blank=True, null=True,
                                      on_delete=models.SET_NULL)
    related_event = models.ForeignKey(
        Event, blank=True, null=True, on_delete=models.CASCADE)
    related_work = models.ForeignKey(
        Work, blank=True, null=True, on_delete=models.CASCADE)
    objects = models.Manager()
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
class WorkWork(TempEntityClass):
    """Describes a relation between an Work and a Work

    :param int relation_type: Foreign Key to :class:`vocabularies.models.WorkWorkRelation`
    :param int related_workA: Foreign Key to :class:`entities.models.Work`
    :param int related_workB: Foreign Key to :class:`entities.models.Work`
    """

    relation_type = models.ForeignKey(WorkWorkRelation, blank=True, null=True,
                                      on_delete=models.SET_NULL)
    related_workA = models.ForeignKey(
        Work, blank=True, null=True, related_name="related_workA",
        on_delete=models.CASCADE)
    related_workB = models.ForeignKey(
        Work, blank=True, null=True, related_name="related_workB",
        on_delete=models.CASCADE)
    objects = models.Manager()
    annotation_links = AnnotationRelationLinkManager()

    def get_table_dict(self, entity):
        """Dict for the tabels in the html view

        :param entity: Object of type :class:`entities.models.Place`; Used to determine which Place is the main antity
            and which one the related.
        :return:
        """
        if self.related_workA == entity:
            rel_work = self.related_workB
            rel_type = self.relation_type.name
        elif self.related_workB == entity:
            rel_work = self.related_workA
            rel_type = self.relation_type.name_reverse
        result = {
            'relation_pk': self.pk,
            'relation_type': rel_type,
            'related_work': rel_work,
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

    def __str__(self):
        return "{} ({}) {}".format(self.related_workA, self.relation_type, self.related_workB)
