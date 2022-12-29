from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .utils import get_service_mainfest, get_properties
import json


@csrf_exempt
def reconcile(request):
    if request.method == "POST":
        data = request.POST
        data_dict = json.loads(data.get("queries"))
        print(type(data_dict))
        for key, value in data_dict.items():
            print(key, value)

        return HttpResponse(data)
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
