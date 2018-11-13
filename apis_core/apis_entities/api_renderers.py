from rest_framework import renderers
from apis_core.apis_tei.tei import TeiEntCreator


class EntityToTEI(renderers.BaseRenderer):

    media_type = "text/xml"
    format = 'tei'

    def render(self, data, media_type=None, renderer_context=None):
        tei_doc = TeiEntCreator(data)
        return tei_doc.serialize_full_doc()
