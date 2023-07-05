#w2v에 기반하여 재구성한 Preprocess 파일입니다.

from konlpy.tag import Komoran
import pickle
import jpype
import gensim
import re
import json

class PreprocessW2V:
    def __init__(self, w2v_model='ko_with_corpus_mc1.model', userdic=None):
        # 단어 인덱스 사전 불러오기
        print('modelname:',w2v_model)
        if w2v_model.split('.')[1]=='model':
            model = gensim.models.Word2Vec.load(w2v_model)
            self.word_index = model.wv.key_to_index #w2v모델에 있는 단어사전의 인덱스셋을 불러옴
        elif w2v_model.split('.')[1]=='kv':
            model = gensim.models.keyedvectors.KeyedVectors.load(w2v_model)
            self.word_index = model.key_to_index #w2v모델에 있는 단어사전의 인덱스셋을 불러옴
        else:
            print('Error')
            self.word_index=[]
        # 형태소 분석기 초기화
        self.komoran = Komoran(userdic=userdic)
        
        # 제외할 품사
        # 참조 : https://docs.komoran.kr/firststep/postypes.html
        # 관계언 제거, 기호 제거
        # 어미 제거
        # 접미사 제거
        self.exclusion_tags = [
            'JKS', 'JKC', 'JKG', 'JKO', 'JKB', 'JKV', 'JKQ',
            'JX', 'JC',
            'SF', 'SP', 'SS', 'SE', 'SO',
            'EP', 'EF', 'EC', 'ETN', 'ETM',
            'XSN', 'XSV', 'XSA'
        ]

        with open('menu.json', 'r', encoding='utf-8') as f:
            self.menu=json.load(f)
        self.submenu=[]
        for cat in self.menu.values():
            for food in cat:
                self.submenu.append(food["name"])

        self.mod_submenu=[]
        for item in self.submenu:
            mod_item=re.sub(r"[^가-힣a-zA-Z]", "", item)
            dic={}
            dic['mod']=mod_item
            dic['exactname']=item
            self.mod_submenu.append(dic)

    # 형태소 분석기 POS 태거
    def pos(self, sentence):
        jpype.attachThreadToJVM()
        return self.komoran.pos(sentence)

    # 불용어 제거 후, 필요한 품사 정보만 가져오기
    def get_keywords(self, pos, without_tag=False):
        f = lambda x: x in self.exclusion_tags
        word_list = []
        for p in pos:
            if f(p[1]) is False:
                word_list.append(p if without_tag is False else p[0])

        if without_tag==True:
            word_list=self.auto_correct_keywords(word_list)

        return word_list

    # 키워드를 단어 인덱스 시퀀스로 변환
    def get_wordidx_sequence(self, keywords):
        if self.word_index is None:
            return []

        w2i = []
        for word in keywords:
            try:
                w2i.append(self.word_index[word])
            except KeyError:
                # 해당 단어가 사전에 없는 경우, OOV 처리
                w2i.append(self.word_index['O']) #w2v의 불용어는 O에 대응
        return w2i

    def auto_correct(self, word):
        result=word
        mod_word=re.sub(r"[^가-힣a-zA-Z]", "", word)
        for item in self.mod_submenu:
            if mod_word==item['mod']:
                result=item['exactname']
        return result

    def auto_correct_keywords(self, lst):
        new=[]
        for word in lst:
            new_word=self.auto_correct(word)
            new.append(new_word)
        return new