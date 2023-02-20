from django.urls import path, re_path

from . import rel_views
from . import views

app_name = "apis_relations"

urlpatterns = [
    path(r"^ajax/get/$", views.get_form_ajax, name="get_form_ajax"),
    re_path(
        r"^ajax/save/(?P<entity_type>\w+)/(?P<kind_form>\w+)/(?P<SiteID>[0-9]+)(?:/(?P<ObjectID>[0-9]*))?/$",
        views.save_ajax_form,
        name="save_ajax_form",
    ),
    re_path(r"^(?P<entity>[a-z]+)/list/$", rel_views.GenericRelationView.as_view(), name="generic_relations_list"),
    re_path(
        r"^(?P<entity>[a-z]+)/(?P<pk>[0-9]+)/detail$",
        rel_views.GenericRelationDetailView.as_view(),
        name="generic_relations_detail_view",
    ),
]
