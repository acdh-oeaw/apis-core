from django.urls import path, re_path

from . import views, views2, detail_views, merge_views
from .autocomplete3 import (
    GenericEntitiesAutocomplete,
    GenericNetworkEntitiesAutocomplete,
)

# from .views import ReversionCompareView TODO: add again when import is fixec
from .views2 import GenericEntitiesCreateStanbolView

app_name = "apis_entities"

urlpatterns = [
    re_path(
        r"^entity/(?P<entity>[a-z]+)/(?P<pk>[0-9]+)/edit$",
        views2.GenericEntitiesEditView.as_view(),
        name="generic_entities_edit_view",
    ),
    re_path(
        r"^entity/(?P<entity>[a-z]+)/(?P<pk>[0-9]+)/detail$",
        detail_views.GenericEntitiesDetailView.as_view(),
        name="generic_entities_detail_view",
    ),
    re_path(
        r"^entity/(?P<entity>[a-z]+)/create$",
        views2.GenericEntitiesCreateView.as_view(),
        name="generic_entities_create_view",
    ),
    re_path(
        r"^entity/(?P<entity>[a-z]+)/(?P<pk>[0-9]+)/delete$",
        views2.GenericEntitiesDeleteView.as_view(),
        name="generic_entities_delete_view",
    ),
    re_path(
        r"^entity/(?P<entity>[a-z]+)/list/$",
        views.GenericListViewNew.as_view(),
        name="generic_entities_list",
    ),
    re_path(
        r"^autocomplete/createstanbol/(?P<entity>[a-zA-Z0-9-]+)/$",
        GenericEntitiesCreateStanbolView.as_view(),
        name="generic_entities_stanbol_create",
    ),
    re_path(
        r"^autocomplete/createstanbol/(?P<entity>[a-zA-Z0-9-]+)/(?P<ent_merge_pk>[0-9]+)/$",
        GenericEntitiesCreateStanbolView.as_view(),
        name="generic_entities_stanbol_create",
    ),
    re_path(
        r"^autocomplete/(?P<entity>[a-zA-Z0-9-]+)/(?P<ent_merge_pk>[0-9]+)/$",
        GenericEntitiesAutocomplete.as_view(),
        name="generic_entities_autocomplete",
    ),
    re_path(
        r"^autocomplete/(?P<entity>[a-zA-Z0-9-]+)/$",
        GenericEntitiesAutocomplete.as_view(),
        name="generic_entities_autocomplete",
    ),
    re_path(
        r"^autocomplete/(?P<entity>[a-zA-Z0-9-]+)/(?P<db_include>[a-z]+)/$",
        GenericEntitiesAutocomplete.as_view(),
        name="generic_entities_autocomplete",
    ),
    re_path(
        r"^autocomplete-network/(?P<entity>[a-zA-Z0-9-]+)/$",
        GenericNetworkEntitiesAutocomplete.as_view(),
        name="generic_network_entities_autocomplete",
    ),
    # TODO __sresch__ : This seems unused. Remove it once sure
    # url(r'^detail/work/(?P<pk>[0-9]+)$',
    #     detail_views.WorkDetailView.as_view(), name='work_detail'),
    path(r"place/geojson/", views.getGeoJson, name="getGeoJson"),
    path(r"place/geojson/list/", views.getGeoJsonList, name="getGeoJsonList"),
    path(r"place/network/list/", views.getNetJsonList, name="getNetJsonList"),
    re_path(
        r"^resolve/place/(?P<pk>[0-9]+)/(?P<uri>.+)$",
        views.resolve_ambigue_place,
        name="resolve_ambigue_place",
    ),
    path(r"maps/birthdeath/", views.birth_death_map, name="birth_death_map"),
    path(r"networks/relation_place/", views.pers_place_netw, name="pers_place_netw"),
    path(r"networks/relation_institution/", views.pers_inst_netw, name="pers_inst_netw"),
    path(r"networks/generic/", views.generic_network_viz, name="generic_network_viz"),
    #    url(
    #        r'^compare/(?P<app>[a-z_]+)/(?P<kind>[a-z]+)/(?P<pk>\d+)$', ReversionCompareView.as_view()
    #    ),
    path(r"merge-objects/", merge_views.merge_objects, name="merge_objects"),
]
