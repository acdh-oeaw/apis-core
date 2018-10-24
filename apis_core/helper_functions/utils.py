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
    else:
        try:
            access = settings.APIS_DETAILKJL_VIEWS_ALLOWED
        except AttributeError:
            access = False
        return access
