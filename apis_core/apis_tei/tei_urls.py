from django.urls import path, re_path

from .tei_ac import TeiEntAc, TeiCompleterAc

from apis_core.apis_tei import views

app_name = "apis_tei"

urlpatterns = [
    re_path(r"^autocomplete/(?P<entity>[a-zA-Z0-9-]+)/$", TeiEntAc.as_view(), name="generic_entities_autocomplete"),
    re_path(r"^tei-completer/(?P<entity>[a-zA-Z0-9-]+)/$", TeiCompleterAc.as_view(), name="tei_completer_autocomplete"),
    re_path(r"^person/(?P<pk>[0-9]+)$", views.person_as_tei, name="person_as_tei"),
    re_path(r"^place/(?P<pk>[0-9]+)$", views.place_as_tei, name="place_as_tei"),
    re_path(r"^org/(?P<pk>[0-9]+)$", views.org_as_tei, name="org_as_tei"),
    re_path(r"^institution/(?P<pk>[0-9]+)$", views.org_as_tei, name="org_as_tei"),
    re_path(r"^work/(?P<pk>[0-9]+)$", views.work_as_tei, name="work_as_tei"),
    path(r"uri-to-tei", views.uri_to_tei, name="uri_to_tei"),
]
