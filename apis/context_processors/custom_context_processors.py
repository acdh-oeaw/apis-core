from django.contrib.contenttypes.models import ContentType


def add_entities(request):
    res = {
        'entities_list': [x.name for x in ContentType.objects.filter(app_label='entities')],
        'request': request
    }
    return res
