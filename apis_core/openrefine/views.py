import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from apis_core.apis_entities.models import Person
from .utils import get_service_mainfest, get_properties


@csrf_exempt
def reconcile(request):
    if request.method == "POST":
        data = request.POST
        data_dict = json.loads(data.get("queries"))
        response = {}
        for key, value in data_dict.items():
            query_string = value["query"]
            persons = Person.objects.filter(name__icontains=query_string)
            match_count = persons.count()
            score = 0
            if match_count == 1:
                score = 1
                match = True
            if match_count > 1:
                score = 1 / match_count
                match = False
            matches = [{"id": x.id, "name": f"{x}", "score": score, "match": match} for x in persons]
            item = {"result": matches}
            response[key] = item
        return JsonResponse(response)
    else:
        result = get_service_mainfest(request)
    return JsonResponse(result)


def suggest_types(request):
    data = {}
    data["result"] = get_service_mainfest(request)["defaultTypes"]
    return JsonResponse(data, safe=False)


def properties(request):
    prop_type = request.GET.get("type", "name")
    result = {}
    result["type"] = prop_type
    result["limit"] = 100
    result["properties"] = get_properties()
    return JsonResponse(result)
