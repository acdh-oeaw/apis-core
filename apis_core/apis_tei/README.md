# custom TEI serialisation of Entities

## endpoints

* `/apis/tei/ort|institution|work|person/{id}`

## needed settings

We need to define which e.g. PersonPlaceRelation holds information about a birth/death place. This is done via optional settings listing the ID(s) (several are possible) [# ToDo: check if actually all items are rendered or just the first one]

```python
BIRTH_REL = [88, ]
DEATH_REL = [89, ]

PL_A_PART_OF = [1106, 1136]
PL_B_LOCATED_IN = [971, ]

ORG_LOCATED_IN = [1141, 970, 1160]
```



## TEI commands

## serialize person/places/orgs from collection

`python manage.py persons_to_tei --collection=5  --settings=apis.settings.local_pmb`
`python manage.py places_to_tei --collection=5  --settings=apis.settings.local_pmb`
`python manage.py orgs_to_tei --collection=5  --settings=apis.settings.local_pmb`
`python manage.py works_to_tei --collection=5  --settings=apis.settings.local_pmb`


## serialize all persons/places full

`python manage.py persons_to_tei -f --settings=apis.settings.local_pmb`

## serialize first 25 persons/places
`python manage.py persons_to_tei -f -l --settings=apis.settings.local_pmb`