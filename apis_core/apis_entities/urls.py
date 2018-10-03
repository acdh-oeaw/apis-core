from django.conf.urls import url

from .autocomplete3 import GenericEntitiesAutocomplete, GenericNetworkEntitiesAutocomplete
from .views import ReversionCompareView
from .views2 import GenericEntitiesCreateStanbolView
from . import views, views2, detail_views

app_name = 'apis_entities'

urlpatterns = [
    url(r'^entity/(?P<entity>[a-z]+)/(?P<pk>[0-9]+)/edit$',
        views2.GenericEntitiesEditView.as_view(),
        name='generic_entities_edit_view'),
    url(r'^entity/(?P<entity>[a-z]+)/(?P<pk>[0-9]+)/detail$',
        detail_views.GenericEntitiesDetailView.as_view(),
        name='generic_entities_detail_view'),
    url(r'^entity/(?P<entity>[a-z]+)/create$', views2.GenericEntitiesCreateView.as_view(),
        name='generic_entities_create_view'),
    url(r'^entity/(?P<entity>[a-z]+)/(?P<pk>[0-9]+)/delete$',
        views2.GenericEntitiesDeleteView.as_view(),
        name='generic_entities_delete_view'),
    url(r'^entity/(?P<entity>[a-z]+)/list/$',
        views.GenericListViewNew.as_view(), name='generic_entities_list'),
    url(r'^autocomplete/createstanbol/(?P<entity>[a-zA-Z0-9-]+)/$',
        GenericEntitiesCreateStanbolView.as_view(),
        name='generic_entities_stanbol_create'),
    url(r'^autocomplete/createstanbol/(?P<entity>[a-zA-Z0-9-]+)/(?P<ent_merge_pk>[0-9]+)/$',
        GenericEntitiesCreateStanbolView.as_view(),
        name='generic_entities_stanbol_create'),
    url(r'^autocomplete/(?P<entity>[a-zA-Z0-9-]+)/$',
        GenericEntitiesAutocomplete.as_view(),
        name='generic_entities_autocomplete'),
    url(r'^autocomplete/(?P<entity>[a-zA-Z0-9-]+)/(?P<db_include>[a-z]+)/$',
        GenericEntitiesAutocomplete.as_view(),
        name='generic_entities_autocomplete'),
    url(r'^autocomplete-network/(?P<entity>[a-zA-Z0-9-]+)/$',
        GenericNetworkEntitiesAutocomplete.as_view(),
        name='generic_network_entities_autocomplete'),
    url(r'^detail/work/(?P<pk>[0-9]+)$',
        detail_views.WorkDetailView.as_view(), name='work_detail'),
    url(r'^place/geojson/$', views.getGeoJson, name='getGeoJson'),
    url(r'^place/geojson/list/$', views.getGeoJsonList, name='getGeoJsonList'),
    url(r'^place/network/list/$', views.getNetJsonList, name='getNetJsonList'),
    url(r'^resolve/place/(?P<pk>[0-9]+)/(?P<uri>.+)$',
        views.resolve_ambigue_place, name='resolve_ambigue_place'),
    url(r'^maps/birthdeath/$', views.birth_death_map, name='birth_death_map'),
    url(r'^networks/relation_place/$', views.pers_place_netw, name='pers_place_netw'),
    url(r'^networks/relation_institution/$', views.pers_inst_netw, name='pers_inst_netw'),
    url(r'^networks/generic/$', views.generic_network_viz, name='generic_network_viz'),
    url(r'^compare/(?P<app>[a-z]+)/(?P<kind>[a-z]+)/(?P<pk>\d+)$', ReversionCompareView.as_view() ),
]
