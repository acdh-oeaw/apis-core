import pandas as pd
from collections import Counter
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.conf import settings

from apis_core.apis_relations.models import PersonPlace


def get_heatmap_data(request):

    rel_type = request.GET.get('rel-type')

    # places = Counter([
    #     (
    #         x.related_place.lat,
    #         x.related_place.lng,
    #     ) for x in PersonPlace.objects.filter(
    #         relation_type__name=rel_type
    #     ).exclude(related_place__lat__isnull=True)
    # ])
    places = [
        (
            x.related_place.lat,
            x.related_place.lng,
        ) for x in PersonPlace.objects.filter(
            relation_type__name=rel_type
        ).exclude(related_place__lat__isnull=True)
    ]
    # df = pd.DataFrame.from_dict(places, orient='index').reset_index()
    # df['lat'] = df.apply(lambda row: row['index'][1], axis=1)
    # df['lng'] = df.apply(lambda row: row['index'][0], axis=1)
    # df['normalized'] = (df[0]-df[0].min())/(df[0].max()-df[0].min())
    # payload = df[['lng', 'lat', 'normalized']].values.tolist()
    return JsonResponse(places, safe=False)


class HeatMapView(TemplateView):
    template_name = "apis_vis/heatmap.html"

    def get_context_data(self, **kwargs):
        context = super(HeatMapView, self).get_context_data(**kwargs)
        context['apps'] = settings.INSTALLED_APPS
        return context
