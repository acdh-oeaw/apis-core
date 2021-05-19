import fnmatch
import os
import re
from datetime import datetime
from io import TextIOWrapper

import requests
from django.conf import settings
from django.db.models import Q, Prefetch
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import api_view
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import DjangoObjectPermissions
from rest_framework.response import Response
from rest_framework.reverse import reverse_lazy
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from apis_core.apis_metainfo.api_renderers import PaginatedCSVRenderer
from apis_core.apis_metainfo.models import TempEntityClass, Uri
from apis_core.apis_relations.models import (
    PersonPlace,
    InstitutionPlace,
    AbstractRelation,
    PersonInstitution,
)
from apis_core.apis_vocabularies.models import (
    VocabsBaseClass,
    PersonPlaceRelation,
    InstitutionPlaceRelation,
)
from apis_core.default_settings.NER_settings import autocomp_settings, stb_base
from apis_core.helper_functions.RDFParser import RDFParser
from apis_core.helper_functions.stanbolQueries import find_loc
from .api_renderers import (
    EntityToTEI,
    EntityToCIDOCXML,
    EntityToProsopogrAPhI,
    EntityToCIDOCN3,
    EntityToCIDOCNQUADS,
    EntityToCIDOCTURTLE,
)
from .models import Event, Institution, Person, Place, Work, AbstractEntity
from .serializers import (
    EventSerializer,
    GeoJsonSerializer,
    InstitutionSerializer,
    NetJsonEdgeSerializer,
    NetJsonNodeSerializer,
    PersonSerializer,
    PlaceSerializer,
    WorkSerializer,
    GeoJsonSerializerTheme,
    LifePathSerializer,
)
from .serializers_generic import EntitySerializer


# from metainfo.models import TempEntityClass


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 1000


class GetEntityGeneric(GenericAPIView):
    serializer_class = EntitySerializer
    queryset = TempEntityClass.objects.all()
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (
        EntityToTEI,
        EntityToCIDOCXML,
        EntityToProsopogrAPhI,
        EntityToCIDOCN3,
        EntityToCIDOCNQUADS,
        EntityToCIDOCTURTLE,
    )
    if getattr(settings, "APIS_RENDERERS", None) is not None:
        rend_add = tuple()
        for rd in settings.APIS_RENDERERS:
            rend_mod = __import__(rd)
            for name, cls in rend_mod.__dict__.items():
                rend_add + (cls,)
        renderer_classes += rend_add

    def get_object(self, pk, request):
        try:
            return TempEntityClass.objects_inheritance.get_subclass(pk=pk)
        except TempEntityClass.DoesNotExist:
            uri2 = Uri.objects.filter(uri=request.build_absolute_uri())
            if uri2.count() == 1:
                return TempEntityClass.objects_inheritance.get_subclass(
                    pk=uri2[0].entity_id
                )
            else:
                raise Http404

    def get(self, request, pk):
        ent = self.get_object(pk, request)
        res = EntitySerializer(ent, context={"request": request})
        return Response(res.data)


@api_view(["GET"])
def uri_resolver(request):
    uri = request.query_params.get("uri", None)
    f = request.query_params.get("target_format", "gui")
    if uri is None:
        raise Http404
    else:
        uri = Uri.objects.get(uri=uri)
        if f == "gui":
            ent = TempEntityClass.objects_inheritance.get_subclass(pk=uri.entity_id)
            c_name = ent.__class__.__name__
            url = reverse(
                "apis_core:apis_entities:generic_entities_detail_view",
                kwargs={"pk": uri.entity_id, "entity": c_name.lower()},
            )
        else:
            url = reverse(
                "apis_core:apis_api2:GetEntityGeneric", kwargs={"pk": uri.entity_id}
            ) + "?format={}".format(f)
        return redirect(url)


class InstitutionViewSet(viewsets.ModelViewSet):
    """Serialization of the institution class.
    In addition to the institution this view includes related texts and \
    the kind of the institution (separated object)."""

    permission_classes = (DjangoObjectPermissions,)
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    depth = 2
    filter_fields = ("name", "kind__name", "collection__name")
    search_fields = ("name",)


class PersonViewSet(viewsets.ModelViewSet):
    """Serialization of the Person class.
    In addition to the person this view includes related texts (e.g. biographies), \
    a list of professions (separated objects) and the collection it belongs to."""

    permission_classes = (DjangoObjectPermissions,)
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    depth = 2
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filter_fields = (
        "name",
        "first_name",
        "gender",
        "profession__name",
        "collection__name",
        "uri__uri",
    )
    search_fields = ("name", "first_name")


class PlaceViewSet(viewsets.ModelViewSet):
    """Serialization of the Place class.
    In addition to the place this view includes related texts (e.g. from the ÖBL database), \
     and the collection it belongs to."""

    permission_classes = (DjangoObjectPermissions,)
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    depth = 2
    filter_fields = ("name", "kind__name", "collection__name")
    search_fields = ("name",)
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (
        PaginatedCSVRenderer,
    )


class EventViewSet(viewsets.ModelViewSet):
    """Serialization of the event class.
    In addition to the event this view includes related texts and
    the kind of the event (separated object)."""

    permission_classes = (DjangoObjectPermissions,)
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    depth = 2
    filter_fields = ("name", "kind__name", "collection__name")
    search_fields = ("name",)


class WorkViewSet(viewsets.ModelViewSet):
    """Serialization of the work class.
    In addition to the work this view includes related texts and
    the kind of the work (separated object)."""

    permission_classes = (DjangoObjectPermissions,)
    queryset = Work.objects.all()
    serializer_class = WorkSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    depth = 2
    filter_fields = ("name", "kind__name", "collection__name")
    search_fields = ("name",)


class PlaceGeoJsonViewSet(viewsets.ViewSet):
    def list(self, request):
        queryset = request.query_params.get("q", None)
        diff = re.match(r"^([^\[]*)\[(\d+)\]", queryset)
        match_url = re.search(r"geonames[^0-9]+([0-9]+)", queryset)
        res = False
        if match_url:
            for u in autocomp_settings["Place"]:
                if "url" in u.keys():
                    site = re.search("site/([^/]+)/", u["url"])
                    if site:
                        params = {
                            "id": "http://sws.geonames.org/{}/".format(
                                match_url.group(1)
                            )
                        }
                        headers = {"Content-Type": "application/json"}
                        w = requests.get(
                            stb_base + site.group(1) + "/entity",
                            params=params,
                            headers=headers,
                        )
                        if w.status_code == 200:
                            if "representation" in w.json().keys():
                                res = [True, w.json()["representation"]]
                                break
        elif diff and queryset:
            queryset = diff.group(1)
            res = find_loc(queryset.split(","), dec_diff=int(diff.group(2)))
        elif queryset:
            res = find_loc(queryset.split(","))
        else:
            res = False, False
        if res[1]:
            if type(res[1]) is not list:
                res = (res[0], [res[1]])
            serializer = GeoJsonSerializer(
                res[1],
                many=True,
                context={"p_pk": request.query_params.get("p_pk", None)},
            )
        else:
            serializer = GeoJsonSerializer(
                [], many=True, context={"p_pk": request.query_params.get("p_pk", None)}
            )
        return Response(serializer.data)


class NetJsonViewSet(viewsets.GenericViewSet):
    def get_queryset(self):
        rel = self.request.data["select_relation"]
        q = AbstractRelation.get_relation_class_of_name("".join(rel.split("-")))
        return q.objects.all()

    def create(self, request):
        rel = request.data["select_relation"]
        if "select_kind" in request.data.keys():
            kind = request.data["select_kind"]
        else:
            kind = None
        if "annotation_proj" in request.data.keys():
            annotation_proj = request.data["annotation_proj"]
        else:
            annotation_proj = None
        if "ann_include_all" in request.data.keys():
            ann_include_all = True
        else:
            ann_include_all = False
        q = AbstractRelation.get_relation_class_of_name("".join(rel.split("-")))
        rel_match = re.match(r"([A-Z][a-z]+)([A-Z][a-z]+$)", rel)
        lst_nodes = []
        rel_a = "related_" + rel.split("-")[0]
        rel_b = "related_" + rel.split("-")[1]
        q_dict = {}
        q_list = None
        if rel_a == rel_b:
            rel_a += "A"
            rel_b += "B"
        if "search_source" in request.data.keys():
            source = request.data["search_source"]
            if source.startswith("cl:"):
                if q_list is not None:
                    q_list.append(
                        Q(**{rel_a + "__collection__id": int(source[3:])})
                        | Q(**{rel_b + "__collection__id": int(source[3:])})
                    )
                else:
                    q_dict[rel_a + "__collection__id"] = int(source[3:])
            else:
                if q_list is not None:
                    q_list.append(
                        Q(**{rel_a + "_id": int(source)})
                        | Q(**{rel_b + "_id": int(source)})
                    )
                else:
                    q_dict[rel_a + "_id"] = int(source)
        elif "search_source-autocomplete" in request.data.keys():
            source = request.data["search_source-autocomplete"]
            if q_list is not None:
                q_list.append(
                    Q(**{rel_a + "__name__icontains": source})
                    | Q(**{rel_b + "__name__icontains": source})
                )
            else:
                q_dict[rel_a + "__name__icontains"] = source
        if "search_target" in request.data.keys():
            target = request.data["search_target"]
            if target.startswith("cl:"):
                if q_list is not None:
                    q_list.append(
                        Q(**{rel_b + "__collection__id": int(target[3:])})
                        | Q(**{rel_a + "__collection__id": int(target[3:])})
                    )
                else:
                    q_dict[rel_b + "__collection__id"] = int(target[3:])
            else:
                if q_list is not None:
                    q_list.append(
                        Q(**{rel_a + "_id": int(target)})
                        | Q(**{rel_b + "_id": int(target)})
                    )
                else:
                    q_dict[rel_b + "_id"] = target
        elif "search_target-autocomplete" in request.data.keys():
            if len(request.data["search_target-autocomplete"]) > 0:
                target = request.data["search_target-autocomplete"]
                if q_list is not None:
                    q_list.append(
                        Q(**{rel_a + "__name__icontains": target})
                        | Q(**{rel_b + "__name__icontains": target})
                    )
                else:
                    q_dict[rel_b + "__name__icontains"] = target
        if kind:
            kind_ids = [int(kind.strip())]
            kind_ids_res = [int(kind.strip())]
            while len(kind_ids) > 0:
                id_a = kind_ids.pop()
                ids_b = VocabsBaseClass.objects.filter(
                    parent_class_id=id_a
                ).values_list("pk", flat=True)
                kind_ids.extend(ids_b)
                kind_ids_res.extend(ids_b)
            q_dict["relation_type_id__in"] = kind_ids_res
        if "start_date" in request.data.keys():
            if len(request.data["start_date"]) > 0:
                start_date_d = datetime.strptime(request.data["start_date"], "%d.%m.%Y")
                q_dict["end_date__gte"] = start_date_d
        if "end_date" in request.data.keys():
            if len(request.data["end_date"]) > 0:
                end_date_d = datetime.strptime(request.data["end_date"], "%d.%m.%Y")
                q_dict["start_date__lte"] = end_date_d
        if annotation_proj:
            annProj_filter = {"ann_proj": annotation_proj}
            if not ann_include_all:
                annProj_filter["include_all"] = False
            sr1 = (
                q.annotation_links.filter_ann_proj(**annProj_filter)
                .filter(**q_dict)
                .select_related(rel_a, rel_b)
            )
        else:
            sr1 = q.objects.filter(**q_dict)
        if q_list is not None:
            sr1 = sr1.filter(q_list[0])
        for node in sr1:
            if getattr(node, rel_a) not in lst_nodes:
                lst_nodes.append(getattr(node, rel_a))
            if getattr(node, rel_b) not in lst_nodes:
                lst_nodes.append(getattr(node, rel_b))
        sr1_1 = NetJsonEdgeSerializer(sr1, many=True)
        sr1_2 = NetJsonNodeSerializer(lst_nodes, many=True)
        res = {"nodes": sr1_2.data, "edges": sr1_1.data}
        return Response(res)


class SaveNetworkFiles(APIView):
    def post(self, request, format=None):
        file_name = request.data["file_name"]
        file_name_list = file_name.split(".")
        data = request.data["file"]
        nmb = False
        for file in os.listdir("downloads/"):
            if (
                fnmatch.fnmatch(file, file_name_list[0] + "_*." + file_name_list[1])
                or file == file_name
            ):
                if nmb:
                    nmb += 1
                else:
                    nmb = 1
        if nmb:
            file_name = file_name_list[0] + "_" + str(nmb) + "." + file_name_list[1]
        with open("downloads/" + file_name, "wb") as fw:
            data = data.replace('"edges"', '"links"', 1)
            fw.write(data.encode("utf-8"))
        res = {"test": True, "file_name": "/downloads/" + file_name}
        return Response(res)


class ResolveAbbreviations(APIView):
    parser_classes = (FileUploadParser,)

    def put(self, request, filename, format=None):
        file_obj = request.data["file"]
        txt = TextIOWrapper(file_obj, encoding="utf8")
        return Response(status=204)


class GetOrCreateEntity(APIView):
    def get(self, request):
        entity = request.query_params.get("entity2", None)
        uri = request.query_params.get("uri", None)
        if uri.startswith("http:"):
            ent = RDFParser(uri, entity.title()).get_or_create()
        else:
            r1 = re.search(r"^[^<]+", uri)
            r2 = re.search(r"<([^>]+)>", uri)
            q_d = dict()
            q_d["name"] = r1
            if r2:
                for x in r2.group(1).split(";"):
                    x2 = x.split("=")
                    q_d[x2[0].strip()] = x2[1].strip()
            if entity == "person":
                r1_2 = r1.group(0).split(",")
                if len(r1_2) == 2:
                    q_d["first_name"] = r1_2[1].strip()
                    q_d["name"] = r1_2[0].strip()
            ent = AbstractEntity.get_entity_class_of_name(entity).objects.create(**q_d)
        res = {
            "id": ent.pk,
            "url": reverse_lazy(
                "apis:apis_entities:generic_entities_edit_view",
                request=request,
                kwargs={"pk": ent.pk, "entity": entity},
            ),
        }
        return Response(res)


class GetRelatedPlaces(APIView):
    # map_qs = {
    #   'institution': Prefetch('personinstitution_set__related_institution__institutionplace_set', queryset=InstitutionPlace.objects.select_related('related_place'))
    # }

    def get(self, request):
        b_rel = PersonPlaceRelation.objects.get(
            name=getattr(settings, "BIRTH_REL_NAME", "")
        )
        d_rel = PersonPlaceRelation.objects.get(
            name=getattr(settings, "DEATH_REL_NAME", "")
        )
        person_pk = request.query_params.get("person_id", None)
        pers = Person.objects.get(pk=person_pk)
        relation_types = request.query_params.get("relation_types", None)
        place_pk = dict()
        res = []
        p = (
            PersonPlace.objects.select_related("related_place")
            .filter(related_person_id=person_pk, related_place__lat__isnull=False)
            .filter_for_user()
        )
        for pp in p:
            if pp.related_place_id not in place_pk:
                res.append(
                    (
                        pp.related_place,
                        [
                            (
                                pp.relation_type,
                                None,
                                pers.start_date
                                if b_rel.pk == pp.relation_type_id
                                else pp.start_date,
                                pers.end_date
                                if d_rel.pk == pp.relation_type_id
                                else pp.end_date,
                                pp,
                            )
                        ],
                    )
                )
                place_pk[pp.related_place_id] = len(res) - 1
            else:
                res[place_pk[pp.related_place_id]][1].append(
                    (
                        pp.relation_type,
                        None,
                        pers.start_date
                        if b_rel.pk == pp.relation_type_id
                        else pp.start_date,
                        pers.end_date
                        if d_rel.pk == pp.relation_type_id
                        else pp.end_date,
                        pp,
                    )
                )
        for pi in PersonInstitution.objects.filter(
            related_person_id=person_pk
        ).filter_for_user():
            inst = pi.related_institution
            rel_type = getattr(
                settings,
                "APIS_LOCATED_IN_ATTR",
                [
                    "situated in",
                ],
            )
            ipl_rel = InstitutionPlaceRelation.objects.filter(
                name__in=rel_type
            ).values_list("pk", flat=True)
            plc = InstitutionPlace.objects.filter(
                relation_type_id__in=ipl_rel, related_institution=inst
            )
            if plc.count() == 1:
                if plc[0].related_place_id not in place_pk:
                    res.append(
                        (
                            plc[0].related_place,
                            [
                                (
                                    pi.relation_type,
                                    pi.related_institution,
                                    pi.start_date,
                                    pi.end_date,
                                    pi,
                                )
                            ],
                        )
                    )
                    place_pk[plc[0].related_place_id] = len(res) - 1
                else:
                    res[place_pk[plc[0].related_place_id]][1].append(
                        (
                            pi.relation_type,
                            pi.related_institution,
                            pi.start_date,
                            pi.end_date,
                            pi,
                        )
                    )
        res = GeoJsonSerializerTheme(res, many=True)
        return Response(res.data)


class LifePathViewset(APIView):
    def get(self, request, pk):
        b_rel = PersonPlaceRelation.objects.get(
            name=getattr(settings, "BIRTH_REL_NAME", "")
        )
        d_rel = PersonPlaceRelation.objects.get(
            name=getattr(settings, "DEATH_REL_NAME", "")
        )
        pb_pd = [b_rel.pk, d_rel.pk]
        lst_inst = list(
            PersonInstitution.objects.filter(
                Q(related_person_id=pk),
                Q(start_date__isnull=False) | Q(end_date__isnull=False),
            ).filter_for_user()
        )
        lst_place = list(
            PersonPlace.objects.filter(
                Q(related_person_id=pk),
                Q(start_date__isnull=False)
                | Q(end_date__isnull=False)
                | Q(relation_type_id__in=pb_pd),
            ).filter_for_user()
        )
        comb_lst = lst_inst + lst_place
        p1 = Person.objects.get(pk=pk)
        if p1.start_date:
            for e in comb_lst:
                if e.relation_type_id == b_rel.pk:
                    e.start_date = p1.start_date
        if p1.end_date:
            for e in comb_lst:
                if e.relation_type_id == d_rel.pk:
                    e.start_date = p1.end_date
        data = LifePathSerializer(comb_lst, many=True).data
        data = [d for d in data if d is not None]
        data = sorted(data, key=lambda i: i["year"])

        return Response(data)
