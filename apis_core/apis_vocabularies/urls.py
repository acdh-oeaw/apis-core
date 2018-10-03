from django.conf.urls import url

from apis_core.apis_entities.autocomplete3 import GenericVocabulariesAutocomplete

app_name = 'apis_vocabularies'

urlpatterns = [
    url(r'^autocomplete/(?P<vocab>[a-zA-Z0-9-]+)/(?P<direct>[a-zA-Z0-9-]+)/$',
        GenericVocabulariesAutocomplete.as_view(),
        name='generic_vocabularies_autocomplete'),
]
