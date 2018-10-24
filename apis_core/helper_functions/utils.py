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
