from django.contrib.contenttypes.models import ContentType
from django.conf import settings


def add_entities(request):
    res = {
        'entities_list': [x.name for x in ContentType.objects.filter(app_label='entities')],
        'request': request
    }
    return res


def add_apis_settings(request):
    res = {
        'additional_functions': getattr(settings, "APIS_COMPONENTS", []),
        'request': request
    }
    return res
