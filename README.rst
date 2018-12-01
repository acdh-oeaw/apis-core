Readme
======

The APIS_ project intents to semantically annotate the Austrian Bibliography Lexicon (ÖBL_). To achieve this goal
we develop(ed) this web-app. It is based on a 5 entities (person, place, institution, event, work) data model.
All 5 entities are connected to each other. Entities, as well as relations between them, can be typed with vocabularies
similar to the Simple Knowledge Organization System (SKOS_).

APIS comes with a built in system of autocompletes that allows researchers to import meta-data of entities with just a
single click. Out of the box APIS supports Stanbol_ as a backend for the autocompletes, but the system is rather easy to
adapt to any Restfull API. APIS also supports the parsing of RDFs_ describing entities into an entity. The parsing is
configured in a settings file.

APIS comes also with a built in highlighter. The highlighter is configured via the built in admin backend and allows
to annotate texts with entities and/or relations between entities.

For a demo of the application please refer to apisdev_.


Installation
------------

The installation process is described in the apis-core docs_.


Licensing
---------

All code unless otherwise noted is licensed under the terms of the MIT License (MIT). Please refer to the file LICENSE in the root directory of this repository.

All documentation and images unless otherwise noted are licensed under the terms of Creative Commons Attribution-ShareAlike 4.0 International License. To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/4.0/


.. _APIS: https://www.oeaw.ac.at/acdh/projects/apis/
.. _apisdev: https://apisdev.acdh.oeaw.ac.at
.. _ÖBL: http://www.biographien.ac.at
.. _SKOS: https://en.wikipedia.org/wiki/Simple_Knowledge_Organization_System
.. _Stanbol: https://stanbol.apache.org/
.. _RDFs: https://en.wikipedia.org/wiki/Resource_Description_Framework
.. _docs: https://acdh-oeaw.github.io/apis-core/


Install the package
------------

things which needs to be added to the project's settings and urls files

# mandatory:

## add apis-apps to `INSTALLED_APPS`

```
...
'apis_core.apis_entities',
'apis_core.apis_metainfo',
'apis_core.apis_relations',
'apis_core.apis_vocabularies',
'apis_core.apis_labels',
...
```

## add apis specific context_processors

```
'OPTIONS': {
    'context_processors': [
        ...
        'webpage.webpage_content_processors.is_dev_version',
        'apis_core.context_processors.custom_context_processors.add_entities',
        ...
    ],
},
```

## APIS_ENTITIES

todo!

# optional:

## APIS_NEXT_PREV

In case you set this parameter to `False` then `apis_core.apis_metainfo.TempEntityClass.get_prev_url()` and `apis_core.apis_metainfo.TempEntityClass.get_next_url()` methods return `False`. Set this param to deactivate the prev/next browsing function in the entitie's detail view. Default (if not set) is `True`


## APIS_BASE_URI

This parameter is used to construct URIs for Apis Entities in case no external URIs (like geonames or gnd) are provided, defaults to `http://apis.info`

e.g. `APIS_BASE_URI = 'https://myprocect/objects/'` will create a URI like `https://myprocect/objects/1234`

## log-in-restrictions
If theese settings are missing or set to `False` not logged in users will be redirected to log-in page

```
APIS_LIST_VIEWS_ALLOWED = True
APIS_DETAILKJL_VIEWS_ALLOWED = True
```

## Override the entities' list view template:

Change the template name in the project's settings file by adding the following variable

`APIS_LIST_VIEW_TEMPLATE = "browsing/generic_list.html"`
`APIS_DELETE_VIEW_TEMPLATE = "webpage/confirm_delete.html"`

## TEI

In case you store TEI encoded XML in you TEXT objects, you can display those with https://github.com/TEIC/CETEIcean. Therefore you'll need to list the values of `Text.kind.name` in a settings parameter.
Let's say that all TEI texts are stored in Text fields with kind "xml/tei transcription":

`APIS_TEI_TEXTS = ['xml/tei transcription']`

You'll also need to set define the locations for the CETEICEAN specific static files via dedicated paramters:

```
APIS_CETEICEAN_CSS = "http://teic.github.io/CETEIcean/css/CETEIcean.css"
APIS_CETEICEAN_JS = "http://teic.github.io/CETEIcean/js/CETEI.js"
``` 
