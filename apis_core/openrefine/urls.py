from django.urls import path

from . import views

app_name = "openrefine"

urlpatterns = [
    path("reconcile", views.reconcile),
    path("properties", views.properties),
    path("suggest/type", views.suggest_types),
]
