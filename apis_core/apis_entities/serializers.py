from django.urls import reverse_lazy
from rest_framework import serializers
from .models import Institution, Person, Place, Event, Work
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

import re


class EntityUriSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    uri = serializers.URLField()


class EntitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField() 
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    uris = EntityUriSerializer(source="uri_set", many=True)
    
    def add_relations(self, obj):
        res = {}
        mk = obj.__class__.__name__
        for rel in ContentType.objects.filter(app_label='apis_relations', model__icontains=mk.lower()):
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
        for f in self.instance._meta.fields:
            field_name = re.search(r'([A-Za-z]+)\'>', str(f.__class__)).group(1)
            if field_name in ['CharField', 'DateField', 'DateTimeField', 'IntegerField', 'FloatField']:
                self.fields[f.name] = getattr(serializers, field_name)()
        self.fields['entity_type'] = serializers.SerializerMethodField(method_name="add_entity_type")
        if depth_ent == 1:
            self.fields['relations'] = serializers.SerializerMethodField(method_name="add_relations")


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
        res_1['url'] =  self.context['request'].build_absolute_uri(reverse("apis_core:{}relation-detail".format(cm).lower(), kwargs={'pk':obj.relation_type.pk})) 
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
                        self.fields['{}'.format(mk2_)] = serializers.SerializerMethodField(method_name="add_entity")


class InstitutionSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Institution
        fields = ('id', 'name', 'uri_set', 'kind', 'collection', 'text')


class PersonSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Person
        fields = ('id', 'name', 'first_name', 'uri_set', 'profession', 'collection', 'text')


class PlaceSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Place
        fields = ('id', 'name', 'uri_set', 'collection', 'text', 'kind', 'lng', 'lat')


class EventSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Event
        fields = ('id', 'name', 'uri_set', 'collection', 'text')


class WorkSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Work
        fields = ('id', 'name', 'uri_set', 'collection', 'text')



class GeoJsonSerializer(serializers.BaseSerializer):

    def to_representation(self, obj):
        p_pk = self.context.get('p_pk')
        short = False
        url_r = reverse_lazy('apis:apis_entities:resolve_ambigue_place', kwargs={'pk': str(p_pk), 'uri': obj['id'][7:]})
        long = False
        if 'http://www.w3.org/2003/01/geo/wgs84_pos#long' in obj.keys():
            long = float(obj['http://www.w3.org/2003/01/geo/wgs84_pos#long'][0]['value'])
            lat = float(obj['http://www.w3.org/2003/01/geo/wgs84_pos#lat'][0]['value'])
        elif 'long' in obj.keys():
            long = float(obj['long'][0]['value'])
            lat = float(obj['lat'][0]['value'])
            short = True
        if long:
            popup = ''
            for k in obj.keys():
                if k == 'id' or k == 'long' or k == 'lat':
                    continue
                if not short or k.startswith('http'):
                    title = k.split('#')[-1]
                else:
                    title = k
                popup += '<b>{}:</b> {}<br/>'.format(title, obj[k][0]['value'])
            r = {"geometry": {
                    "type": "Point",
                    "coordinates": [long, lat]
                },
                "type": "Feature",
                "properties": {
                    "popupContent": """{}
                    <b>Geonames:</b> <a href='{}'>Select this URI</a>""".format(popup, url_r)
                },
                "id": url_r
                }
            return r
        else:
            return ''


class NetJsonEdgeSerializer(serializers.BaseSerializer):

    def to_representation(self, obj):
        ent_obj = obj.__class__.__name__
        ob_match = re.match(r'([A-Z][a-z]+)([A-Z][a-z]+)$', ent_obj)
        rel_a = 'related_' + ob_match.group(1).lower()
        rel_b = 'related_' + ob_match.group(2).lower()
        if rel_a == rel_b:
            rel_a += 'A'
            rel_b += 'B'
        r = {
            'source': getattr(obj, rel_a).pk,
            'target': getattr(obj, rel_b).pk,
            'id': obj.pk,
            'type': 'arrow',
            'data': dict()
        }
        r['data']['start_date'] = obj.start_date_written
        r['data']['end_date'] = obj.end_date_written
        r['data']['relation_type'] = obj.relation_type.name

        return r


class NetJsonNodeSerializer(serializers.BaseSerializer):

    def to_representation(self, obj):
        ent_obj = obj.__class__.__name__
        ent_url = reverse_lazy('apis:apis_entities:generic_entities_edit_view', kwargs={'pk': str(obj.pk),
                                                                              'entity': ent_obj.lower()})
        tt = """<div class='arrow'></div>
            <div class='sigma-tooltip-header'>{}</div>
            <div class='sigma-tooltip-body'>
            <table>
                <tr><th>Type</th> <td>{}</td></tr>
                <tr><th>Entity</th> <td><a href='{}'>Link</a></td></tr>
            </table>
            <button class='small-button' onclick='expand_node("{}", {})'>expand</button>
            </div>""".format(str(obj), ent_obj, ent_url, ent_obj, obj.pk)
        r = {
            'type': ent_obj.lower(),
            'label': str(obj),
            'id': obj.pk,
            'tooltip': tt,
            'data': dict()}
        r['data']['uri'] = [x.uri for x in obj.uri_set.all()]
        r['data']['collections'] = [x.name for x in obj.collection.all()]
        r['data']['notes'] = obj.notes
        r['data']['references'] = obj.references
        r['data']['start_date'] = obj.start_date_written
        r['data']['end_date'] = obj.end_date_written
        if ent_obj.lower() != 'person':
            if obj.kind:
                r['data']['kind'] = obj.kind.name
        if ent_obj.lower() == 'place':
            r['data']['lat'] = obj.lat
            r['data']['lon'] = obj.lng
        if ent_obj.lower() == 'person':
            r['data']['profession'] = [x.name for x in obj.profession.all()]
            if obj.gender:
                r['data']['gender'] = obj.gender
        return r
