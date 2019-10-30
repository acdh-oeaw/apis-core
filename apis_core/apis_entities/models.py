import re
import unicodedata
import sys
import inspect
# from reversion import revisions as reversion
import reversion
from apis_core.apis_labels.models import Label
from apis_core.apis_metainfo.models import Collection, TempEntityClass, Text, Uri
from apis_core.apis_vocabularies.models import (
    EventType,
    InstitutionType,
    PlaceType,
    Title,
    PassageLanguage,
    PassageType,
    PassageTopics
)
from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.urls import reverse
from guardian.shortcuts import assign_perm, remove_perm

BASE_URI = getattr(settings, "APIS_BASE_URI", "http://apis.info/")


class GenericEntity(TempEntityClass):
    """
    Abstract super class which encapsulates common logic between the different entity kinds and provides various methods
    relating to either all or a specific entity kind.

    Most of the class methods are designed to be used in the sublcass as they are considering contexts which depend on
    the subclass entity type. So they are to be understood in that dynamic context.
    """

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.__class__.create_relation_methods_from_manytomany_fields()

    # TODO __sresch__ : consider moving this block of logic for creation of related_entity_instances functions to generate_relation_fields
    @classmethod
    def create_relation_methods_from_manytomany_fields(cls):
        """
        Creates methods on an entity class with which other related entities can be called without the need to consider
        potential self-references (the A and B sides therein).

        The resulting methods follow the syntax:
        <entity>.get_related_<entity>_instances()

        e.g. for Person:
        person.get_related_work_instances()
        or
        person.get_related_person_instances()

        Note that with these methods it is not necessary to differentiate between A and B entities when self-relations exist.

        The result of any such method call is the queryset of the related entities.
        (And not a ManyToManyManager as is the case when calling <entity>.<entity>_set where in the case of self-relation
        it must be differentiated between A and B entities, e.g. person.personA_set )

        It was not possible to my understanding to change managers in such a way that two (the A and the B) could be combined
        into one manager. Hence these additional shortcut methods.

        :return: None
        """

        def create_function_from_manytomany_field_to_other_entity(entity_manytomany_field):
            """
            creates the individual method from a ManyToMany field by calling the manager's objects.all()

            This method creation has to be done here in a separate method, so that it can be called once before assignment
            as otherwise the variable 'entity_name' in the loop below changes with each iteration and with that also the
            method references (due to python's "late binding").
            A method call in between thus forces the content of 'entity_name' to be assigned for good to the
            respective class ( = forced early binding).
            For more details on this: https://stackoverflow.com/questions/3431676/creating-functions-in-a-loop

            :param entity_manytomany_field: the ManyToManyManager to another model
            :return: method which will call the managers's objects.all() method
            """
            return lambda self: getattr(self, entity_manytomany_field).all().distinct()

        def create_function_from_manytomany_field_to_self_entity(entityA_manytomany_field, entityB_manytomany_field):
            """
            Same method as above, but with two managers instead of one for the case of self-relations.

            Both managers' objects.all() methods are called and their queryset results are unionised for the
            shortcut method of an entity to its own related entities.

            :param entityA_manytomany_field: ManyToManyManager to entity A in a self-relation
            :param entityB_manytomany_field: ManyToManyManager to entity A in a self-relation
            :return: method to call both and return the distinct union of them
            """
            return lambda self: \
                (
                    getattr(self, entityA_manytomany_field).all().union(
                        getattr(self, entityB_manytomany_field).all())
                ).distinct()

        for entity_name in cls.get_all_entity_names():
            # Iterate over each entity defined within this models' module

            related_entity_function_name = "get_related_" + entity_name + "_instances"

            if not hasattr(cls, related_entity_function_name):

                if cls.__name__.lower() == entity_name:
                    # If the related entity is the same as this current one, then set the names of the related functions
                    # to A and B and also combine them into one function where both A and B are returned.

                    related_entityA_function_name = "get_related_" + entity_name + "A_instances"
                    related_entityB_function_name = "get_related_" + entity_name + "B_instances"
                    entityA_manytomany_field = entity_name + "A_set"
                    entityB_manytomany_field = entity_name + "B_set"

                    setattr(
                        cls,
                        related_entityA_function_name,
                        create_function_from_manytomany_field_to_other_entity(entityA_manytomany_field)
                    )

                    setattr(
                        cls,
                        related_entityB_function_name,
                        create_function_from_manytomany_field_to_other_entity(entityB_manytomany_field)
                    )

                    setattr(
                        cls,
                        related_entity_function_name,
                        create_function_from_manytomany_field_to_self_entity(entityA_manytomany_field,
                                                                             entityB_manytomany_field)
                    )

                else:
                    # If the related entity is a different one, then just build on the usual names

                    entity_manytomany_field = entity_name + "_set"

                    setattr(
                        cls,
                        related_entity_function_name,
                        create_function_from_manytomany_field_to_other_entity(entity_manytomany_field)
                    )

    # private class variables used for saving both class dependend and class independent information
    # for more convenient retrieval later on.
    # Initially defined as empty lists, they will be properly instantiated on their first call

    _all_entity_classes = None
    _all_entity_names = None
    _related_relation_classes = None
    _related_relation_names = None
    _related_relationtype_classes = None
    _related_relationtype_names = None
    _related_entity_field_names = None
    _related_relationtype_field_names = None

    # Methods dealing with all entities
    ####################################################################################################################

    @classmethod
    def get_all_entity_classes(cls):
        """
        :return: list of all python classes of the entities defined within this models' module
        """

        if cls._all_entity_classes == None:

            entity_classes = []
            entity_names = []

            for entity_name, entity_class in inspect.getmembers(sys.modules[__name__], inspect.isclass):

                if entity_class.__module__ == "apis_core.apis_entities.models" and \
                        entity_name != "GenericEntity":
                    entity_classes.append(entity_class)
                    entity_names.append(entity_name.lower())

            cls._all_entity_classes = entity_classes
            cls._all_entity_names = entity_names

        return cls._all_entity_classes

    @classmethod
    def get_all_entity_names(cls):
        """
        :return: list of all class names in lower case of the entities defined within this models' module
        """

        if cls._all_entity_names == None:
            cls.get_all_entity_classes()

        return cls._all_entity_names

    # Methods dealing with related entities
    ####################################################################################################################

    @classmethod
    def get_related_entity_field_names(cls):
        """
        :return: a list of names of all ManyToMany field names relating to entities from the respective entity class

        E.g. for Person.get_related_entity_field_names() or person_instance.get_related_entity_field_names() ->
        ['event_set', 'institution_set', 'personB_set', 'personA_set', 'place_set', 'work_set']

        Note: this method depends on the 'generate_relation_fields' method which wires the ManyToMany Fields into the
        entities and respective relationtypes. It is nevertheless defined here within GenericEntity for documentational purpose.
        """

        if cls._related_entity_field_names == None:
            raise Exception("_related_entity_field_names was not initialized yet.")
        else:
            return cls._related_entity_field_names

    @classmethod
    def add_related_entity_field_name(cls, entity_field_name):
        """
        :param entity_field_name: the name of one of several ManyToMany fields created automatically
        :return: None

        Note: this method depends on the 'generate_relation_fields' method which wires the ManyToMany Fields into the
        entities and respective relationtypes. It is nevertheless defined here within GenericEntity for documentational purpose.
        """

        if cls._related_entity_field_names == None:
            cls._related_entity_field_names = []

        cls._related_entity_field_names.append(entity_field_name)

    def get_related_entity_instances(self):
        """
        :return: list of queryset of all entity instances which are somehow related to the calling entity instance
        """

        queryset_list = []

        for entity_name in self.get_all_entity_names():

            queryset = getattr(self, "get_related_" + entity_name + "_instances")()
            if len(queryset) > 0:
                queryset_list.append(queryset)

        return queryset_list

    # Methods dealing with related relations
    ####################################################################################################################

    @classmethod
    def get_related_relation_classes(cls):
        """
        :return: list of python classes of the relations which are related to the respective entity class

        E.g. for Place.get_related_relation_classes() or place_instance.get_related_relation_classes() ->
        [ InstitutionPlace, PersonPlace, PlaceEvent, PlacePlace, PlaceWork ]
        """

        if cls._related_relation_classes == None:

            relation_classes = []
            relation_names = []

            # TODO __sresch__ : check for best practice on local imports vs circularity problems.
            # These imports are done locally to avoid circular import problems which arise if they are done globally in this module
            from apis_core.apis_relations.models import GenericRelation

            for relation_class in GenericRelation.get_all_relation_classes():

                relation_name = relation_class.__name__.lower()

                if cls.__name__.lower() in relation_name:
                    relation_classes.append(relation_class)
                    relation_names.append(relation_name)

            cls._related_relation_classes = relation_classes
            cls._related_relation_names = relation_names

        return cls._related_relation_classes

    @classmethod
    def get_related_relation_names(cls):
        """
        :return: list of class names in lower case of the relations which are related to the respective entity class

        E.g. for Place.get_related_relation_names() or place_instance.get_related_relation_names() ->
        ['institutionplace', 'personplace', 'placeevent', 'placeplace', 'placework']
        """

        if cls._related_relation_names == None:
            cls.get_related_relation_classes()

        return cls._related_relation_names

    def get_related_relation_instances(self):
        """
        :return: list of queryset of all relation instances which are somehow related to the calling entity instance
        """

        queryset_list = []
        self_entity_name = self.__class__.__name__.lower()

        for relation_class in self.get_related_relation_classes():

            queryset = None

            count_occurence = relation_class.__name__.lower().count(self_entity_name)

            # TODO __sresch__ : Try to change it to a call from entity class itself (e.g. Work.eventwork_set.all() )
            # for now search in the relation model, because somehow somewhere when the entity models
            # are symmetrical, then the foreign key field in the entity model is called for example relate_workA.all()
            # find where this is done, and change it

            if count_occurence == 1:

                queryset = relation_class.objects.filter(**{'related_' + self_entity_name.lower(): self})

            elif count_occurence == 2:

                querysetA = relation_class.objects.filter(**{'related_' + self_entity_name.lower() + 'A': self})
                querysetB = relation_class.objects.filter(**{'related_' + self_entity_name.lower() + 'B': self})
                queryset = querysetA.union(querysetB).distinct()

            if queryset and len(queryset) > 0:
                queryset_list.append(queryset)

        return queryset_list

    # Methods dealing with related relationtypes
    ####################################################################################################################

    @classmethod
    def get_related_relationtype_classes(cls):
        """
        :return: list of python classes of the relation types which are related to the respective entity class

        E.g. for Place.get_related_relation_classes() or place_instance.get_related_relation_classes() ->
        [ InstitutionPlaceRelation, PersonPlaceRelation, PlaceEventRelation, PlacePlaceRelation, PlaceWorkRelation ]
        """

        if cls._related_relationtype_classes == None:

            relationtype_classes = []
            relationtype_names = []

            # TODO __sresch__ : check for best practice on local imports vs circularity problems.
            # These imports are done locally to avoid circular import problems which arise if they are done globally in this module
            from apis_core.apis_vocabularies.models import GenericRelationType

            for relationtype_class in GenericRelationType.get_all_relationtype_classes():

                relationtype_name = relationtype_class.__name__.lower()

                if cls.__name__.lower() in relationtype_name:
                    relationtype_classes.append(relationtype_class)
                    relationtype_names.append(relationtype_name)

            cls._related_relationtype_classes = relationtype_classes
            cls._related_relationtype_names = relationtype_names

        return cls._related_relationtype_classes

    @classmethod
    def get_related_relationtype_names(cls):
        """
        :return: list of class names in lower case of the relation types which are related to the respective entity class

        E.g. for Place.get_related_relation_classes() or place_instance.get_related_relation_classes() ->
        [ 'institutionplacerelation', 'personplacerelation', 'placeeventrelation', 'placeplacerelation', 'placeworkrelation' ]
        """

        if cls._related_relationtype_names == None:
            cls.get_related_relationtype_classes()

        return cls._related_relationtype_names

    @classmethod
    def get_related_relationtype_field_names(cls):
        """
        :return: a list of names of all ManyToMany field names relating to relationtypes from the respective entity class

        E.g. for PersonPerson.get_related_relationtype_field_names() or person_instance.get_related_relationtype_field_names() ->
        ['event_relationtype_set', 'institution_relationtype_set', 'personB_relationtype_set', 'personA_relationtype_set', 'place_relationtype_set', 'work_relationtype_set']

        Note: this method depends on the 'generate_relation_fields' method which wires the ManyToMany Fields into the
        entities and respective relationtypes. It is nevertheless defined here within GenericEntity for documentational purpose.
        """

        if cls._related_relationtype_field_names == None:
            raise Exception("_related_relationtype_field_names was not initialized yet.")
        else:
            return cls._related_relationtype_field_names

    @classmethod
    def add_related_relationtype_field_name(cls, relationtype_field_name):
        """
        :param entity_field_name: the name of one of several ManyToMany fields created automatically
        :return: None

        Note: this method depends on the 'generate_relation_fields' method which wires the ManyToMany Fields into the
        entities and respective relationtypes. It is nevertheless defined here within GenericEntity for documentational purpose.
        """

        if cls._related_relationtype_field_names == None:
            cls._related_relationtype_field_names = []

        cls._related_relationtype_field_names.append(relationtype_field_name)

    def get_related_relationtype_instances(self):
        """
        :return: list of queryset of all relationtype instances which are somehow related to the calling entity instance
        """

        queryset_list = []

        for entity_name in self.get_all_entity_names():
            queryset = None

            if entity_name != self.__class__.__name__.lower():

                queryset = getattr(self, entity_name + "_relationtype_set").all().distinct()

            else:

                querysetA = getattr(self, entity_name + "A_relationtype_set").all().distinct()
                querysetB = getattr(self, entity_name + "B_relationtype_set").all().distinct()
                queryset = querysetA.union(querysetB)

            if queryset and len(queryset) > 0:
                queryset_list.append(queryset)

        return queryset_list


@reversion.register(follow=["tempentityclass_ptr"])
class Person(GenericEntity):
    """ A temporalized entity to model a human beeing."""

    GENDER_CHOICES = (("female", "female"), ("male", "male"))
    first_name = models.CharField(
        max_length=255,
        help_text="The persons´s forename. In case of more then one name...",
        blank=True,
        null=True,
    )
    title = models.ManyToManyField(Title, blank=True)
    gender = models.CharField(max_length=15, choices=GENDER_CHOICES, blank=True)

    def __str__(self):
        if self.first_name != "" and self.name != "":
            return "{}, {}".format(self.name, self.first_name)
        elif self.first_name != "" and self.name == "":
            return "{}, {}".format("no surename provided", self.first_name)
        elif self.first_name == "" and self.name != "":
            return self.name
        elif self.first_name == "" and self.name == "":
            return "no name provided"

    def get_or_create_uri(uri):
        try:
            if re.match(r"^[0-9]*$", uri):
                p = Person.objects.get(pk=uri)
            else:
                p = Person.objects.get(uri__uri=uri)
            return p
        except:
            return False

    def save(self, *args, **kwargs):
        if self.first_name:
            # secure correct unicode encoding
            if self.first_name != unicodedata.normalize("NFC", self.first_name):
                self.first_name = unicodedata.normalize("NFC", self.first_name)
        super(Person, self).save(*args, **kwargs)
        return self


@reversion.register(follow=["tempentityclass_ptr"])
class Place(GenericEntity):
    """ A temporalized entity to model a place"""

    kind = models.ForeignKey(
        PlaceType, blank=True, null=True, on_delete=models.SET_NULL
    )
    lat = models.FloatField(blank=True, null=True, verbose_name="latitude")
    lng = models.FloatField(blank=True, null=True, verbose_name="longitude")
    name_english = models.CharField(max_length=1024, blank=True, null=True)

    def __str__(self):
        if self.name != "":
            return self.name
        else:
            return "no name provided"

    def get_or_create_uri(uri):
        try:
            if re.match(r"^[0-9]*$", uri):
                p = Place.objects.get(pk=uri)
            else:
                p = Place.objects.get(uri__uri=uri)
            return p
        except:
            return False


@reversion.register(follow=["tempentityclass_ptr"])
class Institution(GenericEntity):
    kind = models.ForeignKey(
        InstitutionType, blank=True, null=True, on_delete=models.SET_NULL
    )
    name_english = models.CharField(max_length=1024, blank=True, null=True)

    def __str__(self):
        if self.name != "":
            return self.name
        else:
            return "no name provided"

    def get_or_create_uri(uri):
        try:
            if re.match(r"^[0-9]*$", uri):
                p = Institution.objects.get(pk=uri)
            else:
                p = Institution.objects.get(uri__uri=uri)
                print(p)
            return p
        except:
            print("returned false")
            return False


@reversion.register(follow=["tempentityclass_ptr"])
class Event(GenericEntity):
    kind = models.ForeignKey(
        EventType, blank=True, null=True, on_delete=models.SET_NULL
    )
    name_english = models.CharField(max_length=1024, blank=True, null=True)

    def __str__(self):
        if self.name != "":
            return self.name
        else:
            return "no name provided"

    def get_or_create_uri(uri):
        try:
            if re.match(r"^[0-9]*$", uri):
                p = Event.objects.get(pk=uri)
            else:
                p = Event.objects.get(uri__uri=uri)
            return p
        except:
            return False


@reversion.register(follow=["tempentityclass_ptr"])
class Passage(GenericEntity):

    # TODO __sresch__ : consider renaming ManyToManyFields like topics to passagetopic_set to be consistent with reverse direction
    topics = models.ManyToManyField(PassageTopics, blank=True, null=True)
    migne_number = models.CharField(max_length=1024, blank=True, null=True)
    kind = models.ForeignKey(PassageType, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        if self.name != "":
            return self.name
        else:
            return "no name provided"

    def get_or_create_uri(uri):
        try:
            if re.match(r"^[0-9]*$", uri):
                p = Passage.objects.get(pk=uri)
            else:
                p = Passage.objects.get(uri__uri=uri)
            return p
        except:
            return False


@reversion.register(follow=["tempentityclass_ptr"])
class Publication(GenericEntity):
    kind = models.ForeignKey(PassageType, blank=True, null=True, on_delete=models.SET_NULL)
    language = models.ForeignKey(PassageLanguage, blank=True, null=True, on_delete=models.SET_NULL)
    clavis_number = models.CharField(max_length=1024, blank=True, null=True)
    migne_number = models.CharField(max_length=1024, blank=True, null=True)
    publication_description = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.name != "":
            return self.name
        else:
            return "no name provided"

    def get_or_create_uri(uri):
        try:
            if re.match(r"^[0-9]*$", uri):
                p = Publication.objects.get(pk=uri)
            else:
                p = Publication.objects.get(uri__uri=uri)
            return p
        except:
            return False







@receiver(post_save, sender=Event, dispatch_uid="create_default_uri")
@receiver(post_save, sender=Passage, dispatch_uid="create_default_uri")
@receiver(post_save, sender=Institution, dispatch_uid="create_default_uri")
@receiver(post_save, sender=Person, dispatch_uid="create_default_uri")
@receiver(post_save, sender=Place, dispatch_uid="create_default_uri")
@receiver(post_save, sender=Publication, dispatch_uid="create_default_uri")
def create_default_uri(sender, instance, **kwargs):
    uri = Uri.objects.filter(entity=instance)
    if uri.count() == 0:
        uri_c = "http://{}{}".format(
            BASE_URI,
            reverse("apis_core:apis_api2:GetEntityGeneric", kwargs={"pk": instance.pk}),
        )
        uri2 = Uri(uri=uri_c, domain="apis default", entity=instance)
        uri2.save()


@receiver(
    m2m_changed,
    sender=Event.collection.through,
    dispatch_uid="create_object_permissions",
)
@receiver(
    m2m_changed,
    sender=Passage.collection.through,
    dispatch_uid="create_object_permissions",
)
@receiver(
    m2m_changed,
    sender=Institution.collection.through,
    dispatch_uid="create_object_permissions",
)
@receiver(
    m2m_changed,
    sender=Person.collection.through,
    dispatch_uid="create_object_permissions",
)
@receiver(
    m2m_changed,
    sender=Place.collection.through,
    dispatch_uid="create_object_permissions",
)
@receiver(
    m2m_changed,
    sender=Publication.collection.through,
    dispatch_uid="create_object_permissions",
)
def create_object_permissions(sender, instance, **kwargs):
    if kwargs["action"] == "pre_add":
        perms = []
        for j in kwargs["model"].objects.filter(pk__in=kwargs["pk_set"]):
            perms.extend(j.groups_allowed.all())
        for x in perms:
            assign_perm("change_" + instance.__class__.__name__.lower(), x, instance)
            assign_perm("delete_" + instance.__class__.__name__.lower(), x, instance)
    elif kwargs["action"] == "post_remove":
        perms = []
        perms_keep = []
        for j in kwargs["model"].objects.filter(pk__in=kwargs["pk_set"]):
            perms.extend(j.groups_allowed.all())
        for u in instance.collection.all():
            perms_keep.extend(u.groups_allowed.all())
        rm_perms = set(perms) - set(perms_keep)
        for x in rm_perms:
            remove_perm("change_" + instance.__class__.__name__.lower(), x, instance)
            remove_perm("delete_" + instance.__class__.__name__.lower(), x, instance)


@receiver(
    m2m_changed,
    sender=Collection.groups_allowed.through,
    dispatch_uid="add_usergroup_collection",
)
def add_usergroup_collection(sender, instance, **kwargs):
    if kwargs["action"] == "pre_add":
        for x in kwargs["model"].objects.filter(pk__in=kwargs["pk_set"]):
            for z in ["change", "delete"]:
                for y in [Person, Institution, Place, Event, Passage, Publication]:
                    assign_perm(
                        z + "_" + y.__name__.lower(),
                        x,
                        y.objects.filter(collection=instance),
                    )


if "registration" in getattr(settings, "INSTALLED_APPS", []):
    from registration.backends.simple.views import RegistrationView
    from registration.signals import user_registered

    @receiver(
        user_registered,
        sender=RegistrationView,
        dispatch_uid="add_registered_user_to_group",
    )
    def add_user_to_group(sender, user, request, **kwargs):
        user_group = getattr(settings, "APIS_AUTO_USERGROUP", None)
        if user_group is not None:
            user.groups.add(Group.objects.get(name=user_group))




def generate_relation_fields():
    """
    This function goes through every entity, relation, and relationytpe model and automatically wires them together
    by setting ManyToMany fields to each other through the relation model. This way the relations of a given entity
    to any other entity or relationtype can be queried much more directly and without the overhead of going through
    the relation model each time.

    The wiring is done by going reflectively through the python code and finding in the respective model modules the relevant classes.

    Django's ContentType interface could not be used since this relies on full class declaration before calling any models,
    however since we want to define attributes of models during their declaration, this was not possible and thus python's
    own code inspection had to be used.

    E.g. for Person these fields are auto-generated: event_set, institution_set, personB_set, personA_set, place_set, work_set
    And each of those fields are ManyToMany Managers where their django methods can be used upon, such as all() and filter()

    This function is called just below.

    :return: None
    """

    # TODO __sresch__ : check for best practice on local imports vs circularity problems.
    # These imports are done locally to avoid circular import problems which arise if they are done globally in this module
    from apis_core.apis_relations.models import GenericRelation
    from apis_core.apis_vocabularies.models import GenericRelationType


    # all the classes which are to be iterated over, also in the case of relation and relationtype they are sorted to ensure their proper alignment
    entity_classes = GenericEntity.get_all_entity_classes()
    relation_classes = GenericRelation.get_all_relation_classes()
    relation_classes.sort(key=lambda x : x.__name__)
    relationtype_classes = GenericRelationType.get_all_relationtype_classes()
    relationtype_classes.sort(key=lambda x : x.__name__)


    # Outer loop iterating over each of the entities, twice, in order to create their full power set
    for entity_class_A in entity_classes:
        for entity_class_B in entity_classes:

            entity_name_A = entity_class_A.__name__.lower()
            entity_name_B = entity_class_B.__name__.lower()

            # inner loop iterating over each of the relation_class and relationtype at the same time, which were sorted before
            # in order to align the relation_class and relationtype_class with each other.
            for relation_class, relationtype_class in zip(relation_classes, relationtype_classes):

                relation_name = relation_class.__name__.lower()
                relation_type_name = relationtype_class.__name__.lower()

                # Ensure that relation_class and relationtype_class are indeed talking about the same relation
                # If this error is thrown then it would indicate misaligment in the models themselves
                # which would be a critical violation of the models.
                if relation_name not in relation_type_name:
                    raise Exception("Mismatch between Relation and RelationType class found! Between:\n",
                            relation_class, "and", relationtype_class)

                # Check if current relation related to both entities
                # Note that this way two entites are checked twice, such as person - place and place - person
                # but however in the relation model only one of these two exists. Thus the right one is picked.
                if entity_name_A + entity_name_B == relation_name:

                    if entity_name_A != entity_name_B:

                        # Define all the names for the ManyToMany fields generated below
                        field_name_to_entity_A = entity_name_A + "_set"
                        field_name_to_entity_B = entity_name_B + "_set"
                        field_name_to_entity_B_relationtype = entity_name_B + "_relationtype_set"
                        field_name_to_entity_A_relationtype = entity_name_A + "_relationtype_set"

                        # Add those names already into the respective class's list of field names
                        entity_class_A.add_related_entity_field_name(field_name_to_entity_B)
                        entity_class_B.add_related_entity_field_name(field_name_to_entity_A)
                        entity_class_A.add_related_relationtype_field_name(field_name_to_entity_B_relationtype)
                        entity_class_B.add_related_relationtype_field_name(field_name_to_entity_A_relationtype)
                        relationtype_class.add_related_entity_field_name(field_name_to_entity_B)
                        relationtype_class.add_related_entity_field_name(field_name_to_entity_A)

                        # entity A to entity B, and B back to A
                        models.ManyToManyField(
                            to=entity_class_B,
                            through=relation_class,
                            related_name=field_name_to_entity_A,
                            blank=True,
                        ).contribute_to_class(entity_class_A, field_name_to_entity_B)

                        # entity A to RelationType via entity B, and RelationType back to A
                        models.ManyToManyField(
                            to=relationtype_class,
                            through=relation_class,
                            related_name=field_name_to_entity_A,
                            blank=True,
                        ).contribute_to_class(entity_class_A, field_name_to_entity_B_relationtype)

                        # entity B to RelationType via entity A, and RelationType back to B
                        models.ManyToManyField(
                            to=relationtype_class,
                            through=relation_class,
                            related_name=field_name_to_entity_B,
                            blank=True,
                        ).contribute_to_class(entity_class_B, field_name_to_entity_A_relationtype)


                    else:
                        # TODO __sresch__ : look further into if it's really not possible to combine the A and B manager into one

                        # Define all the names for the ManyToMany fields generated below
                        field_name_to_entity_A = entity_name_A + "A_set"
                        field_name_to_entity_B = entity_name_B + "B_set"
                        field_name_to_entity_B_relationtype = entity_name_B + "B_relationtype_set"
                        field_name_to_entity_A_relationtype = entity_name_A + "A_relationtype_set"

                        # Add those names already into the respective class's list of field names
                        entity_class_A.add_related_entity_field_name(field_name_to_entity_B)
                        entity_class_B.add_related_entity_field_name(field_name_to_entity_A)
                        entity_class_A.add_related_relationtype_field_name(field_name_to_entity_B_relationtype)
                        entity_class_B.add_related_relationtype_field_name(field_name_to_entity_A_relationtype)
                        relationtype_class.add_related_entity_field_name(field_name_to_entity_B)
                        relationtype_class.add_related_entity_field_name(field_name_to_entity_A)

                        # entity A to same entity B, and B back to A
                        models.ManyToManyField(
                            to=entity_class_B,
                            through=relation_class,
                            related_name=field_name_to_entity_A,
                            blank=True,
                            symmetrical=False,
                            through_fields=("related_" + entity_name_A + "A", "related_" + entity_name_B + "B")
                        ).contribute_to_class(entity_class_A, field_name_to_entity_B)

                        # entity A to RelationType via entity B, and RelationType back to A
                        models.ManyToManyField(
                            to=relationtype_class,
                            through=relation_class,
                            related_name=field_name_to_entity_A,
                            blank=True,
                            symmetrical=False,
                            through_fields=("related_" + entity_name_A + "A", "relation_type")
                        ).contribute_to_class(entity_class_A, field_name_to_entity_B_relationtype)

                        # entity B to RelationType via entity A, and RelationType back to B
                        models.ManyToManyField(
                            to=entity_class_B,
                            through=relation_class,
                            related_name=field_name_to_entity_A_relationtype,
                            blank=True,
                            symmetrical=False,
                            through_fields=("relation_type", "related_" + entity_name_B + "B")
                        ).contribute_to_class(relationtype_class, field_name_to_entity_B)

                    break


generate_relation_fields()