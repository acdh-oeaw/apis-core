from django.conf import settings
from django.conf.urls import url
from django.urls import path

from . import api_views

app_name = 'apis_entities'

urlpatterns = [
    url(r'^savenetworkfiles/$', api_views.SaveNetworkFiles.as_view()),
    url(r'^getorcreateentity/$', api_views.GetOrCreateEntity.as_view(), name='GetOrCreateEntity'),
    path(r'entity/<int:pk>/', api_views.GetEntityGeneric.as_view(), name="GetEntityGeneric"),
    path(r'uri/', api_views.uri_resolver, name="UriResolver"),
    path(r'getrelatedplaces/', api_views.GetRelatedPlaces.as_view(), name="GetRelatedPlaces"),
    path(r'lifepath/<int:pk>/', api_views.LifePathViewset.as_view(), name="Lifepathviewset")
]

if 'deep learning' in getattr(settings, "APIS_COMPONENTS", []) and 'apis_highlighter' in settings.INSTALLED_APPS:
    from apis_highlighter.api_views import TestDLModel
    urlpatterns.append(url(r'^nlp_model/$', TestDLModel.as_view(), name='TestDLModel'),)

if 'apis_highlighter' in settings.INSTALLED_APPS:
    from apis_highlighter.api_views import AnnotatorAgreementView, ShowOverlappingHighlights
    urlpatterns.extend([url(r'^annotatoragreement/$',
                            AnnotatorAgreementView.as_view(),
                            name='AnnotatorAgreementView'),
                       url(r'^overlappinghighlights/$',
                           ShowOverlappingHighlights.as_view(),
                           name='ShowOverlappingHighlights')])
