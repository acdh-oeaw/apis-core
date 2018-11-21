from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import serializers
from django.db.models.query import QuerySet
from apis_core.apis_labels.serializers import LabelSerializer
from apis_core.apis_vocabularies.models import ProfessionType


import re


class CollectionSerializer(serializers.Serializer): 
    id = serializers.IntegerField()
    name = serializers.CharField()


class ProfessionTypeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ProfessionType
        fields = ('id', 'name', 'label')


class EntityUriSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    uri = serializers.URLField()


class EntitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    uris = EntityUriSerializer(source="uri_set", many=True)
    labels = LabelSerializer(source="label_set", many=True)

    def add_relations(self, obj):
        res = {}
        mk = obj.__class__.__name__
        for rel in ContentType.objects.filter(
                app_label='apis_relations', model__icontains=mk.lower()):
            mk2 = re.match(r'{}([A-Za-z]+)'.format(mk.lower()), rel.model)
            if not mk2:
                mk2 = re.match(r'([A-Za-z]+{})'.format(mk.lower()), rel.model)
            res['{}s'.format(mk2.group(1))] = []
            if mk2.group(1).lower() != mk.lower():
                for rel2 in getattr(obj, '{}_set'.format(rel.model)).all():
                    res['{}s'.format(mk2.group(1))].append(RelationEntitySerializer(rel2, own_class=mk, read_only=True, context=self.context).data)
            else:
                for t in ['A', 'B']:
                    for rel2 in getattr(obj, 'related_{}{}'.format(mk.lower(), t)).all():
                        if t == 'A':
                            ok = '{}A'.format(mk.lower())
                        else:
                            ok = '{}B'.format(mk.lower())
                        res['{}s'.format(mk2.group(1))].append(RelationEntitySerializer(rel2, own_class=ok, read_only=True, context=self.context).data)
        return res

    def add_entity_type(self, obj):
        return str(obj.__class__.__name__)

    def __init__(self, *args, depth_ent=1, **kwargs):
        super(EntitySerializer, self).__init__(*args, **kwargs)
        if type(self.instance) == QuerySet:
            inst = self.instance[0]
        else:
            inst = self.instance
        for f in inst._meta.fields:
            field_name = re.search(r'([A-Za-z]+)\'>', str(f.__class__)).group(1)
            if field_name in [
                'CharField', 'DateField', 'DateTimeField', 'IntegerField', 'FloatField'
            ]:
                self.fields[f.name] = getattr(serializers, field_name)()
        for f in inst._meta.many_to_many:
            if f.name == 'profession':
                self.fields['profession'] = ProfessionTypeSerializer(many=True)
            elif f.name == 'collection':
                self.fields['collection'] = CollectionSerializer(many=True)
        self.fields['entity_type'] = serializers.SerializerMethodField(
            method_name="add_entity_type"
        )
        if depth_ent == 1:
            self.fields['relations'] = serializers.SerializerMethodField(
                method_name="add_relations"
            )


class RelationEntitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    relation_type = serializers.SerializerMethodField(method_name="add_relation_label")

    def add_entity(self, obj):
        return EntitySerializer(getattr(obj, "related_{}".format(self.entity_type)), depth_ent=0).data
    
    def add_relation_label(self, obj):
        cm = obj.__class__.__name__
        cm_match_1 = re.match(r'{}.*'.format(self.own_class), cm)
        cm_match_2 = re.match(r'.*{}'.format(self.own_class), cm)
        res_1 = dict()
        request_1 = self.context.get('request', None)
        if request_1 is not None:
            res_1['url'] =  self.context['request'].build_absolute_uri(reverse("apis_core:{}relation-detail".format(cm).lower(), kwargs={'pk':obj.relation_type.pk})) 
        else:
            res_1['url'] =  reverse("apis_core:{}relation-detail".format(cm).lower(), kwargs={'pk':obj.relation_type.pk})
        if cm_match_1:
            res_1['label'] =  obj.relation_type.label
        elif cm_match_2:
            res_1['label'] = obj.relation_type.label_reverse
        else:
            res_1['label'] =  "({})".format(obj.relation_type.label)
        return res_1

    def __init__(self, *args, own_class=None, **kwargs):
        super(RelationEntitySerializer, self).__init__(*args, **kwargs)
        self.own_class = own_class
        if self.instance is not None:
            for f in self.instance._meta.fields:
                if f.name.startswith('related_'):
                    mk2 = f.name.replace('related_', '')

                    if mk2.lower() != own_class.lower():
                        self.entity_type = mk2
                        if re.match(r'.*[A-B]$', mk2):
                            mk2_ = mk2[:-1]
                        else:
                            mk2_ = mk2
                        self.fields['{}'.format(mk2_)] = serializers.SerializerMethodField(
                            method_name="add_entity"
                        )
