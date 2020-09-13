from django.test.runner import DiscoverRunner
from django.contrib.contenttypes.models import ContentType as ct
from django.db.models import fields as ft_dj
import random
import string


def create_data(ft, ln=5):
    print(ft)
    if ft == ft_dj.CharField or ft == ft_dj.TextField:
        return ''.join(random.choices(string.ascii_letters + ' ', k=ln)) 
    elif ft == ft_dj.IntegerField or ft == ft_dj.PositiveIntegerField:
        return int(''.join(random.choices(string.digits,k=ln)))
    elif ft == ft_dj.DateField:
        return f"{random.randint(1, 30)}.{random.randint(1, 12)}.{random.randint(1, 2020)}"
    elif ft == ft_dj.BooleanField:
        return bool(random.getrandbits(1))
    else:
        print('didnt find any matching dt')


class APISTestRunner(DiscoverRunner):

    def setup_databases(self, **kwargs):
        super().setup_databases(**kwargs)

        lst_cont = [x.model_class() for x in ct.objects.filter(app_label__in=['apis_metainfo', 'apis_vocabularies', 'apis_entities', 'apis_relations']).exclude(model__in=["tempentityclass", "texttype_collections", "vocabnames", "vocabsuri", "uricandidate"]).exclude(model__icontains="baseclass")]
        lst_sort = [ct.objects.get(app_label='apis_metainfo', model="uri").model_class()]
        len_lst_cont = len(lst_cont)
        len_lst_sort = len(lst_sort)

        while len(lst_cont) > len(lst_sort):
            for c in lst_cont:
                if c in lst_sort:
                    continue
                check = True
                for fld in c._meta.get_fields() + c._meta.many_to_many:
                    if '_set' in fld.name or fld.name in ['parent_class', 'vocab_name', 'userAdded', 'groups_allowed']:
                        continue
                    if fld.__class__.__name__ in ['ForeignKey', 'ManyToManyField']:
                        if fld.related_model not in lst_sort:
                            print(f"{c} / {fld}")
                            check = False
                if check:
                    lst_sort.append(c)
            if len_lst_cont == len(lst_cont) and len_lst_sort == len(lst_sort):
                print(lst_cont)
                print(lst_sort)
                print(len(lst_cont), len(lst_sort))
                fails = [x for x in lst_cont if x not in lst_sort]
                print(f"the following ents failed: {fails}")
                raise ValueError('no change in figures')
            len_lst_cont = len(lst_cont)
            len_lst_sort = len(lst_sort)
        dict_ents = {}
        l2 = lst_sort.pop()
        lst_sort.append(l2)
        print(lst_sort)
        for ent in lst_sort[1:]:
            print(ent)
            print(f"working on {ent}")
            c_1 = {}
            for fld in ent._meta.get_fields():
                print(f"working on field {fld.name}")
                ck = False
                for pn in ['_ptr', 'set', 'baseclass']:
                    if pn in fld.name:
                        ck = True
                        break
                if fld.__class__.__name__ == "DateField" or ck:
                    continue
                elif fld.name in ['parent_class', 'userAdded', 'vocab_name', 'id', 'vocabsuri']:
                    continue
                elif 'date_written' in fld.name:
                    c_1[fld.name] = create_data(ft_dj.DateField)
                elif fld.__class__.__name__ == "ForeignKey":
                    c_1[fld.name] = dict_ents[fld.related_model.__name__][random.randint(0, len(dict_ents[fld.related_model.__name__])-1)]
                elif fld.__class__.__name__ != 'ManyToManyField' and fld.__class__.__name__ != "ManyToOneRel":
                    c_1[fld.name] = create_data(fld.__class__, random.randint(1, (fld.max_length if fld.max_length else 3) if hasattr(fld, 'max_length') else 3))
            print(c_1)
            c_1_obj = ent.objects.create(**c_1)
            for fld in c._meta.many_to_many:
                if '_set' in fld.name:
                    continue
                getattr(c_1_obj, fld.name).add(dict_ents[fld.related_model.__name__][random.randint(0, len(dict_ents[fld.related_model.__name__])-1)])
            if ent.__class__.__name__ not in dict_ents.keys():
                dict_ents[ent.__name__] = [c_1_obj,]
            else:
                dict_ents[ent.__name__].append(c_1_obj)
            print(f"created {c_1_obj}")
        return {}