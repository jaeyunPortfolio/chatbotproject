#model = gensim.models.Word2Vec.load('ko/ko.bin')
#model = gensim.models.KeyedVectors.load_word2vec_format('ko/ko.bin', encoding='utf8')
#Pretrained W2V: https://github.com/Kyubyong/wordvectors

#https://drive.google.com/file/d/1ZiDi_xvqzUvmf7MqLn4AgB9VRQ5rPKRd/view?usp=drive_link

import pandas as pd
import gensim
import numpy as np
import csv
import re
from customer import Customer
from utils.PreprocessW2V import PreprocessW2V

import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras import preprocessing
from sklearn.model_selection import train_test_split
import numpy as np

from utils.PreprocessW2V import PreprocessW2V as Preprocess
from models.ner.NerModel_New import NerModel
#from models.intent.IntentModel import IntentModel
from models.intent.IntentModel_New import IntentModel


cust=Customer()
# 전처리 객체 생성
p = Preprocess(w2v_model='ko_with_corpus_mc1_menu_added.kv', userdic='utils/user_dic.txt')

# 개체명 인식 모델
ner = NerModel(proprocess=p)

# 의도 파악 모델
#intent = IntentModel(model_name='models/intent/intent_w2v_model.h5', proprocess=p)
intent = IntentModel(proprocess=p, nermodel=ner, customer=cust)

# 개체명 인식 모델
ner = NerModel(proprocess=p)

# 학습 파일 불러오기
def read_file(file_name):
    sents = []
    with open(file_name, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for idx, l in enumerate(lines):
            if l[0] == ';' and lines[idx + 1][0] == '$':
                this_sent = []
            elif l[0] == '$' and lines[idx - 1][0] == ';':
                continue
            elif l[0] == '\n':
                sents.append(this_sent)
            else:
                this_sent.append(tuple(l.split()))
    return sents



def compare_dict():
    pw = PreprocessW2V(w2v_model='ko_with_corpus_mc1_menu_added.kv',userdic='utils/user_dic.txt')
    pn = Preprocess(word2index_dic='train_tools/dict/chatbot_dict.bin',
               userdic='utils/user_dic.txt')
    cnt=0
    for word in pn.word_index.keys():
        if word not in pw.word_index.keys():
            cnt+=1
    print('words only in basecode corpus:', cnt)

    cnt=0
    for word in pw.word_index.keys():
        if word not in pn.word_index.keys():
            cnt+=1
    print('words only in new corpus:', cnt)

#model = gensim.models.keyedvectors.KeyedVectors.load('ko.kv')
#model = gensim.models.Word2Vec.load('ko_with_corpus_mc1.model')

#print(model.wv.index_to_key) #keylist
#print(model.wv.key_to_index) #key : index dict 
#print(type(model.wv.key_to_index))
#print(model['하'])

'''
# 학습용 말뭉치 데이터를 불러옴
corpus = read_file('models/ner/'+'ner_train.txt')

# 말뭉치 데이터에서 단어와 BIO 태그만 불러와 학습용 데이터셋 생성
sentences, tags = [], []
for t in corpus:
    tagged_sentence = []
    sentence, bio_tag = [], []
    for w in t:
        tagged_sentence.append((w[1], w[3]))
        sentence.append(w[1])
        bio_tag.append(w[3])
    
    sentences.append(sentence)
    tags.append(bio_tag)



#######################
#samples= '타코 부리또 퀘사디아 온더보더 멕시코'
samples='타코랑 부리또 주문할게'
print(ner.predict(samples))
samples='짜장면 짬뽕 바나나 가락지빵 쀍'
print(ner.predict(samples))
samples='짬뽕 짜장면 바나나 가락지빵 쀍'
print(ner.predict(samples))
samples='가락지빵 짬뽕 짜장면 바나나 쀍'
print(ner.predict(samples))
'''

def analyse_sent(sent):
    intention=intent.predict_class(sent)
    pos = p.pos(sent)
    keywords = p.get_keywords(pos, without_tag=True)
    nertags=ner.predict(sent)
    tags=[x[1] for x in nertags]
    result= [sent,intention, keywords, tags]
    print(result)

def intent_match(result, intent):
    labels = {0: "인사", 1: "메뉴안내", 2: "주문", 3: "예약", 4: "기타", 5: "메뉴추천", 6: "매장문의", 7: "이벤트정보", 8: "매장정보"}
    if result==labels[intent]:
        return False
    elif result in ["주문", "주문취소", "메뉴추천"] and labels[intent]=="주문":
        return False
    else:
        return True


def intent_test():
    train_file = "total_train_data_new.csv"
    data = pd.read_csv('models/intent/'+train_file, delimiter=',')
    queries = data['query'].tolist()
    intents = data['intent'].tolist()
    labels = {0: "인사", 1: "메뉴안내", 2: "주문", 3: "예약", 4: "기타", 5: "메뉴추천", 6: "매장문의", 7: "이벤트정보", 8: "매장정보"}


    f = open('false_note.csv', 'w')
    writer = csv.writer(f)
    cnt=0
    i=0

    for i in range(data.shape[0]):
        
        result=intent.predict_class(queries[i])
        #if result!=labels[intents[i]]:
        if intent_match(result, intents[i]):
            cnt+=1
            pos = p.pos(queries[i])
            keywords = p.get_keywords(pos, without_tag=True)

            nertags=ner.predict(queries[i])
            tags=[x[1] for x in nertags]
            writer.writerow([queries[i],intents[i], keywords, tags, result])
        i+=1
        
    f.close()
    print('result:',cnt,'per',data.shape[0], '=',1 - cnt/data.shape[0])


def ner_test():
    print(p.pos("부리또 주문할게요"))
    print(ner.predict("부리또 주문할게요"))


def abb_menu(tagword, menu):
        mod_menu={}
        for cat_name, cat_list in menu.items():
            print(cat_list)
            for food in cat_list:
                if tagword in food['rec_cat']:
                    if cat_name in mod_menu.keys():
                        mod_menu[cat_name].append(food)
                    else:
                        mod_menu[cat_name]=[]
                        mod_menu[cat_name].append(food)
        return mod_menu



def display_menu(menu, answer):
    adder=''
    for cat_name, cat_list in menu.items():
        adder+=f"\n{cat_name}:"
        for food in cat_list:
            adder+=f"\n{food['name']} : {food['price']}\n{food['text']}"

    answer+=adder
    return answer

intent_test()
#ner_test()

#samples=['커플이 먹을만한 메뉴 추천해줘', '가족 메뉴 추천해줘', '단체 메뉴 추천해줘', '제일 잘나가는게 뭐야?','아이들 먹을만한 메뉴 추천' '비건 메뉴 추천', '채식 메뉴 있어?', '키즈 메뉴 추천']
#samples=['두시에 세명 예약해줘', '1 2 3 4 5 6 7 8 9 ']

#mod=abb_menu(tagword='가족', menu=intent.menu)
#print(mod)

samples=['구아카몰라이브', '치폴레화이타치킨싸이','콜라', '빅 플래터', '보더 샘플러', '커플 세트 B', '허니 치폴레 쉬림프', '프리타스 피쉬 & 칩스', '보더윙', '구아카몰 라이브', '엠파나다', '구아카몰 볼', '퀘소볼', '샐러드', '그릴드 멕시칸 콘', '그릴드멕시칸콘', '시즐링 화이타 샐러드', '타코 샐러드', '콥샐러드', '하우스샐러드', '하우스 샐러드', '보더볼', '스프', '비프 타코 라이스', '쉬림프 & 소시지 포솔레', '치킨 또띠아 수프', '스테이크', '립아이 스테이크 & 쉬림프', '메가 쉬림프 화이타', '콰트로 하이타', '콰트로 화이타', '텍사스 바비큐 폭립', '얼티밋 화이타', '치폴레 화이타_치킨 싸이', '치폴레 화이타 치킨 싸이', '치폴레 화이타', '몬트레이 랜치 치킨 화이타', '메스퀴드 그릴 화이타', '랜칠라다', '더블 스텍 클럽 퀘사디아', '화이타 퀘사디아', '폴드포크 퀘사디아', '타코', '카르네 아사다 스테이크 타코', '허니 치폴레 쉬림프 타코', '사우스 웨스트 치킨 타코', '폴드포크 타코', '쓰리 소스 화이타 부리또', '치미창가', '클래식 부리또', '델리오', '엘파소', '슈페리어', '토마토 함박 스테이크', '함박 스테이크앤 필라프', '키즈 퀘사디아', '치킨 텐더', '토마토 스파게티', '파스타', '피쉬 & 칩스 세트', '빅플래터 세트', '패밀리세트 D', '패밀리세트 C', '커플 세트 A', '커플 세트 B', '트리플 머시룸 버거', 'OTB 구아카몰 버거', 'OTB 블랑코 퀘소 버거', '스리라차 치킨 버거', '프레즐 치즈케이크', '보더 브라우니 썬데', '츄러스', '아이스크림', '쏘빠삐야', '츄러스 & 아이스크림', '마가리타', '스페셜리타', '맥주', '데킬라', '와인', '무알콜 드링크', '무알콜음료', '필라프', '사이다', '감튀', '플레터', '셍맥주', '셍맥', '레드와인', '화이트와인', '피시앤칩스', '치킨텐더', '구아카몰라이브', '그릴드멕시칸콘', '쉬림프앤소세지', '라이스', '필라프', '치폴레화이타치킨싸이']


#for sent in samples:
#    analyse_sent(sent)

#for sent in samples:
#    pos = p.pos(sent)
#    keywords = p.get_keywords(pos, without_tag=True)
#    print(sent,keywords)

#print(display_menu(intent.menu, ''))