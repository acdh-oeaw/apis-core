from django.conf import settings


def access_for_all(self, viewtype="list"):
    if self.request.user.is_authenticated:
        return self.request.user.is_authenticated
    elif viewtype == "list":
        try:
            access = settings.APIS_LIST_VIEWS_ALLOWED
        except AttributeError:
            access = False
            return access
        return access
    else:
        try:
            access = settings.APIS_DETAIL_VIEWS_ALLOWED
        except AttributeError:
            access = False
            return access
        return access


def access_for_all_function(user):
    if user.is_anonymous:
        print(getattr(settings, 'APIS_DETAIL_VIEWS_ALLOWED', False))
        return getattr(settings, 'APIS_DETAIL_VIEWS_ALLOWED', False)
    else:
        return True


ENTITIES_DEFAULT_COLS = [
    'start_date',
    'start_date_written',
    'end_date',
    'end_date_written',
    'text',
    'collection',
    'status',
    'source',
    'references',
    'notes',
]

def get_child_classes(objids, obclass, labels=False):
    """used to retrieve a list of primary keys of sub classes"""
    if labels:
        labels_lst = []
    for obj in objids:
        obj = obclass.objects.get(pk=obj)
        p_class = list(obj.vocabsbaseclass_set.all())
        p = p_class.pop() if len(p_class) > 0 else False
        while p:
            if p.pk not in objids:
                if labels:
                    labels_lst.append((p.pk, p.label))
                objids.append(p.pk)
            p_class += list(p.vocabsbaseclass_set.all())
            p = p_class.pop() if len(p_class) > 0 else False
    if labels:
        return (objids, labels_lst)
    else:
        return objids
