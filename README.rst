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