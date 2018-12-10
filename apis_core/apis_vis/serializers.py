from rest_framework import serializers
import pandas as pd
from django.db.models import Avg
from . utils import calculate_age


class VisAgeSerializer(serializers.BaseSerializer):
    
    #items = serializers.CharField()
    #title = serializers.CharField()
    #subtitle = serializers.CharField()
    #legendy = serializers.CharField()
    #legendx = serializers.CharField()
    #categories = serializers.CharField()
    #measuredObject = serializers.CharField()
    #ymin = serializers.FloatField()
    #x_axis = serializers.CharField()
    #payload = serializers.SerializerMethodField(method_name='add_age_data')
    #p = serializers.JSONField()

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

    def __init__(self, *args, many=False, **kwargs):
        super(VisAgeSerializer, self).__init__(*args, many=False, **kwargs)
        #self.fields['items'] = 'some'
        #self.fields['payload'] = obj
        #self.fields['title'] = 'Title'

