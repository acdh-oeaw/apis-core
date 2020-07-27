from django.template.loader import render_to_string
from rest_framework import renderers
from rest_framework_csv.renderers import CSVRenderer


class TEIBaseRenderer(renderers.BaseRenderer):
    media_type = 'application/xml+tei'
    format = 'xml'

    def render(self, data, media_type=None, renderer_context=None):
        data = render_to_string("apis_metainfo/TEI_renderer.xml", {'data': data, 'renderer_context': renderer_context})

        return data


class PaginatedCSVRenderer(CSVRenderer):
    results_field = 'results'

    def render(self, data, *args, **kwargs):
        if not isinstance(data, list):
            data = data.get(self.results_field, [])
        return super(PaginatedCSVRenderer, self).render(data, *args, **kwargs)
