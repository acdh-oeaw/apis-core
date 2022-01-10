Data Model
==========

Our internal data model consists of entities, relations, vocabularies and some meta-classes (e.g. annotations,
revisions etc.)

.. _fig-data-model:

.. figure:: /img/data_model_apis.png
   :alt: Data model APIS

   Simplified data-model of the APIS webapp

Please note that in the data-model schema in order to make the figure not too complex some arrows have been removed.

Entities
--------

The entities build the core of the internal APIS data-model:

* :class:`entities.models.Person`: Natural persons
* :class:`entities.models.Place`: Any place on earth that can be defined by longitude and latitude. Mainly cities and countries.
* :class:`entities.models.Institution`: Any legal entity or legal entity similar entity. This includes obviously organisations, but also
  religions, or long lasting prizes.
* :class:`entities.models.Event`: Any event that took place in history and is too big to model as a relation. This does not include a birth
  of a person (like it would be modeled in event based data models) as the birth is split up between attributes (e.g.
  the date of birth) and relations to other entities (e.g. the mother). It includes though wars and battles as these
  would need a lot of entities to relate to each other.
* :class:`entities.models.Work`: Basically anything that human beings produce: letters and books, paintings, buildings and cars.


Relations
---------

Every entity in the APIS data model can be related to any other entity. Relations consist of:

* a start entity (e.g. a person for a PersonPlace relation)
* a target entity (e.g. a place for a PersonPlace relation)
* start and end dates of the relation
* a vocabulary entry to define the kind of relation
* reference- and notes fields. These are full-text fields to further define the relation.

There are


Vocabularies
------------

As we already mentioned we use SKOS_ like vocabularies to define entities and relations. These vocabulary entries
use following attributes:

* *name*: the name of the entry. We define relations always in the direction the class is named. Thus the *PersonPlace*
  relation needs a vocabulary entry describing the relation from the *Person* to the *Place*. E.g. "was educated in".
* *name_reverse*: Specifies the name to use for the reverse relation (*PlacePerson*). E.g. "was place of education of".
* *parent_class*: The parent of the entry. SKOS_ allows for hierarchical structures and we implement these hierarchies
  by setting the parent class.
* *description*: Can be used to further define the entry.


Annotations
-----------

The third important part of the data model are annotations. We store annotations as character offset with start and end
character (please see :class:`highlighter.models.Annotation` for details). Every :class:`highlighter.models.Annotation`
is associated with:

* :class:`django.contrib.auth.models.User`: The user that created the annotation. Please keep in mind that this is not
   changed when someone changes the associated relation or entity.
* an entity or relation (optional): anything within :ref:`entities-models` or :ref:`relations-models`.


.. _SKOS: https://en.wikipedia.org/wiki/Simple_Knowledge_Organization_System