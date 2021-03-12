import re

from django.conf import settings
from django.urls import reverse_lazy
from rest_framework import serializers

from .models import Institution, Person, Place, Event, Work
from ..apis_relations.models import PersonInstitution, InstitutionPlace, PersonPlace
from ..apis_vocabularies.models import RelationBaseClass, InstitutionPlaceRelation


class BaseEntitySerializer(serializers.HyperlinkedModelSerializer):
    uri_set = serializers.HyperlinkedRelatedField(
        view_name="apis:apis_api:uri-detail",
        lookup_field="pk",
        many=True,
        read_only=True,
    )
    collection = serializers.HyperlinkedRelatedField(
        view_name="apis:apis_api:collection-detail",
        lookup_field="pk",
        many=True,
        read_only=True,
    )
    text = serializers.HyperlinkedRelatedField(
        view_name="apis:apis_api:text-detail",
        lookup_field="pk",
        many=True,
        read_only=True,
    )


class InstitutionSerializer(BaseEntitySerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:institution-detail", lookup_field="pk"
    )

    kind = serializers.HyperlinkedRelatedField(
        view_name="apis:apis_api:institutiontype-detail", read_only=True
    )

    class Meta:
        model = Institution
        fields = ("url", "id", "name", "uri_set", "kind", "collection", "text")


class PersonSerializer(BaseEntitySerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:person-detail", lookup_field="pk"
    )
    profession = serializers.HyperlinkedRelatedField(
        view_name="apis:apis_api:professiontype-detail",
        lookup_field="pk",
        many=True,
        read_only=True,
    )

    class Meta:
        model = Person
        fields = (
            "url",
            "id",
            "name",
            "first_name",
            "uri_set",
            "profession",
            "collection",
            "text",
        )


class PlaceSerializer(BaseEntitySerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:place-detail", lookup_field="pk"
    )

    kind = serializers.HyperlinkedRelatedField(
        view_name="apis:apis_api:placetype-detail", lookup_field="pk", read_only=True
    )

    class Meta:
        model = Place
        fields = (
            "url",
            "id",
            "name",
            "uri_set",
            "collection",
            "text",
            "kind",
            "lng",
            "lat",
        )


class EventSerializer(BaseEntitySerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:event-detail", lookup_field="pk"
    )

    kind = serializers.HyperlinkedRelatedField(
        view_name="apis:apis_api:eventtype-detail", lookup_field="pk", read_only=True
    )

    class Meta:
        model = Event
        fields = ("url", "id", "name", "uri_set", "collection", "text", "kind")


class WorkSerializer(BaseEntitySerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name="apis:apis_api:work-detail", lookup_field="pk"
    )

    kind = serializers.HyperlinkedRelatedField(
        view_name="apis:apis_api:worktype-detail", lookup_field="pk", read_only=True
    )

    class Meta:
        model = Work
        fields = ("url", "id", "name", "uri_set", "collection", "text", "kind")


class GeoJsonSerializer(serializers.BaseSerializer):
    def to_representation(self, obj):
        p_pk = self.context.get("p_pk")
        short = False
        url_r = reverse_lazy(
            "apis:apis_entities:resolve_ambigue_place",
            kwargs={"pk": str(p_pk), "uri": obj["id"][7:]},
        )
        long = False
        if "http://www.w3.org/2003/01/geo/wgs84_pos#long" in obj.keys():
            long = float(
                obj["http://www.w3.org/2003/01/geo/wgs84_pos#long"][0]["value"]
            )
            lat = float(obj["http://www.w3.org/2003/01/geo/wgs84_pos#lat"][0]["value"])
        elif "long" in obj.keys():
            long = float(obj["long"][0]["value"])
            lat = float(obj["lat"][0]["value"])
            short = True
        if long:
            popup = ""
            for k in obj.keys():
                if k == "id" or k == "long" or k == "lat":
                    continue
                if not short or k.startswith("http"):
                    title = k.split("#")[-1]
                else:
                    title = k
                popup += "<b>{}:</b> {}<br/>".format(title, obj[k][0]["value"])
            r = {
                "geometry": {"type": "Point", "coordinates": [long, lat]},
                "type": "Feature",
                "properties": {
                    "popupContent": """{}
                    <b>Geonames:</b> <a href='{}'>Select this URI</a>""".format(
                        popup, url_r
                    )
                },
                "id": url_r,
            }
            return r
        else:
            return ""


class GeoJsonSerializerTheme(serializers.BaseSerializer):
    def to_representation(self, obj):
        if obj[0] is None:
            return ""
        url_r = reverse_lazy(
            "apis:apis_core:place-detail", kwargs={"pk": str(obj[0].pk)}
        )
        if obj[0].lng:
            relations = []
            for rel2 in obj[1]:
                if rel2[1] is not None:
                    res_str = f"{rel2[1].name} / {rel2[0].name}"
                else:
                    res_str = f"{rel2[0].name}"
                if rel2[2] is not None:
                    res_str += f" ({rel2[2]}-"
                if rel2[3] is not None:
                    if res_str.endswith("-"):
                        res_str += f"{rel2[3]})"
                    else:
                        res_str += f" (-{rel2[3]})"
                if "(" in res_str and not res_str.endswith(")"):
                    res_str += ")"
                # relations.append((res_str, rel2[2], rel2[3]))
                relations.append(
                    {
                        "id": rel2[-1].pk,
                        "relation": res_str,
                        "start_date": rel2[2],
                        "end_date": rel2[3],
                    }
                )
            r = {
                "geometry": {"type": "Point", "coordinates": [obj[0].lng, obj[0].lat]},
                "type": "Feature",
                "properties": {
                    "name": obj[0].name,
                    "uris": [x.uri for x in obj[0].uri_set.all()],
                    "kind": obj[0].kind.name
                    if obj[0].kind is not None
                    else "undefined",
                    "url": url_r,
                    # "relation_kind": ", ".join([x[0].name for x in obj[1]])
                    "relations": relations,
                },
                "id": url_r,
            }
            return r
        else:
            return ""


class NetJsonEdgeSerializer(serializers.BaseSerializer):
    def to_representation(self, obj):
        ent_obj = obj.__class__.__name__
        ob_match = re.match(r"([A-Z][a-z]+)([A-Z][a-z]+)$", ent_obj)
        rel_a = "related_" + ob_match.group(1).lower()
        rel_b = "related_" + ob_match.group(2).lower()
        if rel_a == rel_b:
            rel_a += "A"
            rel_b += "B"
        r = {
            "source": getattr(obj, rel_a).pk,
            "target": getattr(obj, rel_b).pk,
            "id": obj.pk,
            "type": "arrow",
            "data": dict(),
        }
        r["data"]["start_date"] = obj.start_date_written
        r["data"]["end_date"] = obj.end_date_written
        r["data"]["relation_type"] = obj.relation_type.name

        return r


class NetJsonNodeSerializer(serializers.BaseSerializer):
    def to_representation(self, obj):
        ent_obj = obj.__class__.__name__
        ent_url = reverse_lazy(
            "apis:apis_entities:generic_entities_edit_view",
            kwargs={"pk": str(obj.pk), "entity": ent_obj.lower()},
        )
        tt = """<div class='arrow'></div>
            <div class='sigma-tooltip-header'>{}</div>
            <div class='sigma-tooltip-body'>
            <table>
                <tr><th>Type</th> <td>{}</td></tr>
                <tr><th>Entity</th> <td><a href='{}'>Link</a></td></tr>
            </table>
            <button class='small-button' onclick='expand_node("{}", {})'>expand</button>
            </div>""".format(
            str(obj), ent_obj, ent_url, ent_obj, obj.pk
        )
        r = {
            "type": ent_obj.lower(),
            "label": str(obj),
            "id": obj.pk,
            "tooltip": tt,
            "data": dict(),
        }
        r["data"]["uri"] = [x.uri for x in obj.uri_set.all()]
        r["data"]["collections"] = [x.name for x in obj.collection.all()]
        r["data"]["notes"] = obj.notes
        r["data"]["references"] = obj.references
        r["data"]["start_date"] = obj.start_date_written
        r["data"]["end_date"] = obj.end_date_written
        if ent_obj.lower() != "person":
            if obj.kind:
                r["data"]["kind"] = obj.kind.name
        if ent_obj.lower() == "place":
            r["data"]["lat"] = obj.lat
            r["data"]["lon"] = obj.lng
        if ent_obj.lower() == "person":
            r["data"]["profession"] = [x.name for x in obj.profession.all()]
            if obj.gender:
                r["data"]["gender"] = obj.gender
        return r


class LifePathPlaceSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    name = serializers.CharField()
    lat = serializers.FloatField()
    long = serializers.FloatField(source="lng")

    class Meta:
        fields = ["id", "name", "lat", "long"]
        model = Place


class LifePathSerializer(serializers.BaseSerializer):
    place = serializers.SerializerMethodField(method_name="get_place")
    year = serializers.SerializerMethodField(method_name="get_year")
    relation_type = serializers.CharField(source="relation_type__name")

    def get_place(self, obj):
        if isinstance(obj, PersonInstitution):
            inst = obj.related_institution
            rel_type = getattr(settings, "APIS_LOCATED_IN_ATTR", ["situated in",])
            rel_type_inst = getattr(settings, "APIS_INSTITUTION_PRECEEDING", [160, 161])
            ipl_rel = InstitutionPlaceRelation.objects.filter(
                name__in=rel_type
            ).values_list("pk", flat=True)
            plc = InstitutionPlace.objects.filter(
                relation_type_id__in=ipl_rel, related_institution=inst
            )
            if plc.count() == 0:
                inst_lst1 = [
                    x.related_institutionA
                    for x in inst.related_institutionA.filter(
                        relation_type_id__in=rel_type_inst
                    )
                ]
                inst_lst1.extend(
                    [
                        x.related_institutionB
                        for x in inst.related_institutionB.filter(
                            relation_type_id__in=rel_type_inst
                        )
                    ]
                )
                for i2 in inst_lst1:
                    plc = InstitutionPlace.objects.filter(
                        relation_type_id__in=ipl_rel, related_institution=i2
                    )
                    if plc.count() == 1:
                        if plc[0].related_place.lat:
                            break
            if plc.count() == 1:
                plc = plc.first().related_place
                if plc.lng and plc.lat:
                    return LifePathPlaceSerializer(plc).data
        elif isinstance(obj, PersonPlace):
            plc = obj.related_place
            if plc.lat and plc.lng:
                return LifePathPlaceSerializer(plc).data

    def get_year(self, obj):
        if not obj.start_date and not obj.end_date:
            return None
        if obj.start_date and obj.end_date:
            start = int(obj.start_date.strftime("%Y"))
            end = int(obj.end_date.strftime("%Y"))
            return int((start + end) / 2)
        elif obj.start_date:
            return int(obj.start_date.strftime("%Y"))
        elif obj.end_date:
            return int(obj.end_date.strftime("%Y"))

    def to_representation(self, instance):
        p = self.get_place(instance)
        if p is None:
            return None
        res = {
            "id": instance.pk,
            "coords": [p["lat"], p["long"]],
            "name": p["name"],
            "year": self.get_year(instance),
            "relation_type": str(instance.relation_type),
        }
        return res
