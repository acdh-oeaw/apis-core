import numpy as np
import keras
from keras.datasets import reuters
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation
from keras.preprocessing.text import Tokenizer
import pickle
from keras import backend as K

import spacy
from spacy.matcher import Matcher
from spacy.attrs import IS_PUNCT, LOWER, ENT_TYPE, IS_ALPHA, TAG

import de_core_news_sm

from vocabularies.models import VocabsBaseClass

nlp = de_core_news_sm.load()

lst_orth = []
lst_orth_dict = dict()


def extract_verbs_from_entity(ent, lst_orth, lst_orth_dict, accept_pos=['VERB', 'AUX', 'NOUN', 'ADP', 'PART'], add=True):
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
                    #tokens.append(head.orth)
                    pos_tags.append(head.pos)
                    shapes.append(head.shape)
            else:
                head = False
    return tokens, lemmas, pos_tags, shapes


def get_verbs_relations(doc, ent_id, text_id, ann_proj_id, user_id, kind):
    labels = []
    tokens_lst = []
    lemmas_lst = []
    pos_tags_lst = []
    shapes_lst = []
    for ent in doc.ents:
        if ent.label == ent_id:
            ann = Annotation.objects.filter(text_id=text_id, user_added_id__in=user_id, start=ent.start_char, end=ent.end_char)
            tokens, lemmas, pos_tags, shapes = extract_verbs_from_entity(ent)
            if len(tokens) > 0:
                if ann.count() > 0:
                    if len(ann[0].entity_link.all()) == 1:
                        cn = ann[0].entity_link.all()[0].__class__.__name__
                        if cn in kind:
                            label = ann[0].entity_link.all()[0].relation_type.pk
                            if label in lst_labels:
                                labels.append(lst_labels_dict[label])
                            else:
                                lst_labels.append(label)
                                lst_labels_dict[label] = len(lst_labels)
                                labels.append(len(lst_labels))
                        else:
                            if hash(frozenset(tokens)) not in lst_zero_label:
                                lst_zero_label.append(hash(frozenset(tokens)))
                                labels.append(0)
                            else:
                                continue
                    else:
                        if hash(frozenset(tokens)) not in lst_zero_label:
                                lst_zero_label.append(hash(frozenset(tokens)))
                                labels.append(0)
                        else:
                            continue
                else:
                    if hash(frozenset(tokens)) not in lst_zero_label:
                        lst_zero_label.append(hash(frozenset(tokens)))
                        labels.append(0)
                    else:
                        continue
                tokens_lst.append(tokens)
                lemmas_lst.append(lemmas)
                pos_tags_lst.append(pos_tags)
                shapes_lst.append(shapes)
    return tokens_lst, lemmas_lst, pos_tags_lst, shapes_lst, labels


def get_training_data(col_pk, text_type_name, spc_ent_type, ann_proj_pk, user_pk, relations_list, save=False):
    col = Collection.objects.get(pk=col_pk)
    count=0
    verbs_level = dict()
    tokens_fin = []
    lemmas_fin = []
    pos_tags_fin = []
    shapes_fin = []
    labels_fin = []
    count = 0
    for pers in Person.objects.filter(collection=col):
        try:
            txt = pers.text.all().filter(kind__name__icontains="Haupttext")[0]
            count+=1
        except:
            continue
        count += 1
        doc = nlp(txt.text)
        print('Running through text')
        res2 = get_verbs_relations(doc, spc_ent_type, txt.pk, ann_proj_pk, user_pk, relations_list)
        if res2:
            tokens, lemmas, pos_tags, shapes, labels = res2
            if len(tokens) > 0:
                tokens_fin.extend(tokens)
                lemmas_fin.extend(lemmas)
                pos_tags_fin.extend(pos_tags)
                shapes_fin.extend(shapes)
                labels_fin.extend(labels)
    if save:
        for f in ['tokens_fin', 'lemmas_fin', 'pos_tags_fin', 'shapes_fin', 'labels_fin']:
            fw = open(save, 'wb')
            pickle.dump(eval(f), fw)
    return tokens_fin, lemmas_fin, pos_tags_fin, shapes_fin, labels_fin


def train_model(col_pk, text_type_name, spc_ent_type, ann_proj_pk, user_pk, relations_list, save_train_data=False,
                save=False):
    tokens_fin, lemmas_fin, pos_tags_fin, shapes_fin, labels_fin = get_training_data(col_pk, text_type_name,
                                                                                     spc_ent_type, ann_proj_pk, user_pk,
                                                                                     relations_list, save_train_data)
    x_train2 = np.array(tokens_fin)
    tokenizer = Tokenizer(num_words=len(lst_orth))
    x_train2 = tokenizer.sequences_to_matrix(x_train2, mode='binary')
    y_train2 = keras.utils.to_categorical(labels_fin, len(lst_labels) + 1)
    model = Sequential()
    model.add(Dense(512, input_shape=(len(lst_orth),)))
    model.add(Activation('relu'))
    model.add(Dropout(0.5))
    model.add(Dense(len(lst_labels) + 1))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy',
                  optimizer='adam',
                  metrics=['accuracy'])
    callbacks = []
    if save:
        callbacks.append(keras.callbacks.ModelCheckpoint(save, monitor='val_loss', verbose=1, save_best_only=True,
                                                         save_weights_only=False, mode='auto', period=1))

    history = model.fit(x_train2, y_train2,
                        batch_size=32,
                        epochs=8,
                        verbose=1,
                        validation_split=0.2,
                        callbacks=callbacks,
                        shuffle=True)
    return model, labels_fin


def test_model(model, sent):
    K.clear_session()
    fileh = open('data/nlp_models/{}_vocab.obj'.format(model), 'rb')
    lst_orth, lst_orth_dict, lst_labels, lst_labels_dict, lst_zero_label, lst_labels_dhae2 = pickle.load(fileh)
    model = keras.models.load_model('data/nlp_models/{}.h5'.format(model))
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

