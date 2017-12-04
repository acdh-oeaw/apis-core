from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from entities import api_views
from highlighter.api_views import AnnotatorAgreementView, ShowOverlappingHighlights, TestDLModel

urlpatterns = [
    url(r'^savenetworkfiles/$', api_views.SaveNetworkFiles.as_view()),
    url(r'^annotatoragreement/$', AnnotatorAgreementView.as_view(), name='AnnotatorAgreementView'),
    url(r'^overlappinghighlights/$', ShowOverlappingHighlights.as_view(), name='ShowOverlappingHighlights'),
    url(r'^nlp_model/$', TestDLModel.as_view(), name='TestDLModel'),
]
