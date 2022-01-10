import lxml.etree as ET
from django.conf import settings
from django.template.loader import get_template
from apis_core.apis_entities.models import Work, Place, Person, Institution
from apis_core.apis_relations.models import PlacePlace, PersonWork
from apis_core.apis_vocabularies.models import PersonWorkRelation
from apis_core.helper_functions.utils import get_child_classes 

try:
    birth_rel = settings.BIRTH_REL
except AttributeError:
    birth_rel = False
try:
    death_rel = settings.DEATH_REL
except AttributeError:
    death_rel = False
try:
    pl_a_part_of = settings.PL_A_PART_OF
except AttributeError:
    pl_a_part_of = False
try:
    pl_b_located_in = settings.PL_B_LOCATED_IN
except AttributeError:
    pl_b_located_in = False
try:
    org_located_in = settings.ORG_LOCATED_IN
except AttributeError:
    org_located_in = False
try:
    author_rels = settings.AUTHOR_RELS
except AttributeError:
    author_rels = False

if author_rels:
    author_rels = get_child_classes(author_rels, PersonWorkRelation, labels=False)
else:
    author_rels = False

def get_part_of_relation(res):
    items = []
    for x in PlacePlace.objects.filter(related_placeB=res).filter(relation_type__id__in=pl_b_located_in):
        items.append(x.related_placeA)
    for x in PlacePlace.objects.filter(related_placeA=res).filter(relation_type__id__in=pl_a_part_of):
        items.append(x.related_placeB)
    return list(set(items))

def get_context(res):
    
    context = {}
    context['object'] = res
    context['org_located_in'] = []
    context['birth_rel'] = []
    context['death_rel'] = []
    context['pl_located_in'] = []
    context['author_rels'] = []
    if isinstance(res, Work):
        person_work_ids = get_child_classes(author_rels, PersonWorkRelation, labels=False)
        try:
            context['author_rels'] = PersonWork.objects.filter(relation_type__in=person_work_ids, related_work=res)
        except ValueError:
            context['author_rels'] = []
    if org_located_in and isinstance(res, Institution):
        try:
            context['org_located_in'] = res.institutionplace_set.filter(relation_type__in=org_located_in)
        except AttributeError:
            pass
    if isinstance(res, Person):
        if birth_rel:
            try:
                context['birth_rel'] = res.personplace_set.filter(relation_type__in=birth_rel)
            except AttributeError:
                pass
        if death_rel:
            try:
                context['death_rel'] = res.personplace_set.filter(relation_type__in=death_rel)
            except AttributeError:
                pass
    if isinstance(res, Place):
        if pl_a_part_of and pl_b_located_in:
            try:
                context['pl_located_in'] = get_part_of_relation(res)
            except ValueError:
                pass
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