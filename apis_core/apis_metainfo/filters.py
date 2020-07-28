import django_filters

from .models import *


class UriListFilter(django_filters.FilterSet):

    uri = django_filters.CharFilter(
        lookup_expr='icontains',
        help_text=Uri._meta.get_field('uri').help_text,
        label=Uri._meta.get_field('uri').verbose_name
        )
    domain = django_filters.CharFilter(
        lookup_expr='icontains',
        help_text=Uri._meta.get_field('domain').help_text,
        label=Uri._meta.get_field('domain').verbose_name
        )
    entity__name = django_filters.CharFilter(
        lookup_expr='icontains',
        help_text=Uri._meta.get_field('entity').help_text,
        label=Uri._meta.get_field('entity').verbose_name
        )

    class Meta:
        model = Uri
        fields = "__all__"
