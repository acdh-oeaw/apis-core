from django.conf.urls import url
from . import views

app_name = 'relations'

urlpatterns = [
url(r'^ajax/get/$', views.get_form_ajax, name='get_form_ajax'),
url(r'^ajax/save/(?P<entity_type>\w+)/(?P<kind_form>\w+)/(?P<SiteID>[0-9]+)(?:/(?P<ObjectID>[0-9]*))?/$',
	views.save_ajax_form, name='save_ajax_form')
]
