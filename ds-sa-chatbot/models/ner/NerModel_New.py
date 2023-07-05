import json

#주요 개체명:
#B_FOOD, LC(장소), OG(기관), QT(용량), PS(사람), DT(Datetime), TI(시간)

# 개체명 인식 모델 모듈
class NerModel:
    def __init__(self, proprocess):

        # NER 태그 사전 불러오기
        with open('models/ner/ner2021_compressed.json', 'r') as f:
            self.nerdict = json.load(f)

        # 챗봇 Preprocess 객체
        self.p = proprocess

    # 개체명 클래스 예측
    def predict(self, query):
        def filt(inp):
            if inp=="CV_FOOD" or inp=="CV_DRINK":
                return "B_FOOD"
            elif inp=="O":
                return inp
            else:
                return inp[:2]
        # 형태소 분석
        pos = self.p.pos(query)

        # 문장내 키워드 추출(불용어 제거)
        keywords = self.p.get_keywords(pos, without_tag=True)
        tags = []
        for word in keywords:
            if word in self.nerdict.keys():
                tags.append(filt(self.nerdict[word]))
            else:
                tags.append('O')

        return list(zip(keywords, tags))

    def predict_tags(self, query):
        def filt(inp):
            if inp=="CV_FOOD" or inp=="CV_DRINK":
                return "B_FOOD"
            elif inp=="O":
                return inp
            else:
                return inp[:2]
        # 형태소 분석
        pos = self.p.pos(query)

        # 문장내 키워드 추출(불용어 제거)
        keywords = self.p.get_keywords(pos, without_tag=True)

        tags = []
        for word in keywords:
            if word in self.nerdict.keys():
                tags.append(filt(self.nerdict[word]))
            else:
                tags.append('O')

        if len(tags) == 0: return None
        return tags

