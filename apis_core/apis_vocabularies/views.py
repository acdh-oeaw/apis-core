import pandas as pd
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse


@login_required
def dl_vocabs_as_csv(request, model_name):
    kwargs = {
        "app_label": "apis_vocabularies",
        "entity": model_name
    }
    model = ContentType.objects.get(
        app_label=kwargs.get("app_label"), model=kwargs.get("entity").lower()
    ).model_class()
    data = [[x.id, x.name, x.parent_class] for x in model.objects.all()]
    columns = ['id', 'name', 'parent_class']
    df = pd.DataFrame(data, columns=columns)
    filename = f"{kwargs.get('entity').lower()}.csv"
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f"attachment; filename='{filename}'"
    df.to_csv(response, index=False)

    return response

# Create your views here.
