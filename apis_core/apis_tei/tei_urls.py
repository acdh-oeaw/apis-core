from django.conf.urls import url

from .tei_ac import TeiEntAc, TeiCompleterAc
# from .views import person_as_tei

app_name = 'apis_tei'

urlpatterns = [
    url(
        r'^autocomplete/(?P<entity>[a-zA-Z0-9-]+)/$',
        TeiEntAc.as_view(),
        name='generic_entities_autocomplete'
    ),
    url(
        r'^tei-completer/(?P<entity>[a-zA-Z0-9-]+)/$',
        TeiCompleterAc.as_view(),
        name='tei_completer_autocomplete'
    ),
    # url(
    #      r'^person/(?P<pk>[0-9]+)$',
    #     person_as_tei,
    #     name='person_as_tei'
    # )
]
