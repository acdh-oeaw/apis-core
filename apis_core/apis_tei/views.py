import lxml.etree as ET

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect

from apis_core.apis_entities.models import Person, Place, Institution, Work
from .tei_utils import get_node_from_template
from apis_core.apis_metainfo.models import Uri


def person_as_tei(request, pk):
    full = request.GET.get('full')
    res = get_object_or_404(Person, pk=pk)
    doc = get_node_from_template('apis_tei/person.xml', res, full=full)
    tei = ET.tostring(doc, pretty_print=True, encoding='UTF-8')
    return HttpResponse(tei, content_type="application/xml")


def place_as_tei(request, pk):
    full = request.GET.get('full')
    res = get_object_or_404(Place, pk=pk)
    doc = get_node_from_template('apis_tei/place.xml', res, full=full)
    tei = ET.tostring(doc, pretty_print=True, encoding='UTF-8')
    return HttpResponse(tei, content_type="application/xml")


def work_as_tei(request, pk):
    full = request.GET.get('full')
    res = get_object_or_404(Work, pk=pk)
    doc = get_node_from_template('apis_tei/work.xml', res, full=full)
    tei = ET.tostring(doc, pretty_print=True, encoding='UTF-8')
    return HttpResponse(tei, content_type="application/xml")


def org_as_tei(request, pk):
    full = request.GET.get('full')
    res = get_object_or_404(Institution, pk=pk)
    doc = get_node_from_template('apis_tei/org.xml', res, full=full)
    tei = ET.tostring(doc, pretty_print=True, encoding='UTF-8')
    return HttpResponse(tei, content_type="application/xml")


def uri_to_tei(request):
    requested_uri = request.GET.get('uri', None)
    if requested_uri is not None:
        uri = get_object_or_404(Uri, uri=requested_uri)
        uri_entity_id = uri.entity.id
        uri_entity_class = uri.entity.get_child_entity()
        uri_entity_class_name = uri_entity_class.__class__.__name__.lower()
        redirect_url = f'/apis/entities/tei/{uri_entity_class_name}/{uri_entity_id}'
        return redirect(redirect_url)
    else:
        return HttpResponse(f"no URI provided, please try e.g. uri-to-tei?uri=https://whatever.you/want", content_type="text/plain")
