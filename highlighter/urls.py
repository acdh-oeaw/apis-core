from django.conf.urls import url
from django.conf import settings

urlpatterns = []

if 'annotator agreement' in getattr(settings, "APIS_COMPONENTS", []):
    from highlighter.views import ComputeAgreement
    urlpatterns.append(url(r'^agreement/$', ComputeAgreement.as_view(), name='agreement'))
