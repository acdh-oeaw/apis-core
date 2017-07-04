from django.conf.urls import url
from highlighter.views import ComputeAgreement

urlpatterns = [
    url(r'^agreement/$', ComputeAgreement.as_view(), name='agreement'),]

