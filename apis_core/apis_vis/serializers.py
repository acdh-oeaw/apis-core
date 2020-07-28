import pandas as pd
from django.db.models import Avg
from rest_framework import serializers

from .utils import calculate_age


class GenericBaseSerializer(serializers.BaseSerializer):

    def to_representation(self, obj):
        data = {
            "items": "some",
            "title": "{}".format('Members by Year'),
            "subtitle": "Person Institution relation type {}".format('some type'),
            "legendy": "legendy",
            "legendx": "legendx",
            "categories": "sorted(dates)",
            "measuredObject": "{} relations".format("find some variable"),
            "ymin": 0,
            "x_axis": "something",
            "payload": "something"
        }
        return data


class AvRelations(GenericBaseSerializer):

    def to_representation(self, obj):
        print(obj[0].__class__.__name__)
        qs = obj.filter(start_date__isnull=False).filter(end_date__isnull=False)
        start_year = int(str(qs.order_by('start_date')[0].start_date)[:4])
        end_year = int(str(qs.order_by('-start_date')[0].start_date)[:4])
        qs = [
            {
                'year': x,
                'members_new': qs.filter(start_date__year=x).count(),
                'members_all': qs.filter(
                    start_date__year__lte=x, end_date__year__gte=x
                ).count(),
            } for x in range(start_year, end_year)
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
            "measuredObject": "{} relations".format("find some variable"),
            "ymin": 0,
            "x_axis": df['year'].values.tolist(),
            "payload": payload
        }
        return data


class VisAgeSerializer(serializers.BaseSerializer):

    def to_representation(self, obj):
        qs = [
            {
                'year': x,
                'members_new': obj.filter(start_date__year=x).count(),
                'avg_birth_new': obj.filter(start_date__year=x)
                .aggregate(
                    Avg('related_person__start_date__year')
                )['related_person__start_date__year__avg'],
                'members_all': obj.filter(
                    start_date__year__lte=x, end_date__year__gte=x
                ).count(),
                'avg_birth': obj.filter(start_date__year__lte=x, end_date__year__gte=x)
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
        return payload
