from django.conf.urls import url

from entities.autocomplete3 import GenericVocabulariesAutocomplete

urlpatterns = [
    url(r'^autocomplete/(?P<vocab>[a-zA-Z0-9-]+)/(?P<direct>[a-zA-Z0-9-]+)/$',
        GenericVocabulariesAutocomplete.as_view(),
        name='generic_vocabularies_autocomplete'),
]