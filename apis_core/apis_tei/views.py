import lxml.etree as ET

from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from apis_core.apis_entities.models import Person, Place, Institution
from .tei_utils import get_node_from_template


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


def org_as_tei(request, pk):
    full = request.GET.get('full')
    res = get_object_or_404(Institution, pk=pk)
    doc = get_node_from_template('apis_tei/org.xml', res, full=full)
    tei = ET.tostring(doc, pretty_print=True, encoding='UTF-8')
    return HttpResponse(tei, content_type="application/xml")


