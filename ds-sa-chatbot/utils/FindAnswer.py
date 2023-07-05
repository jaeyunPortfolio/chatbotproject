import json
import re

class FindAnswer:
    def __init__(self, db):
        self.db = db
        with open('train_tools/qna/faq.json', 'r', encoding='utf-8') as f:
            self.faq=json.load(f)
        with open('train_tools/qna/branch.json', 'r', encoding='utf-8') as br:
            self.branch=json.load(br)

    # 검색 쿼리 생성
    def _make_query(self, intent_name, ner_predicts):
        sql = "select * from chatbot_train_data"
        if intent_name != None and ner_predicts == None:
            sql = sql + " where intent='{}' ".format(intent_name)

        elif intent_name != None and ner_predicts != None:
            where = ' where intent="%s" ' % intent_name
            if (len(ner_predicts) > 0):
                where += 'and ('
                for word, ne in ner_predicts:
                    if ne!='O': #'O'인 경우는 제외
                        where += " ner like '%{}%' or ".format(ne)
                where = where[:-3] + ')'
            sql = sql + where

        # 동일한 답변이 2개 이상인 경우, 랜덤으로 선택
        sql = sql + " order by rand() limit 1"
        return sql

    # 답변 검색
    def search2(self, intent_name, ner_predicts):
        # 의도명, 개체명으로 답변 검색
        sql = self._make_query(intent_name, ner_predicts)
        answer = self.db.select_one(sql)

        # 검색되는 답변이 없으면 의도명만 검색
        if answer is None:
            sql = self._make_query(intent_name, None)
            answer = self.db.select_one(sql)

        answer_sent=answer['answer']
        #ner tag를 원래 단어로 변환
        for word, tag in ner_predicts:

            # 변환해야하는 태그가 있는 경우 추가
            if tag == 'B_FOOD':
                answer_sent = answer_sent.replace(tag, word)

        answer_sent = answer_sent.replace('{', '')
        answer_sent = answer_sent.replace('}', '')

        return (answer_sent, answer['answer_code'])
    
    # 답변 검색
    def search(self, intent_name, ner_predicts):
        answer=None
        answer_code=None

        if intent_name=="인사":
            answer="네 안녕하세요 :D\n반갑습니다. 온더보더입니다."
        if intent_name=="예약":
            answer_code='1'
        if intent_name=="주문취소":
            answer_code='21'
        if intent_name=="주문":
            answer_code='2'
            for word, tag in ner_predicts:
                if tag=="B_FOOD":
                    answer_code='22'
        if intent_name=="메뉴추천":
            answer_code='3'
        if intent_name=="메뉴안내":
            answer_code='3'
            for word, tag in ner_predicts:
                if word=="뭐" or word =="얼마":
                    answer_code='4'
        if intent_name=="매장문의" or intent_name=="매장정보":
            answer_code='4'
        if intent_name=="이벤트정보":
            answer_code='5'

        return (answer, answer_code)
    
    #지점 faq 답 생성
    def make_sentence(self, exactname, info, keytag):

        if keytag=="parking":
            answer=f"{info}"
        elif keytag=="transportation":
            answer=f"{info}"
        elif keytag=="location":
            answer=f"{exactname}점의 주소는 {info}입니다."
        elif keytag=="phone":
            answer=f"{exactname}점의 전화번호는 {info}입니다."
        elif keytag=="time":
            answer=f"{exactname}점의 영업시간은 {info}입니다."
        return answer


    #faq 답 생성
    def match_answer(self, tagword, intent, ner_predicts):

        if intent=="매장정보":
            answer="매장별 번호, 주차, 교통, 위치 등 기본 정보는 홈페이지의 매장 탭에 안내되어있으니 참고 부탁드립니다." #기본 메시지
            keytag='default'
            if tagword in ["주차", "주차장"]: 
                keytag="parking"
            elif tagword in ["교통"]: 
                keytag="transportation"
            elif tagword in ["주소", "위치"]: 
                keytag="location"
            elif tagword in ["전화", "번호", "전화번호"]: 
                keytag="phone"
            elif tagword in ["이용시간"]: 
                keytag="time"
            elif tagword in ['가깝']:
                answer="여기서 가장 가까운 매장은 코엑스 도심공항점입니다."

            if keytag!='default':
                for word, tag in ner_predicts:
                    for brch in self.branch:
                        if word in brch["name"]:
                            exactname=brch['exactname']
                            info=brch[keytag]
                answer=self.make_sentence(exactname, info, keytag)

        if intent=="매장문의":
            answer = "상담원 연결을 도와드리겠습니다. 잠시만 기다려주세요." #기본 메시지
            if tagword in self.faq.keys():
                answer=self.faq[tagword]

        return answer
    

    def abb_menu(self, tagword, menu):
        mod_menu={}
        for cat_name, cat_list in menu.items():
            for food in cat_list:
                if tagword in food['rec_cat']:
                    if cat_name in mod_menu.keys():
                        mod_menu[cat_name].append(food)
                    else:
                        mod_menu[cat_name]=[]
                        mod_menu[cat_name].append(food)
        return mod_menu


    def show_menu(self, tagword, menu):
        wordtonum={ "두":"2", "세":"3", "네":"4","다섯":"5","여섯":"6","일곱":"7","여덟":"8","아홉":"9","열":"10"}
        if tagword in wordtonum.keys():
            tagword=wordtonum[tagword]
        answer=''

        if tagword=="전체":
            #전체
            mod_menu={}
            for cat_name, cat_list in menu.items():
                for food in cat_list:
                    food = dict({'name':food['name'], 'price':food['price'], 'text':''})
                    if cat_name in mod_menu.keys():
                        mod_menu[cat_name].append(food)
                    else:
                        mod_menu[cat_name]=[]
                        mod_menu[cat_name].append(food)
            answer="전체 메뉴 카테고리를 준비해드리겠습니다."
        elif tagword in ["2","3","4","5","6","7","8","9","10"]:
            #인원
            mod_menu=self.abb_menu(tagword, menu)     
            answer=f"{tagword}명 추천 메뉴는 다음과 같이 준비되어있습니다.<br>"
        elif tagword in ["키즈", "가족", "커플", "혼밥", "비건", "베지테리언", "채식", "어린이"]:
            #태그
            mod_menu=self.abb_menu(tagword, menu)     
            answer=f"{tagword} 추천 메뉴는 다음과 같이 준비되어있습니다.<br>"
            if tagword in ["비건", "베지테리언", "채식"]:
                answer = "해당 메뉴는 기본적으로 비건이 아닙니다. 비건 옵션으로 추가 변경이 필요하므로, 직원에게 문의 부탁드립니다.<br>"
        elif tagword in ["라이스", "수프", "스테이크","샐러드","화이타","퀘사디아","타코","부리또","버거","디저트","드링크","음료수"]:
            #카테고리
            mod_menu=self.abb_menu(tagword, menu)     
            answer=f"{tagword}메뉴는 다음과 같이 준비되어있습니다.<br>"
        else:
            #아무것도 아니면 기본 추천메뉴
            mod_menu=self.abb_menu("Best", menu)     
            answer=f"온더보더 베스트 메뉴는 다음과 같이 준비되어있습니다.<br>"

        with open("mod_menu.json", "w", encoding='utf-8') as json_file:
            json.dump(mod_menu, json_file, indent=4, ensure_ascii=False)


        return answer, mod_menu
        
    
    def to_number(self, word):
        wordtonum={ "두":"2", "세":"3", "네":"4","다섯":"5","여섯":"6","일곱":"7","여덟":"8","아홉":"9","열":"10"}
        if word in wordtonum.keys():
            word=wordtonum[word]
        number=int(re.sub(r"[^0-9]", "", word))
        if number=='':
            number=1
        
        return number

    def timeandperson(self, ner_predicts):
        number=''
        time=None
        person=None
        for word, tag in ner_predicts:
            if number!='':
                if word=='시':
                    time=number
                if word in ['명', '분','사람'] or tag=='PS':
                    person=number

            number=''
            if tag=="QT":
                number=self.to_number(word)

            if tag=='TI':
                time=int(re.sub(r"[^0-9]", "", word))

        return time, person


    def display_menu(self, menu, answer):
        adder=''
        for cat_name, cat_list in menu.items():
            adder+=f"<br>{cat_name}:"
            for food in cat_list:
                if food['text'] == "":
                    adder+=f"<br>{food['name']} : {food['price']}<br>{food['text']}"
                else:
                    adder+=f"<br>{food['name']} : {food['price']}<br>{food['text']}<br>"

        answer+=adder
        return answer

    def drink_transform(self, drink):
        if drink in ["논알콜 푸룻 마가리타","프레쉬 에이드","하리토스","페리에","소프트 드링크","커피","홍차", "콜라","사이다","환타"]:
            return "무알콜 드링크"
        if drink in ["레드 와인","화이트 와인"]:
            return "와인"
        if drink in ["생맥주","멕시코맥주","크래프트맥주"]:
            return "맥주"
        return drink

    def phonenum_validity(self, num):
        num=re.sub(r"[-]", "", num)
        if num.startswith("010") and len(num)==11:
            return True
        else:
            return False
    
    def time_validity(self, num):
        mini=11
        maxi=21
        if mini <= num <= maxi:
            return True
        else:
            return False
    
    def person_validity(self, num):
        mini=1
        maxi=10
        if mini <= num <= maxi:
            return True
        else:
            return False

    def name_validity(self, name):
        tmp=re.sub(r"[^가-힣]", "", name)
        if len(name)==0 or len(tmp)!=len(name):
            return False
        else:
            return True