import inspect
import re
import sys
import unicodedata
import yaml

from django.contrib.auth.models import User
from django.db import models
from django.utils.functional import cached_property
from reversion import revisions as reversion
from django.conf import settings


@reversion.register()
class VocabNames(models.Model):
    """List of Vocabulary names to allow the easy retrieval\
    of Vovcabulary names and classes from the VocabsBaseClass"""
    name = models.CharField(max_length=255)

    def get_vocab_label(self):
        return re.sub(r"([A-Z])", r" \1", self.name).strip()


@reversion.register()
class VocabsBaseClass(models.Model):
    """ An abstract base class for other classes which contain so called
    'controlled vocabulary' to describe subtypes of main temporalized
    entites"""
    choices_status = (
        ('rej', 'rejected'),
        ('ac', 'accepted'),
        ('can', 'candidate'),
        ('del', 'deleted')
    )
    name = models.CharField(max_length=255, verbose_name='Name')
    description = models.TextField(
        blank=True,
        help_text="Brief description of the used term.")
    parent_class = models.ForeignKey(
        'self', blank=True, null=True,
        on_delete=models.CASCADE
    )
    status = models.CharField(max_length=4, choices=choices_status, default='can')
    userAdded = models.ForeignKey(
        User, blank=True, null=True,
        on_delete=models.SET_NULL
    )
    vocab_name = models.ForeignKey(
        VocabNames, blank=True, null=True,
        on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        d, created = VocabNames.objects.get_or_create(name=type(self).__name__)
        self.vocab_name = d
        if self.name != unicodedata.normalize('NFC', self.name):  # secure correct unicode encoding
            self.name = unicodedata.normalize('NFC', self.name)
        super(VocabsBaseClass, self).save(*args, **kwargs)
        return self

    @cached_property
    def label(self):
        d = self
        res = self.name
        while d.parent_class:
            res = d.parent_class.name + ' >> ' + res
            d = d.parent_class
        return res


@reversion.register(follow=['vocabsbaseclass_ptr'])
class RelationBaseClass(VocabsBaseClass):
    """ An abstract base class for other classes which contain so called
    'controlled vocabulary' to describe the relations between main temporalized
    entities ('db_')"""

    name_reverse = models.CharField(
        max_length=255,
        verbose_name='Name reverse',
        help_text='Inverse relation like: "is sub-class of" vs. "is super-class of".',
        blank=True)

    def __str__(self):
        return self.name

    @cached_property
    def label_reverse(self):
        d = self
        if len(self.name_reverse) < 1:
            res = '(' + self.name + ')'
        else:
            res = self.name_reverse
        while d.parent_class:
            try:
                t = RelationBaseClass.objects.get(pk=d.parent_class.pk).name_reverse
                if len(t) < 1:
                    t = '(' + d.parent_class.name + ')'
            except Exception as e:
                t = '(' + d.parent_class.name + ')'
            res = t + ' >> ' + res
            d = d.parent_class
        return res

    def save(self, *args, **kwargs):
        if self.name_reverse != unicodedata.normalize('NFC', self.name_reverse):
            self.name_reverse = unicodedata.normalize('NFC', self.name_reverse)

        if self.name_reverse == "" or self.name_reverse == None:
            self.name_reverse = self.name + " [REVERSE]"

        super(RelationBaseClass, self).save(*args, **kwargs)
        return self


@reversion.register()
class VocabsUri(models.Model):
    """Class to store URIs for imported types. URI class from metainfo is not
    used in order to keep the vocabularies module/app seperated from the rest of the application.
    """
    uri = models.URLField()
    domain = models.CharField(max_length=255, blank=True)
    rdf_link = models.URLField(blank=True)
    vocab = models.ForeignKey(VocabsBaseClass, blank=True, null=True,
                              on_delete=models.CASCADE)
    # loaded: set to True when RDF was loaded and parsed into the data model
    loaded = models.BooleanField(default=False)
    # loaded_time: Timestamp when file was loaded and parsed
    loaded_time = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.uri

#######################################################################
#
#   entity types
#
#######################################################################


@reversion.register(follow=['vocabsbaseclass_ptr'])
class WorkType(VocabsBaseClass):
    """Holds controlled vocabularies about work-types"""
    pass


@reversion.register(follow=['vocabsbaseclass_ptr'])
class Title(VocabsBaseClass):
    """A person´s (academic) title"""
    abbreviation = models.CharField(max_length=10, blank=True)


@reversion.register(follow=['vocabsbaseclass_ptr'])
class ProfessionType(VocabsBaseClass):
    """Holds controlled vocabularies about profession-types"""
    pass


@reversion.register(follow=['vocabsbaseclass_ptr'])
class PlaceType(VocabsBaseClass):
    """Holds controlled vocabularies about place-types"""
    pass


@reversion.register(follow=['vocabsbaseclass_ptr'])
class InstitutionType(VocabsBaseClass):
    """Holds controlled vocabularies about institution-types"""
    pass


@reversion.register(follow=['vocabsbaseclass_ptr'])
class EventType(VocabsBaseClass):
    """Holds controlled vocabularies about event-types"""
    pass


@reversion.register(follow=['vocabsbaseclass_ptr'])
class LabelType(VocabsBaseClass):
    """Holds controlled vocabularies about label-types"""
    pass


@reversion.register(follow=['vocabsbaseclass_ptr'])
class CollectionType(VocabsBaseClass):
    """e.g. reseachCollection, importCollection """
    pass

@reversion.register(follow=['vocabsbaseclass_ptr'])
class TextType(VocabsBaseClass):
    """used to store the Text types for the forms"""
    entity = models.CharField(max_length=255)
    collections = models.ManyToManyField('apis_metainfo.Collection', blank=True)
    lang = models.CharField(
        max_length=3, blank=True, null=True,
        help_text="The ISO 639-3 (or 2) code for the label's language.",
        verbose_name='ISO Code', default='deu')



#######################################################################
#
#   relation types
#
#######################################################################



class AbstractRelationType(RelationBaseClass):
    """
    Abstract super class which encapsulates common logic between the different relationtypes and provides various methods
    relating to either all or a specific relationtypes.
    """

    class Meta:
        abstract = True

    _all_relationtype_classes = None
    _all_relationtype_names = None
    _related_entity_field_names = None


    # Methods dealing with all relationtypes
    ####################################################################################################################
    
    @classmethod
    def get_all_relationtype_classes(cls):
        """
        :return: list of all python classes of the relationtypes defined within this models' module  
        """

        if cls._all_relationtype_classes == None:

            relationtype_classes = []
            relationtype_names = []

            for relationtype_name, relationtype_class in inspect.getmembers(
                    sys.modules[__name__], inspect.isclass):

                if relationtype_class.__module__ == "apis_core.apis_vocabularies.models" and \
                        relationtype_name != "ent_class" and \
                        relationtype_name.endswith("Relation"):

                    relationtype_classes.append(relationtype_class)
                    relationtype_names.append(relationtype_name.lower())

            cls._all_relationtype_classes = relationtype_classes
            cls._all_relationtype_names = relationtype_names

        return cls._all_relationtype_classes


    @classmethod
    def get_relationtype_class_of_name(cls, relationtype_name):
        """
        :param entity_name: str : The name of an relationtype
        :return: The model class of the relationtype respective to the given name
        """

        for relationtype_class in cls.get_all_relationtype_classes():
            if relationtype_class.__name__.lower() == relationtype_name.lower():
                return relationtype_class

        raise Exception("Could not find relationtype class of name:", relationtype_name)


    @classmethod
    def get_all_relationtype_names(cls):
        """
        :return: list of all class names in lower case of the relationtypes defined within this models' module
        """

        if cls._all_relationtype_names == None:

            cls.get_all_relationtype_classes()

        return cls._all_relationtype_names


    # Methods dealing with related entities
    ####################################################################################################################
    
    @classmethod
    def get_related_entity_field_names(cls):
        """
        :return: a list of names of all ManyToMany field names relating to entities from the respective relationtype class

        E.g. for PersonPersonRelation.get_related_entity_field_names() or personpersonrelation_instance.get_related_entity_field_names() ->
        ['personB_set', 'personA_set']

        Note: this method depends on the 'generate_relation_fields' method in apis_entities.models which wires the ManyToMany Fields into the
        entities and respective relationtypes. It is nevertheless defined here within AbstractRelationType for documentational purpose.
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

        Note: this method depends on the 'generate_relation_fields' method in apis_entities.models which wires the ManyToMany Fields into the
        entities and respective relationtypes. It is nevertheless defined here within AbstractRelationType for documentational purpose.
        """

        if cls._related_entity_field_names == None:
            cls._related_entity_field_names = []

        cls._related_entity_field_names.append(entity_field_name)


#######################################################################
# Person-Relation-Types
#######################################################################


@reversion.register(follow=['relationbaseclass_ptr'])
class PersonPersonRelation(AbstractRelationType):
    """Holds controlled vocabularies relation types of Persons and Persons"""
    pass


@reversion.register(follow=['relationbaseclass_ptr'])
class PersonPlaceRelation(AbstractRelationType):
    """Holds controlled vocabularies relation types of Persons and Places"""
    pass


@reversion.register(follow=['relationbaseclass_ptr'])
class PersonInstitutionRelation(AbstractRelationType):
    """Holds controlled vocabularies relation types of Persons and Persons"""
    pass


@reversion.register(follow=['relationbaseclass_ptr'])
class PersonEventRelation(AbstractRelationType):
    """Holds controlled vocabularies relation types of Persons and Events"""
    pass


@reversion.register(follow=['relationbaseclass_ptr'])
class PersonWorkRelation(AbstractRelationType):
    """Holds controlled vocabularies relation types of Persons and Works"""
    pass


#######################################################################
# Institution-Relation-Types
#######################################################################


@reversion.register(follow=['relationbaseclass_ptr'])
class InstitutionEventRelation(AbstractRelationType):
    """Holds controlled vocabularies relation types of Institutions and Events."""
    pass


@reversion.register(follow=['relationbaseclass_ptr'])
class InstitutionPlaceRelation(AbstractRelationType):
    """Holds controlled vocabularies relation types of Institutions and Places."""
    pass


@reversion.register(follow=['relationbaseclass_ptr'])
class InstitutionInstitutionRelation(AbstractRelationType):
    """Holds controlled vocabularies relation types of Institutions and Institutions."""
    pass


@reversion.register(follow=['relationbaseclass_ptr'])
class InstitutionWorkRelation(AbstractRelationType):
    """Holds controlled vocabularies relation types of Institutions and Works."""
    pass

#######################################################################
# Place-Relation-Types
#######################################################################


@reversion.register(follow=['relationbaseclass_ptr'])
class PlacePlaceRelation(AbstractRelationType):
    """Holds controlled vocabularies relation types of Places and Places"""
    pass


@reversion.register(follow=['relationbaseclass_ptr'])
class PlaceEventRelation(AbstractRelationType):
    """Holds controlled vocabularies relation types of Places and Events"""
    pass


@reversion.register(follow=['relationbaseclass_ptr'])
class PlaceWorkRelation(AbstractRelationType):
    """Holds controlled vocabularies relation types of Places and Works"""
    pass


#######################################################################
# Event-Relation-Types
#######################################################################


@reversion.register(follow=['relationbaseclass_ptr'])
class EventEventRelation(AbstractRelationType):
    """Holds controlled vocabularies relation types of Events and Events"""
    pass


@reversion.register(follow=['relationbaseclass_ptr'])
class EventWorkRelation(AbstractRelationType):
    """Holds controlled vocabularies relation types of Events and Works"""
    pass


#######################################################################
# Work-Relation-Types
#######################################################################


@reversion.register(follow=['relationbaseclass_ptr'])
class WorkWorkRelation(AbstractRelationType):
    """Holds controlled vocabularies relation types of Works and Works"""
    pass


a_ents = getattr(settings, 'APIS_ADDITIONAL_ENTITIES', False)

if a_ents:
    with open(a_ents, 'r') as ents_file:
        ents = yaml.load(ents_file, Loader=yaml.CLoader)
        print(ents)
        for ent in ents['entities']:
            for voc in ent.get('vocabs', []):
                attributes = {"__module__": __name__}
                ent_class = type(voc, (VocabsBaseClass,), attributes)
                globals()[ent['name']] = ent_class
            rels = ent.get("relations", [])
            base_ents = ['Person', 'Institution', 'Place', 'Work', 'Event']
            if isinstance(rels, str):
                if rels == 'all':
                    rels = base_ents + [x['name'].title() for x in ents['entities']]
            else:
                rels = base_ents + rels
            for r2 in rels:
                attributes = {"__module__":__name__}
                if r2 in base_ents:
                    rel_class_name = f"{r2.title()}{ent['name'].title()}"
                else:
                    rel_class_name = f"{ent['name'].title()}{r2.title()}"
                attributes = {"__module__": __name__}
                if f"{rel_class_name}Relation" not in globals().keys():
                    ent_class = type(f"{rel_class_name}Relation", (AbstractRelationType,), attributes)
                    globals()[f"{rel_class_name}Relation"] = ent_class

