from django.urls import path, re_path

from . import views

app_name = 'apis_metainfo'

urlpatterns = [
    path(
        r'apis/metainfo/uri/',
        views.UriListView.as_view(),
        name='uri_browse'
    ),
    re_path(
        r'^uri/detail/(?P<pk>[0-9]+)$',
        views.UriDetailView.as_view(),
        name='uri_detail'
    ),
    path(
        r'uri/create/',
        views.UriCreate.as_view(),
        name='uri_create'
    ),
    re_path(
        r'^uri/edit/(?P<pk>[0-9]+)$',
        views.UriUpdate.as_view(),
        name='uri_edit'
    ),
    re_path(
        r'^uri/delete/(?P<pk>[0-9]+)$',
        views.UriDelete.as_view(),
        name='uri_delete'),
]
