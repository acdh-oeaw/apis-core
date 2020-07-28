from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect


@login_required
def merge_objects(request):
    go_back = request.META.get('HTTP_REFERER')
    print("go back: {}".format(go_back))
    if request.method == 'POST':
        keep = request.POST.get("keep", None)
        remove = request.POST.getlist("remove", None)
        model_name = request.POST.get("model_name", None)
        app_name = request.POST.get("app_name", None)
        print('##############################')
        print(keep, remove, model_name, app_name)
        if keep and remove and model_name and app_name:
            print("all good, let's merge")
            try:
                ct = ContentType.objects.get(app_label=app_name, model=model_name).model_class()
            except ObjectDoesNotExist:
                ct = None
                print('no "keep" object found')
                return HttpResponseRedirect(go_back)
            if ct:
                try:
                    keep_obj = ct.objects.filter(pk=keep)[0]
                except IndexError:
                    print("No matching object to keep found")
                    return HttpResponseRedirect(go_back)
                remove_objs = ct.objects.filter(pk__in=remove)
                keep_obj.merge_with(remove_objs)
                return HttpResponseRedirect(go_back)
            else:
                return HttpResponseRedirect(go_back)
        elif remove and model_name and app_name:
            print("all good, let's delete")
            try:
                ct = ContentType.objects.get(app_label=app_name, model=model_name).model_class()
            except ObjectDoesNotExist:
                ct = None
            if ct:
                remove_objs = ct.objects.filter(pk__in=remove)
                if len(remove_objs) > 0:
                    for x in remove_objs:
                        x.delete()
                        print("deleted: {}".format(x))
            return HttpResponseRedirect(go_back)
        else:
            return HttpResponseRedirect(go_back)
    else:
        print('ui, something went wrong')
        return HttpResponseRedirect(go_back)
