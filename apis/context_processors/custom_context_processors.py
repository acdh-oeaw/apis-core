from django.conf import settings
import sys, inspect


def add_entities(request):
    ent_list = []
    for name, obj in inspect.getmembers(sys.modules['entities.models'], inspect.isclass):
        if obj.__module__ == 'entities.models':
            ent_list.append(str(name).lower())
    res = {
        'entities_list': ent_list,
        'request': request
    }
    return res


def add_apis_settings(request):
    res = {
        'additional_functions': getattr(settings, "APIS_COMPONENTS", []),
        'request': request
    }
    return res
