import re
from collections import OrderedDict

from rest_framework import renderers


class NetJsonRenderer(renderers.JSONRenderer):
    media_type = "application/json"
    format = "json+net"

    def render(self, data, media_type=None, renderer_context=None):
        try:
            test = re.search(r"/relations/([^/]+)/", data["results"][0]["url"])
        except IndexError:
            return super().render(
                data, accepted_media_type=media_type, renderer_context=renderer_context
            )
        if test:
            rel = test.group(1)
            for r in data["results"][0].keys():
                if r.startswith("related_"):
                    r2 = r.split("_")[1]
                    rel2 = re.match("^{}[a-z]*".format(r2), rel)
                    if rel2:
                        source = r
                    elif r.endswith('A'):
                        source = r
                    elif r.endswith('B'):
                        target = r
                    rel2 = re.match("^[a-z]*?{}$".format(r2), rel)
                    if rel2:
                        target = r
            results2 = []
            for d in data["results"]:
                d2 = OrderedDict(
                    [
                        ("target", v)
                        if k == target
                        else ("source", v)
                        if k == source
                        else (k, v)
                        for k, v in d.items()
                    ]
                )
                results2.append(d2)
            data["results"] = results2
            res3 = super().render(data, accepted_media_type=media_type, renderer_context=renderer_context)
            return res3
