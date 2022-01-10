import inspect
import sys

from django.conf import settings


def add_entities(request):
    ent_list = []
    for name, obj in inspect.getmembers(
        sys.modules['apis_core.apis_entities.models'], inspect.isclass
    ):
        if obj.__module__ == 'apis_core.apis_entities.models' and name != "AbstractEntity" and name != "ent_class":
            ent_list.append(str(name).lower())
    res = {
        'entities_list': ent_list,
        'request': request
    }
    return res


def add_relations(request):
    relations_list = []
    for name, obj in inspect.getmembers(
        sys.modules['apis_core.apis_relations.models'], inspect.isclass
    ):
        if obj.__module__ == 'apis_core.apis_relations.models' and name not in ["AbstractRelation", "AnnotationRelationLinkManager", "ent_class", "BaseRelationManager", "RelationPublishedQueryset"]:
            relations_list.append(str(name).lower())
    res = {
        'relations_list': relations_list,
        'request': request
    }
    return res


def add_apis_settings(request):
    """adds the custom settings to the templates"""
    res = {
        'additional_functions': getattr(settings, "APIS_COMPONENTS", []),
        'request': request
    }
    if 'apis_highlighter' in settings.INSTALLED_APPS:
        res['highlighter_active'] = True
    else:
        res['highlighter_active'] = False
    if 'apis_bibsonomy' in settings.INSTALLED_APPS:
        res['bibsonomy_active'] = True
    else:
        res['bibsonomy_active'] = False
    return res
