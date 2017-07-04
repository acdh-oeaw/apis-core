from django.conf.urls import url
from django_spaghetti.views import plate

urlpatterns = [
    url(r'^$', plate, name='plate'),
]
