from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView

from browsing.browsing_utils import GenericListView, BaseCreateView, BaseUpdateView
from .filters import UriListFilter
from .forms import UriFilterFormHelper, UriForm
from .models import Uri
from .tables import UriTable


PROJECT_NAME = settings.PROJECT_NAME


def beacon(request):
    domain = request.build_absolute_uri("/")
    result = f"#FORMAT: BEACON\n#NAME: {PROJECT_NAME}\n"
    uris = [(x.uri, x.entity.name, x.entity.id) for x in Uri.objects.filter(uri__icontains='d-nb.info/gnd')]
    for x in uris:
        result = result + f"{x[0]}|"f"{x[1]}|"f"{domain}entity/{x[2]}/\n"
    return HttpResponse(result, content_type="text/plain")


class UriListView(GenericListView):
    model = Uri
    filter_class = UriListFilter
    formhelper_class = UriFilterFormHelper
    table_class = UriTable
    init_columns = [
        'id',
        'uri',
        'entity',
    ]
    enable_merge = True


class UriDetailView(DetailView):
    model = Uri
    template_name = 'apis_metainfo/uri_detail.html'


class UriCreate(BaseCreateView):

    model = Uri
    form_class = UriForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UriCreate, self).dispatch(*args, **kwargs)


class UriUpdate(BaseUpdateView):

    model = Uri
    form_class = UriForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UriUpdate, self).dispatch(*args, **kwargs)


class UriDelete(DeleteView):
    model = Uri
    template_name = 'webpage/confirm_delete.html'
    success_url = reverse_lazy('apis_core:apis_metainfo:uri_browse')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UriDelete, self).dispatch(*args, **kwargs)
