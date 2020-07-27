from django.conf.urls import url

from . import views, api_views

app_name = 'apis_vis'

urlpatterns = [
    url(r'^heatmap/$', views.HeatMapView.as_view(), name='heatmap_view'),
    url(r'^heatmap-data/$', views.get_heatmap_data, name='get_heatmap_data'),
    url(r'^avg-age-data/$', views.get_average_age_data, name='get_avg_age_data'),
    url(r'^avg-age/$', views.AvgAge.as_view(), name='avgage_view'),
    url(r'^avg-members-data/$', views.get_average_members_data, name='get_avg_members_data'),
    url(r'^avg-members/$', views.MembersAmountPerYear.as_view(), name='avg_members_view'),
    url(
        r'^(?P<relation>[a-z]+)/data/$',
        api_views.GetVisJson.as_view(),
        name='person-institution-data'
    ),
    url(r'^inst-range-data/$', views.get_inst_range_data, name='get_inst_range_data'),
    url(r'^inst-range/$', views.InstRange.as_view(), name='inst_range_view'),
]
