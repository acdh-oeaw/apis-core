from django.conf.urls import url

from . import views

app_name = 'apis_metainfo'

urlpatterns = [
    url(
        r'^apis/metainfo/uri/$',
        views.UriListView.as_view(),
        name='uri_browse'
    ),
    url(
        r'^uri/detail/(?P<pk>[0-9]+)$',
        views.UriDetailView.as_view(),
        name='uri_detail'
    ),
    url(
        r'^uri/create/$',
        views.UriCreate.as_view(),
        name='uri_create'
    ),
    url(
        r'^uri/edit/(?P<pk>[0-9]+)$',
        views.UriUpdate.as_view(),
        name='uri_edit'
    ),
    url(
        r'^uri/delete/(?P<pk>[0-9]+)$',
        views.UriDelete.as_view(),
        name='uri_delete'),
]
