from apis_highlighter.models import Annotation
from apis_core.metainfo.models import Text
import re
from django.contrib.contenttypes.models import ContentType


def highlight_text(*args, **kwargs):
    ann_proj_pk = kwargs.pop('set_ann_proj', False)
    types = kwargs.pop('types', False)
    users_show = kwargs.pop('users_show', False)
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
        queries['user_added_id__in'] = users_show
    if ann_proj_pk:
        queries['annotation_project__pk'] = ann_proj_pk
    queries['text'] = obj
    for an in Annotation.objects.filter(**queries).order_by('start'):
        if types:
            test = False
            for m in an.entity_link.all():
                t = ContentType.objects.get_for_model(m)
                if str(t.pk) in types:
                    test = True
            if not test:
                continue
        if an.start >= t_start and an.start <= t_end:
            lst_annot[-1].append(an)
        else:
            lst_annot.append([an, ])
        t_start = an.start
        t_end = an.end
    if len(lst_annot) == 0:
        return obj.text
    html_return = obj.text[:lst_annot[0][0].start]
    end = ''
    lst_end = None
    for an in lst_annot:
        start = min([x.start for x in an])
        end = max([x.end for x in an])
        if len(an) > 1:
            start_span = '''<mark class="hl_text_complex" data-hl-type="complex" data-hl-start="{}"
            data-hl-end="{}" data-hl-text-id="{}">'''.format(start, end, obj.pk)
        else:
            start_span = an[0].get_html_markup()
        if lst_end:
            html_return += obj.text[lst_end:start] + start_span + obj.text[start:end] + '</mark>'
        else:
            html_return += start_span + obj.text[start:end] + '</mark>'
        lst_end = end
    html_return += obj.text[end:]
    if obj.text[0] == '\n':
        html_return = '-'+html_return[1:]
    return html_return


def highlight_textTEI(*args, **kwargs):
    user_pk = kwargs.pop('user', False)
    ann_proj_pk = kwargs.pop('ann_proj', False)
    obj = args[-1]
    t_start = 0
    t_end = 0
    if isinstance(obj, str):
        obj = Text.objects.get(pk=obj)
    lst_annot = []
    for an in Annotation.objects.filter(text=obj).order_by('start'):
        if an.start >= t_start and an.start <= t_end:
            lst_annot[-1].append(an)
        else:
            lst_annot.append([an, ])
        t_start = an.start
        t_end = an.end
    #print(lst_annot)
    if len(lst_annot) == 0:
        return obj.text
    html_return = obj.text[:lst_annot[0][0].start]
    end = ''
    lst_end = None
    for an in lst_annot:
        start = min([x.start for x in an])
        end = max([x.end for x in an])
        try:
            lst_classes = ' '.join([str(x.relation_type.pk) for x in an[0].entity_link.all()])
        except:
            try:
                lst_classes = ' '.join([str(x.kind.pk) for x in an[0].entity_link.all()])
            except:
                lst_classes = ''
        if len(an) > 1:
            start_span = '<name type="complex" hl-start="{}" hl-end="{}" hl-text-id="{}">'.format(start, end, obj.pk)
        else:
            try:
                entity_type = type(an[0].entity_link.all()[0]).__name__
                entity_pk = an[0].entity_link.all()[0].pk
                ent_lst_pk = []
                for x in dir(an[0].entity_link.all()[0]):
                    c = re.match('related_\w+_id', x)
                    if c:
                        ent_lst_pk.append(str(getattr(an[0].entity_link.all()[0], c.group(0))))
                if len(ent_lst_pk) == 0:
                    ent_lst_pk.append(str(an[0].entity_link.all()[0].pk))
            except:
                entity_type = ''
                entity_pk = ''
                ent_lst_pk = []
            try:
                entity_uri = an[0].entity_link.all()[0].uri_set.values_list('uri', flat=True)[0]
            except:
                entity_uri = 'internal db id: {}'.format(an[0].entity_link.all()[0].pk)
            start_span = '<name hl-type="simple" hl-start="{}" hl-end="{}" hl-text-id="{}" hl-ann-id="{}" type="{}" entity-pk="{}" related-entity-pk="{}">'.format(start, end, obj.pk, an[0].pk, entity_type, entity_pk, ','.join(ent_lst_pk))
            #'<span class="highlight hl_text_{}" data-hl-type="simple" data-hl-start="{}" data-hl-end="{}" data-hl-text-id="{}" data-hl-ann-id="{}" data-entity-class="{}" data-entity-pk="{}" data-related-entity-pk="{}">'.format(start, end, obj.pk, an[0].pk, entity_type, entity_pk, ','.join(ent_lst_pk))
        if lst_end:
            if len(an) > 1:
                html_return += obj.text[lst_end:start] + start_span + obj.text[start:end] + '</name>'
            else:
                html_return += obj.text[lst_end:start] + start_span + obj.text[start:end] + '<index><term>'+entity_uri+ '</term></index></name>'
        else:
            html_return += start_span + obj.text[start:end] + '</name>'
        lst_end = end
    html_return += obj.text[end:]
    return html_return
