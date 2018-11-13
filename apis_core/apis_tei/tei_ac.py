import json

from dal import autocomplete

from django import http
from django.contrib.contenttypes.models import ContentType


class TeiEntAc(autocomplete.Select2ListView):

    def get(self, request, *args, **kwargs):
        page_size = 200
        offset = (int(self.request.GET.get('page', 1))-1)*page_size
        ac_type = self.kwargs['entity']
        if ac_type == "org":
            ac_type = "institution"
        choices = []
        headers = {'Content-Type': 'application/json'}
        ent_model = ContentType.objects.get(
            app_label='apis_entities', model=ac_type.lower()
        ).model_class()
        q = self.q.strip()

        res = ent_model.objects.filter(name__startswith=q)
        for r in res[offset:offset+page_size]:
            dates = "time: {} - {}".format(r.start_date, r.end_date)
            f = dict()
            f['id'] = "{}".format(str(r.id))
            if ac_type == 'institution':
                f['type'] = "org"
            else:
                f['type'] = "{}".format(ac_type)
            f['name'] = "{}".format(str(r))
            f['description'] = "{}".format(dates)
            choices.append(f)
        return http.HttpResponse(json.dumps({
                    'item': choices + [],
                    'pagination': {'more': True}
                }), content_type='application/json')
