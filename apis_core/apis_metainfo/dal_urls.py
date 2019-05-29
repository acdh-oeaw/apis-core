from django.conf.urls import url
from . import views
from . import dal_views
from .models import *

app_name = 'apis_metainfo'

urlpatterns = [
    url(
        r'^tempentity-autocomplete/$', dal_views.TempEntityClassAC.as_view(),
        name='apis_tempentity-autocomplete',
    )
]
