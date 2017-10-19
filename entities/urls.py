from django.conf.urls import url
from . import views, views2

urlpatterns = [
url(r'^entity/(?P<entity>[a-z]+)/(?P<pk>[0-9]+)/edit$', views2.GenericEntitiesEditView.as_view(),
    name='generic_entities_edit_view'),
url(r'^entity/(?P<entity>[a-z]+)/create$', views2.GenericEntitiesCreateView.as_view(),
    name='generic_entities_create_view'),
url(r'^entity/(?P<entity>[a-z]+)/(?P<pk>[0-9]+)/delete$', views2.GenericEntitiesDeleteView.as_view(),
    name='generic_entities_delete_view'),
url(r'^entity/(?P<entity>[a-z]+)/list/$', views.GenericListViewNew.as_view(), name='generic_entities_list'),
url(r'^place/geojson/$', views.getGeoJson, name='getGeoJson'),
url(r'^place/geojson/list/$', views.getGeoJsonList, name='getGeoJsonList'),
url(r'^place/network/list/$', views.getNetJsonList, name='getNetJsonList'),
url(r'^resolve/place/(?P<pk>[0-9]+)/(?P<uri>.+)$', views.resolve_ambigue_place, name='resolve_ambigue_place'),
url(r'^maps/birthdeath/$', views.birth_death_map, name='birth_death_map'),
url(r'^networks/relation_place/$', views.pers_place_netw, name='pers_place_netw'),
url(r'^networks/relation_institution/$', views.pers_inst_netw, name='pers_inst_netw'),
url(r'^networks/generic/$', views.generic_network_viz, name='generic_network_viz'),
]
