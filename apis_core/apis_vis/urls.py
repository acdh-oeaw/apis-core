from django.conf.urls import url
from . import views

app_name = 'apis_vis'

urlpatterns = [
    url(r'^heatmap/$', views.HeatMapView.as_view(), name='heatmap_view'),
    url(r'^heatmap-data/$', views.get_heatmap_data, name='get_heatmap_data'),
    url(r'^avg-age-data/$', views.get_average_age_data, name='get_avg_age_data'),
    url(r'^avg-age/$', views.AvgAge.as_view(), name='avgage_view'),
]
