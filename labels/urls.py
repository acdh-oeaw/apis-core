# -*- coding: utf-8 -*-
from django.conf.urls import url
from . import views

urlpatterns = [
url(r'^list/$', views.LabelListView.as_view(), name='label_list'),
url(r'^create/$', views.label_create, name='label_create'),
url(r'^edit/(?P<pk>[0-9]+)$', views.label_edit, name='label_edit'),
url(r'^delete/(?P<pk>[0-9]+)$', views.LabelDelete.as_view(), name='label_delete'),
]