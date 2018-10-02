#Labels App

depends on webpage-app

a hopefully very generic django-application to add, edit and delete labels. A label has the properties:

 - **Labels**: A freetext field for the entities name or label. (mandatory)
 - **Language**: A freetext field which is basically itself a label for the language of the Label. (optionally)
 - **ISO 639-3**: An autocomplete field for the according ISO 639-3 language code. (mandatory)
