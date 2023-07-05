#작업 플로우:
#test2.py를 돌리면 현재 모델의 정확도가 나옴. 현재 정확도 0.922
#"오답노트"가 false_note.csv에 저장됨. 
#형태소 분리가 잘못되어있다면 user_dic.txt에 형태소 업데이트
#원하는 키워드를 아래 모델에 자유롭게 입력하여 모델 업데이트. 

#단, 현 시점에서 각 라벨링의 우선도/순서는 모두 계산되어 매겨져있는 상황임. 같은 키워드가 주문, 추천, 안내나 문의, 정보요청 등에 중복으로 사용될 여지가 충분히 있다는걸 확실히 인지하고 단어를 배치해야하며
#같이 사용되는 단어, NER태그등의 조건도 복합적으로 고려해서 매겨져야 함. NER 태그 정보가 온다면, 해당 정보를 받아서 intent 모델을 완성하는 것이 더 완성도 높은 의도모델이 될 것으로 보임.

#최종 목표는 오답노트를 비우는 것이겠으나... 일부는 라벨링이 모호한 경우도 있고, 기타의 경우 분류가 불가능해 보이는 것도 보임. (이경우는 NER 태그가 와야 해결이 될 것으로 보임)

import json

# 의도 분류 모델 모듈
class IntentModel:
    def __init__(self, proprocess, nermodel, customer):

        with open('menu.json', 'r', encoding='utf-8') as f:
            self.menu=json.load(f)
        self.submenu=[]
        for cat in self.menu.values():
            for food in cat:
                self.submenu.append(food["name"])

        with open('train_tools/qna/branch.json', 'r', encoding='utf-8') as brc:
            self.brch=json.load(brc)
        self.brcsubs=[]
        for brc in self.brch:
            self.brcsubs+=brc['name']

        
        # 챗봇 Preprocess 객체
        self.p = proprocess
        self.nermodel = nermodel
        self.drinks=["논알콜 푸룻 마가리타","프레쉬 에이드","하리토스","페리에","소프트 드링크","커피","홍차","레드 와인","화이트 와인","생맥주","멕시코맥주","크래프트맥주","콜라","사이다","환타"]
        self.submenu+=self.drinks
        #레이블별 단어그룹
        self.greet_words=["헬로우", "헬로", "인사", "안녕", "안녕하세요", "반갑", "반가", "하이", "좋은 아침", "지내", "안녕히", "반갑습니다", "봄"]
        self.menu_words=["메뉴판", "전체 메뉴", "매뉴판", "전체"]
        self.menu_words2=["알리", "확인", "궁금", "알", "뭐", "정보", "띄우", "보이"] #메뉴와 같이 사용되는 단어
        self.menu_words3=["메뉴", "매뉴"] #메뉴와 같이 사용되는 단어
        self.order_words=["주문","선택","시키","주문ㄱㄱ", "시킬", "방문 주문", "방문 포장"]
        self.reserv_words=["예약", "조정", "변경", "취소", "신청","방문", "미루","못하","미루워","캔슬"]
        self.reserv_words_sub=['취소', '못하', '미루', '미루워', '캔슬', '조정']
        self.rec_words=["추천", "인기", "같이", "키즈", "가족", "커플", "어린이", "적당", "괜찮", "맛있", "많이", "혼자", "혼밥", "비건", "베지테리언", "채식"]
        self.rec_words_sub=["키즈", "가족", "커플", "혼밥", "비건", "베지테리언", "채식", "어린이"]
        self.rec_words2=["어떤"]
        self.help_words=["문의", "민원", "상담원", "고객", "센터", "서비스","지원","멤버","환불", "혜택" "비밀번호", "아이디", "회원", "수신거부", "고객만족도", "기념일", "생일", "쿠폰", "재결제", "상품권"] #FAQ류 질문이 많으므로, 1:1대응되는 답변을 많이 준비해야함
        self.help_words2=["질문", "궁금", "물어보", "알리"] #FAQ류 질문이 많으므로, 1:1대응되는 답변을 많이 준비해야함
        self.event_words=["할인", "프로모션", "이벤트", "행사"]
        self.info_words=["주차", "주차장", "교통", "주소", "전화번호", "전화", "매장", "위치", "번호", "어디", "지점", "점포", "식당"]

        self.amb=["싶", '주문'] #주문, 추천, 안내중 애매한  #구체적 메뉴명 +싶이면 주문으로, 아니면 추천으로 받음
        self.ordercancel=["취소", '변경'] #장바구니에 있는 메뉴룰 취소하기 위함

        #self.exact_menu_name=['구아카몰라이브', '치폴레화이타치킨싸이','콜라', '빅 플래터', '보더 샘플러', '커플 세트 B', '허니 치폴레 쉬림프', '프리타스 피쉬 & 칩스', '보더윙', '구아카몰 라이브', '엠파나다', '구아카몰 볼', '퀘소볼', '샐러드', '그릴드 멕시칸 콘', '그릴드멕시칸콘', '시즐링 화이타 샐러드', '타코 샐러드', '콥샐러드', '하우스샐러드', '하우스 샐러드', '보더볼', '스프', '비프 타코 라이스', '쉬림프 & 소시지 포솔레', '치킨 또띠아 수프', '스테이크', '립아이 스테이크 & 쉬림프', '메가 쉬림프 화이타', '콰트로 하이타', '콰트로 화이타', '텍사스 바비큐 폭립', '얼티밋 화이타', '치폴레 화이타_치킨 싸이', '치폴레 화이타 치킨 싸이', '치폴레 화이타', '몬트레이 랜치 치킨 화이타', '메스퀴드 그릴 화이타', '랜칠라다', '더블 스텍 클럽 퀘사디아', '화이타 퀘사디아', '폴드포크 퀘사디아', '타코', '카르네 아사다 스테이크 타코', '허니 치폴레 쉬림프 타코', '사우스 웨스트 치킨 타코', '폴드포크 타코', '쓰리 소스 화이타 부리또', '치미창가', '클래식 부리또', '델리오', '엘파소', '슈페리어', '토마토 함박 스테이크', '함박 스테이크앤 필라프', '키즈 퀘사디아', '치킨 텐더', '토마토 스파게티', '파스타', '피쉬 & 칩스 세트', '빅플래터 세트', '패밀리세트 D', '패밀리세트 C', '커플 세트 A', '커플 세트 B', '트리플 머시룸 버거', 'OTB 구아카몰 버거', 'OTB 블랑코 퀘소 버거', '스리라차 치킨 버거', '프레즐 치즈케이크', '보더 브라우니 썬데', '츄러스', '아이스크림', '쏘빠삐야', '츄러스 & 아이스크림', '마가리타', '스페셜리타', '맥주', '데킬라', '와인', '무알콜 드링크', '무알콜음료', '필라프', '사이다', '감튀', '플레터', '셍맥주', '셍맥', '레드와인', '화이트와인', '피시앤칩스', '치킨텐더', '구아카몰라이브', '그릴드멕시칸콘', '쉬림프앤소세지', '라이스', '필라프', '치폴레화이타치킨싸이']
        #self.exact_menu_name+=self.submenu
        self.exact_menu_name=self.submenu
        #self.vague_menu_name=['음료수', '탄산', '탄산음료', '라이스', '타코', '세트메뉴', '화이타', '햄버거', '버거', '세트', '플레터', "라이스", "수프", "스테이크","샐러드","화이타","퀘사디아","타코","부리또","버거","디저트","드링크","음료수"]
        self.vague_menu_name=["라이스", "수프", "스테이크","샐러드","화이타","퀘사디아","타코","부리또","버거","디저트","드링크","음료수"]
        self.vague_menu_name+=self.menu.keys()
        self.extra_food=['마라탕','바나나', '사과', '샤브샤브', '핫소스', '플레터', '샘플러', '초밥', '뇨끼', '짜장면', '라자냐', '치킨', '피자', '캐밥', '카레', '김치찌개', '돈까스', '꿔바로우', '타코샐러드', '파히타', '찜닭', '수박', '스무디', '환타', '메인메뉴', '소고기', '돈가스', 'A세트', 'B세트', '쉬림프', '소세지','수제버거']

        self.branch=['에버랜드점', '온더보드 에버랜드점', '온더보더 에버랜드점', '광명점', '광명 AK점', '광명AK점', '현대백화점', '현대백화점 중동점', '중동점', '현대 디큐브시티점', '디큐브시티점', '수원점', '수원 AK점', '도심공항점', '코엑스 도심공항점', '코엑스도심공항점', '코엑스점', '여의도점', '여의도 IFC점', '롯데월드몰점', '롯데월드점', '타임스퀘어점', '스타필드점', '스타필드 하남점', '하남점', '롯데몰점', '김포공항점', '롯데몰 김포공항점', '부산점', '부산 삼정타워점', '대전점', '현대프리미엄아울렛 대전점', '현대 프리미엄 아울렛 대전점']
        self.branch+=self.brcsubs
        #CV_FOOD, CV_DRINK+기타인 경우 주문으로 받음. 
        #구체적 메뉴명 +싶이면 주문으로, 아니면 추천으로 받음  "콜라를 마시고싶은데."=주문, "음료수를 마시고 싶은데"=추천, 음료수 선택지를 띄워줌.

          


    # 의도 클래스 예측
    def predict_class(self, query):
        def class_check(word_group, keywords):
            for word in word_group:
                if word in keywords:
                    return True
            return False
 
        # 형태소 분석
        pos = self.p.pos(query)
        # 문장내 키워드 추출(불용어 제거)
        keywords = self.p.get_keywords(pos, without_tag=True)
        nertags=self.nermodel.predict(query)
        tags=[x[1] for x in nertags]


        if 'QT' in tags and 'PS' in tags and '메뉴' in keywords: #몇명이서 먹을만한 메뉴 알려줘
            return "메뉴추천"
        elif "가깝" in keywords:
            return "매장정보"
        elif class_check(self.menu_words, keywords):
            return "메뉴안내"
        elif class_check(self.menu_words2, keywords) and class_check(self.menu_words3, keywords): #메뉴판 띄우기
            return "메뉴안내"
        elif class_check(self.rec_words, keywords):
            return "메뉴추천"
        elif '먹' in keywords and '만' in keywords: #먹을만한 메뉴~
            return "메뉴추천"
        elif class_check(self.submenu, keywords) and class_check(self.ordercancel, keywords):
            return "주문취소"
        elif class_check(self.reserv_words, keywords):
            return "예약"
        elif class_check(self.amb, keywords) and class_check(self.exact_menu_name, keywords): #구체적 메뉴명 +싶이면 주문으로, 아니면 추천으로 받음
            return "주문"
        elif class_check(self.branch, keywords):
            return "매장정보"
        elif class_check(self.event_words, keywords):
            return "이벤트정보"
        elif class_check(self.help_words, keywords):
            return "매장문의"
        elif '몇' in keywords and '시' in keywords: #매장 시간에 대한 안내
            return "매장문의"
        elif class_check(self.info_words, keywords):
            return "매장정보"
        elif class_check(self.help_words2, keywords):
            return "매장문의"
        elif class_check(self.rec_words2, keywords): #어떤
            return "메뉴추천"
        elif class_check(self.greet_words, keywords):
            return "인사"
        elif class_check(self.exact_menu_name, keywords): #구체적인 메뉴 이름을 말했다면 주문으로 넘어감
            if "뭐" in keywords or "얼마" in keywords:
                return "메뉴안내"
            else:
                return "주문"
        elif class_check(self.vague_menu_name, keywords): #대략적인 메뉴 이름을 말하면 추천으로 넘어감
            if "뭐" in keywords:
                return "메뉴안내"
            else:
                return "메뉴추천"
        elif class_check(self.extra_food, keywords): #없는 메뉴를 말했을 경우 없다는 답변을 내놓을 것.
            return "주문"
        elif class_check(self.order_words, keywords):
            return "주문"
        
        

        return "기타"


# 의도 클래스 보조단어 출력
    def detailed_class_check(self, query):
        def class_check(word_group, keywords):
            for word in word_group:
                if word in keywords:
                    return True
            return False
        
        def return_word(word_group, keywords):
                for word in word_group:
                    if word in keywords:
                        return word
                return None
        
        def return_QT(nertags):
                for word, tag in nertags:
                    if tag=='QT':
                        return word
                return None
        # 형태소 분석
        pos = self.p.pos(query)
        # 문장내 키워드 추출(불용어 제거)
        keywords = self.p.get_keywords(pos, without_tag=True)
        nertags=self.nermodel.predict(query)
        tags=[x[1] for x in nertags]


        if 'QT' in tags and 'PS' in tags and '메뉴' in keywords: #몇명이서 먹을만한 메뉴 알려줘
            return return_QT(nertags)
        elif "가깝" in keywords:
            return "가깝"
        elif class_check(self.menu_words, keywords):
            return "전체"
        elif class_check(self.menu_words2, keywords) and class_check(self.menu_words3, keywords): #메뉴판 띄우기
            return "전체"
        elif class_check(self.rec_words, keywords):
            return return_word(self.rec_words_sub, keywords)
        elif '먹' in keywords and '만' in keywords: #먹을만한 메뉴~
            return return_word(self.rec_words_sub, keywords)
        elif class_check(self.submenu, keywords) and class_check(self.ordercancel, keywords):
            return None
        elif class_check(self.reserv_words, keywords):
            return return_word(self.reserv_words_sub, keywords)
        elif class_check(self.amb, keywords) and class_check(self.exact_menu_name, keywords): #구체적 메뉴명 +싶이면 주문으로, 아니면 추천으로 받음
            return None
        elif class_check(self.branch, keywords):
            return return_word(self.info_words, keywords)
        elif class_check(self.event_words, keywords):
            return None
        elif class_check(self.help_words, keywords):
            return return_word(self.help_words, keywords)
        elif '몇' in keywords and '시' in keywords: #매장 시간에 대한 안내
            return "이용시간"
        elif class_check(self.info_words, keywords):
            return return_word(self.info_words, keywords)
        elif class_check(self.help_words2, keywords):
            return return_word(self.help_words, keywords)
        elif class_check(self.rec_words2, keywords): #어떤
            return return_word(self.rec_words_sub, keywords)
        elif class_check(self.greet_words, keywords):
            return None
        elif class_check(self.exact_menu_name, keywords): #구체적인 메뉴 이름을 말했다면 주문으로 넘어감
            if "뭐" in keywords or "얼마" in keywords:
                return return_word(['뭐','얼마'], keywords)
            else:
                return None
        elif class_check(self.vague_menu_name, keywords): #대략적인 메뉴 이름을 말하면 추천으로 넘어감
            if "뭐" in keywords:
                return None
            else:
                return return_word(self.vague_menu_name, keywords)
        elif class_check(self.extra_food, keywords): #없는 메뉴를 말했을 경우 없다는 답변을 내놓을 것.
            return None
        elif class_check(self.order_words, keywords):
            return None
        

        return "기타"



