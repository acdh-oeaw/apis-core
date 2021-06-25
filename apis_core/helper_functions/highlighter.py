import re

from django.contrib.contenttypes.models import ContentType

from apis_core.apis_metainfo.models import Text
from apis_highlighter.models import Annotation


def highlight_text_new(*args, **kwargs):
    ann_proj_pk = kwargs.pop("set_ann_proj", False)
    types = kwargs.pop("types", False)
    users_show = kwargs.pop("users_show", False)
    inline_annotations = kwargs.pop("inline_annotations", True)
    t_start = 0
    t_end = 0
    obj = args[-1]
    if isinstance(obj, str):
        obj = Text.objects.get(pk=obj)
    lst_annot = []
    queries = dict()
    if users_show:
        queries["user_added_id__in"] = users_show
    if ann_proj_pk:
        queries["annotation_project__pk"] = ann_proj_pk
    queries["text"] = obj
    anns1 = Annotation.objects.filter(**queries).order_by("start")
    anns_fin = []
    for ann in anns1:
        for lb in re.finditer(r"[\r\n]", obj.text):
            if lb.start() < ann.start + (lb.end() - lb.start()):
                ann.start += lb.end() - lb.start()
                ann.end += lb.end() - lb.start()
        anns_fin.append(ann)
    for an in anns_fin:
        if types:
            m = an.entity_link
            if m is not None:
                t = ContentType.objects.get_for_model(m)
                if not (str(t.pk) in types):
                    continue
        c_start = re.findall(r"[\r\n]+", obj.text[: an.start])
        if len(c_start) > 0:
            an.start += len("".join(c_start))
        c_end = re.findall(r"[\r\n]+", obj.text[: an.end])
        if len(c_end) > 0:
            an.end += len("".join(c_end))
        if an.start >= t_start and an.start <= t_end:
            lst_annot[-1].append(an)
        else:
            lst_annot.append(
                [
                    an,
                ]
            )
        t_start = an.start
        t_end = an.end
    if len(lst_annot) == 0:
        html_return = obj.text
        html_return, nmbs = re.subn(r"\r\n", "<br/>", html_return)
        html_return, nmbs = re.subn(r"\r", "<br/>", html_return)
        html_return, nmbs = re.subn(r"\n", "<br/>", html_return)
        return html_return, None
    html_return = obj.text[: lst_annot[0][0].start]
    end = ""
    lst_end = None
    res_annotations = []
    for an in lst_annot:
        start = min([x.start for x in an])
        end = max([x.end for x in an])
        if len(an) > 1:
            start_span = """<mark class="highlight hl_text_complex" data-hl-type="complex" data-hl-start="{}" data-hl-end="{}" data-hl-text-id="{}">""".format(
                start, end, obj.pk
            )
            for an2 in an:
                res_annotations.append(an2.get_html_markup(include_object=True))
        else:
            start_span, res_ann = an[0].get_html_markup(include_object=True)
            res_annotations.append(res_ann)
        if lst_end:
            html_return += (
                obj.text[lst_end:start] + start_span + obj.text[start:end] + "</mark>"
            )
        else:
            html_return += start_span + obj.text[start:end] + "</mark>"
        lst_end = end
    html_return += obj.text[end:]
    if obj.text[0] == "\n":
        html_return = "-" + html_return[1:]
    if not inline_annotations:
        html_return = obj.text
    html_return, nmbs = re.subn(r"\r\n", "<br/>", html_return)
    html_return, nmbs = re.subn(r"\r", "<br/>", html_return)
    html_return, nmbs = re.subn(r"\n", "<br/>", html_return)
    return html_return, res_annotations


def highlight_text(*args, **kwargs):
    ann_proj_pk = kwargs.pop("set_ann_proj", False)
    types = kwargs.pop("types", False)
    users_show = kwargs.pop("users_show", False)
    t_start = 0
    t_end = 0
    obj = args[-1]
    if isinstance(obj, str):
        obj = Text.objects.get(pk=obj)
    if not types or not users_show:
        return obj.text
    lst_annot = []
    queries = dict()
    if users_show:
        queries["user_added_id__in"] = users_show
    if ann_proj_pk:
        queries["annotation_project__pk"] = ann_proj_pk
    queries["text"] = obj
    anns1 = Annotation.objects.filter(**queries).order_by("start")
    anns_fin = []
    for ann in anns1:
        for lb in re.finditer(r"[\r\n]", obj.text):
            if lb.start() < ann.start + (lb.end() - lb.start()):
                ann.start += lb.end() - lb.start()
                ann.end += lb.end() - lb.start()
        anns_fin.append(ann)
    for an in anns_fin:
        if types:
            m = an.entity_link
            if m is not None:
                t = ContentType.objects.get_for_model(m)
                if not (str(t.pk) in types):
                    continue
        if an.start >= t_start and an.start <= t_end:
            lst_annot[-1].append(an)
        else:
            lst_annot.append(
                [
                    an,
                ]
            )
        t_start = an.start
        t_end = an.end
    if len(lst_annot) == 0:
        html_return = obj.text
        html_return, nmbs = re.subn(r"\r\n", "<br/>", html_return)
        html_return, nmbs = re.subn(r"\r", "<br/>", html_return)
        html_return, nmbs = re.subn(r"\n", "<br/>", html_return)
        return html_return
    html_return = obj.text[: lst_annot[0][0].start]
    end = ""
    lst_end = None
    for an in lst_annot:
        start = min([x.start for x in an])
        end = max([x.end for x in an])
        if len(an) > 1:
            start_span = """<mark class="highlight hl_text_complex" data-hl-type="complex" data-hl-start="{}" data-hl-end="{}" data-hl-text-id="{}">""".format(
                start, end, obj.pk
            )
        else:
            start_span = an[0].get_html_markup()
        if lst_end:
            html_return += (
                obj.text[lst_end:start] + start_span + obj.text[start:end] + "</mark>"
            )
        else:
            html_return += start_span + obj.text[start:end] + "</mark>"
        lst_end = end
    html_return += obj.text[end:]
    if obj.text[0] == "\n":
        html_return = "-" + html_return[1:]

    html_return, nmbs = re.subn(r"\r\n", "<br/>", html_return)
    html_return, nmbs = re.subn(r"\r", "<br/>", html_return)
    html_return, nmbs = re.subn(r"\n", "<br/>", html_return)
    return html_return


def highlight_textTEI(*args, **kwargs):
    user_pk = kwargs.pop("user", False)
    ann_proj_pk = kwargs.pop("ann_proj", False)
    obj = args[-1]
    t_start = 0
    t_end = 0
    if isinstance(obj, str):
        obj = Text.objects.get(pk=obj)
    lst_annot = []
    for an in Annotation.objects.filter(text=obj).order_by("start"):
        if an.start >= t_start and an.start <= t_end:
            lst_annot[-1].append(an)
        else:
            lst_annot.append(
                [
                    an,
                ]
            )
        t_start = an.start
        t_end = an.end
    # print(lst_annot)
    if len(lst_annot) == 0:
        return obj.text
    html_return = obj.text[: lst_annot[0][0].start]
    end = ""
    lst_end = None
    for an in lst_annot:
        start = min([x.start for x in an])
        end = max([x.end for x in an])
        try:
            lst_classes = str(an[0].entity_link.relation_type.pk)
        except:
            try:
                lst_classes = str(an[0].entity_link.kind.pk)
            except:
                lst_classes = ""
        if len(an) > 1:
            start_span = '<name type="complex" hl-start="{}" hl-end="{}" hl-text-id="{}">'.format(
                start, end, obj.pk
            )
        else:
            try:
                entity_type = type(an[0].entity_link).__name__
                entity_pk = an[0].entity_link.pk
            except:
                entity_type = ""
                entity_pk = ""
                ent_lst_pk = []
            try:
                entity_uri = an[0].entity_link.uri_set.values_list('uri', flat=True)[0]
            except:
                entity_uri = 'internal db id: {}'.format(an[0].entity_link.pk)
            start_span = '<name hl-type="simple" hl-start="{}" hl-end="{}" hl-text-id="{}" hl-ann-id="{}" type="{}" entity-pk="{}" related-entity-pk="{}">'.format(
                start,
                end,
                obj.pk,
                an[0].pk,
                entity_type,
                entity_pk,
                ",".join(ent_lst_pk),
            )
            #'<span class="highlight hl_text_{}" data-hl-type="simple" data-hl-start="{}" data-hl-end="{}" data-hl-text-id="{}" data-hl-ann-id="{}" data-entity-class="{}" data-entity-pk="{}" data-related-entity-pk="{}">'.format(start, end, obj.pk, an[0].pk, entity_type, entity_pk, ','.join(ent_lst_pk))
        if lst_end:
            if len(an) > 1:
                html_return += (
                    obj.text[lst_end:start]
                    + start_span
                    + obj.text[start:end]
                    + "</name>"
                )
            else:
                html_return += (
                    obj.text[lst_end:start]
                    + start_span
                    + obj.text[start:end]
                    + "<index><term>"
                    + entity_uri
                    + "</term></index></name>"
                )
        else:
            html_return += start_span + obj.text[start:end] + "</name>"
        lst_end = end
    html_return += obj.text[end:]
    return html_return
