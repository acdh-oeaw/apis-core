from django.conf.urls import url

from . tei_ac import TeiEntAc

app_name = 'apis_tei'

urlpatterns = [
    url(
        r'^autocomplete/(?P<entity>[a-zA-Z0-9-]+)/$',
        TeiEntAc.as_view(),
        name='generic_entities_autocomplete'
    ),
]
