import pandas as pd
from django.db.models import Avg
from django.http import JsonResponse
from django.views.generic import TemplateView

from apis_core.apis_relations.models import *
from .utils import calculate_age


def get_inst_range_data(request):
    df = pd.DataFrame(list(InstitutionInstitution.objects.filter(
        relation_type__name="ist Teil von").distinct().values_list(
        'related_institutionA__name',
        'related_institutionA__start_date__year',
        'related_institutionA__end_date__year',
        'related_institutionB__name'
        )
    ), columns=['name', 'start_year', 'end_year', 'teil von']).fillna(2018)
    df.sort_values('start_year')

    data = {
        "items": "some",
        "title": "{}".format('Kommissionen'),
        "subtitle": "Person Institution relation type {}".format('some type'),
        "legendy": "legendy",
        "legendx": "legendx",
        "categories": "sorted(dates)",
        "measuredObject": "{}".format("Persons average Age"),
        "ymin": 0,
        "x_axis": df['name'].values.tolist(),
        "payload": [
            {
                'name': 'Kommissionen',
                'data': df[['start_year', 'end_year']].values.tolist()
            }
        ]
    }

    return JsonResponse(data, safe=False)


def get_average_members_data(request):
    rel_type = request.GET.get('rel-type')
    rel_inst = request.GET.get('rel-inst')
    start_year = request.GET.get('start-year')
    end_year = request.GET.get('start-year')
    per_inst = PersonInstitution.objects.filter(related_institution_id__in=[3, 2])
    if rel_type:
        data = []
    else:
        start_year = int(str(per_inst.order_by('start_date')[0].start_date)[:4])
        end_year = int(str(per_inst.order_by('-start_date')[0].start_date)[:4])
        qs = [
            {
                'year': x,
                'members_new': per_inst.filter(start_date__year=x).count(),
                'members_all': per_inst.filter(
                    start_date__year__lte=x, end_date__year__gte=x
                ).count(),
            } for x in range(1847, 2015)
        ]
        df = pd.DataFrame(qs)
        payload = [
            {
                'name': 'all members',
                'data': [x for x in df[['members_all']].values.tolist()]
            },
            {
                'name': 'new members',
                'data': [x for x in df[['members_new']].values.tolist()]
            }
        ]
        data = {
            "items": "some",
            "title": "{}".format('Members by Year'),
            "subtitle": "Person Institution relation type {}".format('some type'),
            "legendy": "legendy",
            "legendx": "legendx",
            "categories": "sorted(dates)",
            "measuredObject": "{}".format("Persons average Age"),
            "ymin": 0,
            "x_axis": df['year'].values.tolist(),
            "payload": payload
        }
    return JsonResponse(data, safe=False)


def get_average_age_data(request):
    rel_type = request.GET.get('rel-type')
    rel_inst = request.GET.get('rel-inst')
    start_year = request.GET.get('start-year')
    end_year = request.GET.get('start-year')
    per_inst = PersonInstitution.objects.filter(related_institution_id__in=[3, 2])
    if rel_type:
        data = []
    else:
        start_year = int(str(per_inst.order_by('start_date')[0].start_date)[:4])
        end_year = int(str(per_inst.order_by('-start_date')[0].start_date)[:4])
        qs = [
            {
                'year': x,
                'members_new': per_inst.filter(start_date__year=x).count(),
                'avg_birth_new': per_inst.filter(start_date__year=x)
                .aggregate(
                    Avg('related_person__start_date__year')
                )['related_person__start_date__year__avg'],
                'members_all': per_inst.filter(
                    start_date__year__lte=x, end_date__year__gte=x
                ).count(),
                'avg_birth': per_inst.filter(start_date__year__lte=x, end_date__year__gte=x)
                .aggregate(
                    Avg('related_person__start_date__year')
                )['related_person__start_date__year__avg']
            } for x in range(1847, 2015)
        ]
        df = pd.DataFrame(qs)
        df['avg_age_new'] = df.apply(lambda row: calculate_age(row, 'avg_birth_new'), axis=1)
        df['avg_age_all'] = df.apply(lambda row: calculate_age(row, 'avg_birth'), axis=1)
        payload = [
            {
                'name': 'average age all',
                'data': [x for x in df[['avg_age_all']].values.tolist()]
            },
            {
                'name': 'average age new',
                'data': [x for x in df[['avg_age_new']].values.tolist()]
            }
        ]
        data = {
            "items": "some",
            "title": "{}".format('Average Age by Year'),
            "subtitle": "Person Institution relation type {}".format('some type'),
            "legendy": "legendy",
            "legendx": "legendx",
            "categories": "sorted(dates)",
            "measuredObject": "{}".format("Persons average Age"),
            "ymin": 0,
            "x_axis": df['year'].values.tolist(),
            "payload": payload
        }
    return JsonResponse(data, safe=False)


def get_heatmap_data(request):

    rel_type = request.GET.get('rel-type')
    places = [
        (
            x.related_place.lat,
            x.related_place.lng,
        ) for x in PersonPlace.objects.filter(
            relation_type__name=rel_type
        ).exclude(related_place__lat__isnull=True)
    ]
    return JsonResponse(places, safe=False)


class HeatMapView(TemplateView):
    template_name = "apis_vis/heatmap.html"


class AvgAge(TemplateView):
    template_name = "apis_vis/avgage.html"


class MembersAmountPerYear(TemplateView):
    template_name = "apis_vis/avgmemperyear.html"


class InstRange(TemplateView):
    template_name = "apis_vis/inst_range.html"
