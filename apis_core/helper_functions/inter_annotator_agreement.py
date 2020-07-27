from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models.query import QuerySet

from apis_core.apis_metainfo.models import Text, TempEntityClass
from apis_highlighter.models import Annotation

if 'annotator agreement' in getattr(settings, "APIS_COMPONENTS", []):
    from nltk.metrics import AnnotationTask
    import pandas as pd
    from sklearn.metrics import precision_recall_fscore_support
    import numpy as np


class InternalDataAgreement(object):
    @staticmethod
    def internal_data_agreement_calc(texts, ann1, ann2, anno_proj=None, format_string='start_end_text'):
        if type(texts) == QuerySet:
            q = {'text__in': texts}
        else:
            q = {'text': texts}
        lst_user_ann = []
        if anno_proj:
            q['annotation_project_id'] = anno_proj
        lst_ann_fin = dict()
        for v in [ann1, ann2]:
            lst_ann = []
            q['user_added_id'] = v
            for an in Annotation.objects.filter(**q).order_by('start'):
                lst_ann.append(an.annotation_hash(format_string=format_string))
                if an.user_added_id not in lst_user_ann:
                    lst_user_ann.append(an.user_added_id)
            lst_ann_fin[v] = lst_ann
        ann_task = []
        for ann in lst_ann_fin[ann1]:
            ann_task.append((ann1, ann, 1))
            if ann in lst_ann_fin[ann2]:
                ann_task.append((ann2, ann, 1))
            else:
                ann_task.append((ann2, ann, 0))
        for ann in lst_ann_fin[ann2]:
            if ann not in lst_ann_fin[ann1]:
                ann_task.append((ann2, ann, 1))
                ann_task.append((ann1, ann, 0))

        if len(ann_task) == 0:
            return None
        else:
            return AnnotationTask(data=ann_task)

    def precision_recall_calc(self, texts, gold_standard, user_group, anno_proj=None, format_string='start_end_text'):
        if type(texts) == QuerySet:
            q = {'text__in': texts}
        else:
            q = {'text': texts}
        if anno_proj:
            q['annotation_project_id'] = anno_proj
        lst_ann_fin = dict()
        if not format_string:
            format_string = 'start_end_text'
        user_list = [gold_standard]
        user_list.extend(User.objects.filter(groups__pk=user_group).exclude(pk=gold_standard)
                         .values_list('pk', flat=True))
        df = pd.DataFrame()
        for v in user_list:
            lst_ann = []
            q['user_added_id'] = v
            for an in Annotation.objects.filter(**q).order_by('start'):
                lst_ann.append(an.annotation_hash(format_string=format_string))
            lst_ann_fin[v] = lst_ann
        gold_username = User.objects.get(pk=gold_standard).username
        for u in lst_ann_fin.keys():
            ann_username = User.objects.get(pk=u).username
            if u == gold_standard:
                continue
            gold_list = []
            ann_list = []
            for ann in lst_ann_fin[u]:
                if ann in lst_ann_fin[gold_standard]:
                    gold_list.append(1)
                    ann_list.append(1)
                else:
                    gold_list.append(0)
                    ann_list.append(1)
            for ann in lst_ann_fin[gold_standard]:
                if ann not in lst_ann_fin[u]:
                    gold_list.append(1)
                    ann_list.append(0)
            prec_res = precision_recall_fscore_support(np.array(gold_list), np.array(ann_list), average='binary',
                                                       pos_label=1)
            for idx, k in enumerate(['precission', 'recall', 'fbeta_score', 'support']):
                df.loc[ann_username, k] = prec_res[idx]
        return df

    def get_html_table(self):
        css_class = 'table table-bordered table-hover'
        self.html_tables = dict()
        self.html_tables_gold = None
        if isinstance(self.texts, dict):
            for txt_id in self.texts.keys():
                self.html_tables[txt_id] = self.texts[txt_id].to_html(classes=css_class)
            if self.texts_gold is not None:
                self.html_tables_gold = dict()
                for txt_id in self.texts_gold.keys():
                    self.html_tables_gold[txt_id] = self.texts_gold[txt_id].to_html(classes=css_class)
        elif isinstance(self.texts, pd.DataFrame):
            self.html_tables = self.texts.to_html(classes=css_class)
            if self.texts_gold is not None:
                self.html_tables_gold = self.texts_gold.to_html(classes=css_class)
        return self.html_tables, self.html_tables_gold

    def __init__(self, texts, anno_proj, user_group, metrics='Do_alpha',
                 format_string='start_end_text', combine=False, gold_standard=False):
        if not type(texts) == QuerySet:
            m_name = ContentType.objects.get_for_model(texts).name
            if m_name == 'person' or m_name == 'place' or m_name == 'institution' or m_name == 'event' or m_name == 'work':
                texts = Text.objects.filter(tempentityclass=texts).distinct()
            elif m_name == 'collection':
                t = TempEntityClass.objects.filter(collection=texts)
                texts = Text.objects.filter(tempentityclass__in=t).distinct()
        self.texts_gold = None
        self._list_users = dict()
        if combine:
            self.texts = pd.DataFrame()
        else:
            self.texts = dict()
        if combine:
            texts = [texts]
        if gold_standard:
            self.texts_gold = dict()
        if not user_group:
            user_qs = dict()
        else:
            user_qs = {'groups__pk': user_group}
        for txt in texts:
            df = pd.DataFrame()
            test = False
            for ann1 in User.objects.filter(**user_qs):
                for ann2 in User.objects.filter(**user_qs):
                    if ann1 == ann2:
                        t = None
                        continue
                    try:
                        t = getattr(
                            self.internal_data_agreement_calc(
                                txt,
                                ann1.pk,
                                ann2.pk,
                                anno_proj=anno_proj,
                                format_string=format_string),metrics)()
                        if pd.notnull(t):
                            test = True
                    except AttributeError as ex:
                        t = None
                    df.loc[ann1.username, ann2.username] = t
                    if ann1.pk not in self._list_users.keys():
                        self._list_users[ann1.pk] = ann1
                    if ann2.pk not in self._list_users.keys():
                        self._list_users[ann2.pk] = ann2
            if test:
                if combine:
                    self.texts = df
                else:
                    self.texts[txt.pk] = df
            if gold_standard:
                if combine:
                    self.texts_gold = self.precision_recall_calc(
                        txt, gold_standard, user_group, anno_proj=anno_proj)
                else:
                    self.texts_gold[txt.pk] = self.precision_recall_calc(
                        txt, gold_standard, user_group, anno_proj=anno_proj)
