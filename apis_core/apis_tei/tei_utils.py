from apis.settings.local_pmb import BIRTH_REL
import lxml.etree as ET
from django.conf import settings
from django.template.loader import get_template

try:
    birth_rel = settings.BIRTH_REL
except ImportError:
    birth_rel = False

try:
    death_rel = settings.BIRTH_REL
except ImportError:
    death_rel = False


TEMPLATE_PERSON = get_template('apis_tei/person.xml')

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


def get_node_from_template(template_path, res):
        template = get_template(template_path)
        context = get_context(res)
        temp_str = f"{template.render(context=context)}"
        node = ET.fromstring(temp_str)
        return node