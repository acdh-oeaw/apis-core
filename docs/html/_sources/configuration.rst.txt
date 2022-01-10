Configuration
=============

This section deals with the internal configuration of the APIS tool. For instructions on how to set it up please refer
to :doc:`installation`.
Most of the configuration goes into a Django settings file. We suggest that you create your own configuration file and 
- in case you use the Docker image - import everything from the base settingsfile found in ``/apis/apis-devops/apis/settings/base.py``: ``from .base import *``


REST_FRAMEWORK
--------------

APIS uses the `Django Restframework`_ for API provisioning. Restframework specific settings like the default page size can be set here.

.. code-block:: python

    REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = (
        "rest_framework.permissions.DjangoObjectPermissions",
    )

Use the above default to allow setting permissions on object level. Meaning that every user gets his permissions depending on his/her user group and the collections this group has permissions for.
Set ``"rest_framework.permissions.DjangoModelPermissions"`` for allowing every user with permissions on a model to change all model instances.
Set ``"rest_framework.permissions.IsAuthenticated"`` if every logged in user should have all permissions.

.. code-block:: python

    REST_FRAMEWORK["PAGE_SIZE"] = 50

Sets the default page size the APIS RestAPI should deliver.


APIS_BASE_URI
-------------

.. code-block:: python

    APIS_BASE_URI = "https://your-url-goes-here.com"

Sets the base URI your instance should use. This is important as APIS uses mainly URIs instead of IDs. These URIs are also used for the serialization.


APIS_MIN_CHAR
-------------

.. code-block:: python

    APIS_MIN_CHAR = 0

Sets the minimal characters needed to trigger the autocompletes.


APIS_COMPONENTS
---------------

.. code-block:: python

    APIS_COMPONENTS = []

This activates certain experimental components. This is not of interest for production use yet.


APIS_TEI
--------

.. code-block:: python

    APIS_TEI_TEXTS = ["xml/tei transcription"]
    APIS_CETEICEAN_CSS = "https://teic.github.io/CETEIcean/css/CETEIcean.css"
    APIS_CETEICEAN_JS = "https://teic.github.io/CETEIcean/js/CETEI.js"

APIS includes a experimental feature to save and render TEI files. These settings are used to define the css and js files used to render TEIs.


APIS_NEXT_PREV
--------------

.. code-block:: python
    
    APIS_NEXT_PREV = True


APIS_ALTERNATE_NAMES
--------------------

.. code-block:: python

    APIS_ALTERNATE_NAMES = [
        "Taufname",
        "Ehename",
        "Name laut ÖBL XML",
        "alternative Namensform",
        "alternative name",
        "Künstlername",
        "Mädchenname",
        "Pseudonym",
        "weitere Namensform",
    ]

This setting contains a list of :class:`apis_vocabularies.models.LabelType` entries that should be deemed as alternative name. This is used to determine the label types that should be search in addition to the main name.


APIS_RELATIONS_FILTER_EXCLUDE
-----------------------------

.. code-block:: python
    
    APIS_RELATIONS_FILTER_EXCLUDE = [
        "*uri*",
        "*tempentityclass*",
        "user",
        "*__id",
        "*source*",
        "label",
        "*temp_entity*",
        "*collection*",
        "*published*",
        "*_set",
        "*_set__*",
        "_ptr",
        "baseclass",
        "*id",
        "*written*",
        "relation_type__*",
        "*__text*",
        "text*",
        "*annotation_set_relation*",
        "*start_start_date*",
        "*end_end_date*",
        "*start_end_date*",
        "*end_start_date*",
        "*label*",
        "*review*",
        "*__name",
        "*__status",
        "*__references",
        "*__notes",
    ]


APIS automatically adapts to changes in the datamodel. To automatically create the 
filters used in the GUI and the API we do some code inspection on the models in use. 
This setting is used to define the attributes that shouldn't be used for filtering. You shouldn't 
replace this list in your settings file but append to it: ``APIS_RELATIONS_FILTER_EXCLUDE.extend(['item A', 'item B'])``
The setting uses wildcards (*) and therefore allows to use subsets of attributes.


APIS_RELATIONS
--------------

.. code-block:: python

    APIS_RELATIONS = {
        "list_filters": [("relation_type",)],
        "search": ["relation_type__name"],
        "exclude": ["name"],
        "PersonPlace": {
            "labels": ["related_person", "related_place", "relation_type"],
            "search": [
                "relation_type__name",
                "related_person__name",
                "related_person__first_name",
                "related_place__name",
            ],
            "list_filters": [("relation_type",), ("related_person",), ("related_place",)],
        },} #This is only a subset of the settings in the base file


APIS_ENTITIES
-------------

.. code-block:: python


    APIS_ENTITIES = {
        "Place": {
            "merge": True,
            "search": ["name"],
            "form_order": ["name", "kind", "lat", "lng", "status", "collection"],
            "table_fields": ["name"],
            "additional_cols": ["id", "lat", "lng", "part_of"],
            "list_filters": [
                {"name": {"method": "name_label_filter"}},
                {"collection": {"label": "Collection"}},
                {"kind": {"label": "Kind of Place"}},
                "related_entity_name",
                "related_relationtype_name",
                "lat",
                "lng",
            ],
        },}

``APIS_ENTITIES`` is the setting to define the behavior of the entities list views. Every entity has its own setting.
The example above is the default setting of the Place entity. 
``merge`` is boolean and sets whether the list views will include the possibility to add a merge column. This column
allows to merge several entities in one target entity at once.
``search`` is an array and sets the fields that the search field searches.
``form_order`` defines the order of the fields in the metadata form of the respective entity.
``table_fields`` sets the default columns to show in the list views.
``additional_cols`` allows to set the columns that user can add to the result view.
``list_filters`` is an array of dictionaries/strings that sets the filters for the list view of the entity. If only the name 
of the filter is added, reasonable defaults will be used. If you want to configure the filter a bit more you can add a dictionary:

.. code-block:: python

    {'NAME_OF_THE_ATTRIBUTE': {'method': 'FILTER_METHOD_TO_BE_USED', 'label': 'LABEL'}}

One of the possible methods is for example the ``name_label_filter``. This filter not only searches in the attribute specified, but 
also in ``apis_labels``. The type of labels to be search can be specified in another setting: :ref:`APIS_ALTERNATE_NAMES`. The ``label`` 
setting can be used to set the label of the filter form.


APIS_API_EXCLUDE_SETS
---------------------

.. code-block:: python

    APIS_API_EXCLUDE_SETS = True


Boolean setting for excluding related objects from the API. Normally its not needed to touch this.


APIS_LIST_VIEWS_ALLOWED
-----------------------

.. code-block:: python

    APIS_LIST_VIEWS_ALLOWED = False


Sets whether list views are accessible for anonymous (not logged in) users.


APIS_DETAIL_VIEWS_ALLOWED
-------------------------

.. code-block:: python
    
    APIS_DETAIL_VIEWS_ALLOWED - False


Sets whether detail views are accessible for anonymous (note logged in) users.


APIS_LIST_VIEW_TEMPLATE
-----------------------

.. code-block:: python
    
    APIS_LIST_VIEW_TEMPLATE = "browsing/generic_list.html"


Sets the path of the list view template. This is only needed if you want to customize the appearance of the list views.


APIS_DELETE_VIEW_TEMPLATE
-------------------------

.. code-block:: python
    
    APIS_DELETE_VIEW_TEMPLATE = "webpage/confirm_delete.html"


Sets the path of the delete view template. This is only needed if you want to customize the appearance of the template for 
confirming the deletion of an object.


.. _Django Restframework: https://www.django-rest-framework.org/