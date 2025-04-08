from django.urls import path, re_path

from . import views, api_views

app_name = "apis_vis"

urlpatterns = [
    path(r"heatmap/", views.HeatMapView.as_view(), name="heatmap_view"),
    path(r"heatmap-data/", views.get_heatmap_data, name="get_heatmap_data"),
    path(r"avg-age-data/", views.get_average_age_data, name="get_avg_age_data"),
    path(r"avg-age/", views.AvgAge.as_view(), name="avgage_view"),
    path(r"avg-members-data/", views.get_average_members_data, name="get_avg_members_data"),
    path(r"avg-members/", views.MembersAmountPerYear.as_view(), name="avg_members_view"),
    re_path(r"^(?P<relation>[a-z]+)/data/$", api_views.GetVisJson.as_view(), name="person-institution-data"),
    path(r"inst-range-data/", views.get_inst_range_data, name="get_inst_range_data"),
    path(r"inst-range/", views.InstRange.as_view(), name="inst_range_view"),
]
