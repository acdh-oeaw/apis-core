from django.conf.urls import url
from . import views
from . import rel_views

app_name = 'apis_relations'

urlpatterns = [
    url(r'^ajax/get/$', views.get_form_ajax, name='get_form_ajax'),
    url(
        r'^ajax/save/(?P<entity_type>\w+)/(?P<kind_form>\w+)/(?P<SiteID>[0-9]+)(?:/(?P<ObjectID>[0-9]*))?/$',
        views.save_ajax_form, name='save_ajax_form'
    ),
    url(r'^(?P<entity>[a-z]+)/list/$',
        rel_views.GenericRelationView.as_view(), name='generic_relations_list'),
    url(r'^(?P<entity>[a-z]+)/(?P<pk>[0-9]+)/detail$',
        rel_views.GenericRelationDetailView.as_view(),
        name='generic_relations_detail_view'),
]
