import numpy as np
from keras.models import load_model
from keras.preprocessing.text import Tokenizer
import pickle
from keras import backend as K
import os

import spacy
from spacy.matcher import Matcher
from spacy.attrs import IS_PUNCT, LOWER, ENT_TYPE, IS_ALPHA, TAG

import de_core_news_sm

from apis_core.vocabularies.models import VocabsBaseClass

nlp = de_core_news_sm.load()

lst_orth = []
lst_orth_dict = dict()


def extract_verbs_from_entity(
        ent, lst_orth, lst_orth_dict, accept_pos=['VERB', 'AUX', 'NOUN', 'ADP', 'PART'], add=True):
    res = []
    for y in ent:
        head = y
        tokens = []
        lemmas = []
        pos_tags = []
        shapes = []
        while head:
            if head.head != head:
                head = head.head
                if head.pos_ in accept_pos:
                    if head.orth in lst_orth:
                        tokens.append(lst_orth_dict[head.orth])
                    elif add:
                        lst_orth.append(head.orth)
                        lst_orth_dict[head.orth] = len(lst_orth)
                        tokens.append(len(lst_orth))
                    else:
                        continue
                    pos_tags.append(head.pos)
                    shapes.append(head.shape)
            else:
                head = False
    return tokens, lemmas, pos_tags, shapes


def test_model(model, sent):
    K.clear_session()
    script_dir = os.path.dirname(os.path.realpath('__file__'))
    fileh = open(os.path.join(script_dir,
                              'data/nlp_models/{}_vocab.obj'.format(model)), 'rb')
    lst_orth, lst_orth_dict, lst_labels, lst_labels_dict, lst_zero_label, lst_labels_dhae2 = pickle.load(fileh)
    model = load_model(os.path.join(script_dir,
                       'data/nlp_models/{}.h5'.format(model)))
    result = []
    txt = nlp(sent)
    tokens_lst = []
    for ent in txt.ents:
        print(ent)
        tokens, lemmas, pos_tags, shapes = extract_verbs_from_entity(ent, lst_orth, lst_orth_dict, add=False)
        if len(tokens) > 0:
            tokens_lst.append(tokens)
    x_matrix2 = np.array(tokens_lst)
    print(x_matrix2)
    tokenizer = Tokenizer(num_words=len(lst_orth))
    x_matrix3 = tokenizer.sequences_to_matrix(tokens_lst, mode='binary')
    zz = model.predict(x_matrix3, batch_size=32, verbose=1)
    for idx1, z in enumerate(zz):
        for idx, x in enumerate(zz[idx1]):
            v_id = '-'
            for k in lst_labels_dict.keys():
                if lst_labels_dict[k] == idx:
                    v_id = VocabsBaseClass.objects.get(id=k).name
            result.append((str(txt.ents[idx1]), idx, v_id, x))
    return result
