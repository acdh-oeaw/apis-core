import lxml.etree as ET

from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from .tei_utils import get_node_from_template

Person = ContentType.objects.get(
    app_label='apis_entities', model='person'
).model_class()


def person_as_tei(request, pk):
    full = request.GET.get('full')
    res = get_object_or_404(Person, pk=pk)
    template_path = 'apis_tei/person.xml'
    doc = get_node_from_template(template_path, res, full=full)
    tei = ET.tostring(doc, pretty_print=True, encoding='UTF-8')
    return HttpResponse(tei, content_type="application/xml")


