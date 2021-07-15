import lxml.etree as ET

from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from .tei_utils import get_node_from_template, Person, TEMPLATE_PATH


def person_as_tei(request, pk):
    full = request.GET.get('full')
    res = get_object_or_404(Person, pk=pk)
    doc = get_node_from_template(TEMPLATE_PATH, res, full=full)
    tei = ET.tostring(doc, pretty_print=True, encoding='UTF-8')
    return HttpResponse(tei, content_type="application/xml")


