# TEI commands

## serialize person from collection

`python manage.py persons_to_tei --collection=5  --settings=apis.settings.local_pmb`

## serialize all person full

`python manage.py persons_to_tei -f --settings=apis.settings.local_pmb`

## serialize first 25 persons
`python manage.py persons_to_tei -f -l --settings=apis.settings.local_pmb`