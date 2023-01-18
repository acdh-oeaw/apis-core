import json
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


from apis_core.apis_entities.models import Person, Place, Institution, Work, Event, TempEntityClass
from .utils import get_service_mainfest, get_properties


@csrf_exempt
def reconcile(request):
    model_dict = {
        "person": Person,
        "place": Place,
        "work": Work,
        "institution": Institution,
        "event": Event
    }
    if request.method == "POST":
        response = {}
        data = request.POST
        print(data)
        if "queries" in data.keys():
            data_dict = json.loads(data.get("queries"))
            response = {}
            for key, value in data_dict.items():
                query_string = value["query"]
                try:
                    query_type = value["type"]
                except:
                    query_type = "/person"
                model_name = query_type.split('/')[-1]
                cur_model = model_dict[model_name]
                items = cur_model.objects.filter(name=query_string)
                properties = value.get("properties")
                if properties:
                    filters = Q()
                    for x in properties:
                        filters.add(Q(**{f"{x['pid']}": x["v"]}), Q.AND)
                    items = items.filter(filters)
                items = items.distinct()
                match_count = items.count()
                score = 0
                if match_count == 1:
                    score = 1
                    match = True
                if match_count > 1:
                    score = 1 / match_count
                    match = False
                matches = [{"id": x.id, "name": f"{x}", "score": score, "match": match} for x in items]
                item = {"result": matches}
                response[key] = item
        elif "extend" in data.keys():
            extend = json.loads(data.get("extend"))
            props = extend["properties"]
            ids = extend["ids"]
            result = {}
            result["meta"] = [{"id": x["id"], "name": x["id"].upper()} for x in props]
            rows = {}
            for x in TempEntityClass.objects.filter(id__in=ids):
                rows[f"{x.id}"] = {
                    "entid": [{"str": f"{x.id}"}],
                }
            result["rows"] = rows
            print(extend)
            print(result)
            return JsonResponse(result)
        else:
            pass

        return JsonResponse(response)
    else:
        result = get_service_mainfest(request)
    return JsonResponse(result)


def suggest_types(request):
    data = {}
    prefix = request.GET.get("prefix", "")
    suggestions = get_service_mainfest(request)["defaultTypes"]
    print(suggestions)
    filtered_results = []
    for x in suggestions:
        if x['name'].startswith(prefix):
            filtered_results.append(x)
    data["result"] = filtered_results
    print(data)
    return JsonResponse(data, safe=False)


def properties(request):
    prop_type = request.GET.get("type", "name")
    result = {}
    result["type"] = prop_type
    result["limit"] = 100
    result["properties"] = get_properties()
    return JsonResponse(result)
