from django.views.generic import View
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from highlighter.forms import SelectAnnotatorAgreementCollection
if 'annotator agreement' in getattr(settings, "APIS_COMPONENTS", []):
    from helper_functions.inter_annotator_agreement import InternalDataAgreement
from metainfo.models import Text, Collection, TempEntityClass


@method_decorator(login_required, name='dispatch')
class ComputeAgreement(View):

    def get(self, request):
        form = SelectAnnotatorAgreementCollection()
        return render(request, 'calculate_agreement.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = SelectAnnotatorAgreementCollection(request.POST)
        if form.is_valid():
            gold_standard = form.cleaned_data.get('gold_standard')
            user_group = form.cleaned_data.get('user_group')
            metrics = form.cleaned_data.get('metrics')
            format_string = form.cleaned_data.get('format_string')
            ann_proj_pk = form.cleaned_data.get('anno_proj')
            collection = form.cleaned_data.get('collection')
            kind_instance = form.cleaned_data.get('kind_instance')
            text_type = form.cleaned_data.get('text_type')
            met_dict = dict(form.fields['metrics'].choices)
            title1 = met_dict[form.cleaned_data['metrics']]
            txt = Text.objects.all()
            ent = False
            if kind_instance:
                col = Collection.objects.get(pk=collection)
                ent = ContentType.objects.get_for_id(kind_instance).model_class()
                ent = ent.objects.filter(collection=col)
            elif collection:
                col = Collection.objects.get(pk=collection)
                ent = TempEntityClass.objects.filter(collection=col)
            if ent:
                txt = txt.filter(tempentityclass__in=ent).distinct()
            if text_type:
                txt = txt.filter(kind_id__in=text_type)
            tab1, tab2 = InternalDataAgreement(
                txt, ann_proj_pk, user_group,
                gold_standard=gold_standard, metrics=metrics,
                combine=True, format_string=format_string).get_html_table()
            return render(request, 'calculate_agreement.html', {
                'form': form, 'tab1': tab1, 'tab2': tab2, 'title1': title1})
