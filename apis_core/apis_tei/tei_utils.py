import lxml.etree as ET
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.template.loader import get_template

Person = ContentType.objects.get(
    app_label='apis_entities', model='person'
).model_class()

TEMPLATE_PATH = 'apis_tei/person.xml'

try:
    birth_rel = settings.BIRTH_REL
except ImportError:
    birth_rel = False

try:
    death_rel = settings.DEATH_REL
except ImportError:
    death_rel = False


def get_context(res):
    context = {}
    context['object'] = res
    if birth_rel:
        context['birth_rel'] = res.personplace_set.filter(relation_type__in=birth_rel)
    else:
        context['birth_rel'] = []
    if death_rel:
        context['death_rel'] = res.personplace_set.filter(relation_type=death_rel)
    else:
        context['death_rel'] = []
    return context


def get_node_from_template(template_path, res, full=True):
    template = get_template(template_path)
    context = get_context(res)
    context['FULL'] = full
    temp_str = f"{template.render(context=context)}"
    node = ET.fromstring(temp_str)
    return node


def tei_header(
    title="ListPerson",
    ent_type="<listPerson/>",
    template_path='apis_tei/tei.xml'
):
    template = get_template(template_path)
    context = {
        "title": title,
        "ent_type": ent_type
    }
    temp_str = f"{template.render(context=context)}"
    node = ET.fromstring(temp_str)
    return node