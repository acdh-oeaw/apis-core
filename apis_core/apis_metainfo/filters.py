import django_filters
from dal import autocomplete

from . models import *


class UriListFilter(django_filters.FilterSet):

    class Meta:
        model = Uri
        fields = "__all__"
