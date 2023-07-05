import threading
import json

from config.DatabaseConfig import *
from utils.Database import Database
from utils.BotServer import BotServer
from utils.PreprocessW2V import PreprocessW2V as Preprocess
from models.intent.IntentModel_New import IntentModel
from models.ner.NerModel_New import NerModel
from utils.FindAnswer import FindAnswer
from customer import Customer

# 전처리 객체 생성
p = Preprocess(w2v_model='ko_with_corpus_mc1_menu_added.kv', userdic='utils/user_dic.txt')

# 개체명 인식 모델
ner = NerModel(proprocess=p)

cust=Customer()

# 의도 파악 모델
intent = IntentModel(proprocess=p, nermodel=ner, customer=cust)

wordtonum={
    "두":2, "세":3, "네":4,"다섯":5,"여섯":6,"일곱":7,"여덟":8,"아홉":9,"열":10
}


def to_client(conn, addr, params):
    db = params['db']

    try:
        db.connect()  # 디비 연결

        # 데이터 수신
        read = conn.recv(2048)  # 수신 데이터가 있을 때 까지 블로킹
        print('===========================')
        print('Connection from: %s' % str(addr))

        if read is None or not read:
            # 클라이언트 연결이 끊어지거나, 오류가 있는 경우
            print('클라이언트 연결 끊어짐')
            exit(0)


        # json 데이터로 변환
        recv_json_data = json.loads(read.decode())
        print("데이터 수신 : ", recv_json_data)
        query = recv_json_data['Query']

        # 의도 파악
        intent_name = intent.predict_class(query)
        tagword=intent.detailed_class_check(query)

        # 개체명 파악
        ner_predicts = ner.predict(query)


        # 답변 검색
        try:
            f = FindAnswer(db)
            answer, answer_code = f.search(intent_name, ner_predicts)
            if answer_code=="22":
                answer=''
                tempbag=''
                checker=0
                for word, tag in ner_predicts:
                    if checker==1:
                        if tag=="QT":
                            num=f.to_number(word)
                            cust.put_item(tempbag, num)
                            answer+=tempbag+' '+str(num)+', '
                            tempbag=''
                        else:
                            cust.put_item(tempbag, 1)
                            answer+=tempbag+', '
                            tempbag=''
                        checker=0

                    if word in intent.submenu:
                        tempbag=word
                        checker=1
                if checker==1:
                    cust.put_item(tempbag, 1)
                    answer+=tempbag+', '
                    tempbag=''
   
                if len(answer)!=0:
                    answer=answer[:-2]+" 장바구니에 넣었습니다."
                else:
                    answer = "죄송합니다. 저희 매장에는 없는 메뉴입니다."

            if answer_code=="21":
                tempbag=[]
                for word, tag in ner_predicts:
                    if word in cust.bag:
                        cust.cancel_item(word)
                        tempbag.append(word)

                if len(tempbag)!=0:
                    answer=''
                    for word in tempbag:
                        answer+=word+', '
                    answer=answer[:-2]+" 장바구니에서 제외되었습니다."
                    # 장바구니 정보를 담은 데이터 생성
                    
                else:
                    answer = "해당 메뉴는 장바구니에 없습니다."
                    
            if answer_code=='2':
                if len(cust.bag)!=0:
                    answer='다음 메뉴를 최종 주문합니다.'
                    for item in cust.bag:
                        answer+=f"\n{item}, {cust.numbag[item]}"
                    total=cust.charge()
                    answer+=f"\n총액:{total}원"
                    #주문 내역 보여주기는 디스플레이로 대체 가능하다면 지울것
                else:
                    answer='장바구니에 담긴 메뉴가 없습니다.'

            if answer_code=='4':
                if intent_name=="메뉴안내":
                    search_done=0
                    for word, tag in ner_predicts:
                        if word in intent.submenu:
                            for cat in intent.menu.values():
                                for exactmenu in cat:
                                    if exactmenu['name']==word and search_done==0:
                                        if tagword=="뭐":
                                            answer=exactmenu['text']
                                        if tagword=="얼마":
                                            answer=exactmenu['name']+"의 가격은 "+exactmenu['price']+"원 입니다."
                                        search_done=1
                                        break
                    
                    if search_done==0:
                        answer = "죄송해요 무슨 말인지 모르겠어요. 조금 더 공부 할게요."
                else:
                    answer=f.match_answer(tagword, intent_name, ner_predicts)

            
            if answer_code=='3':
                answer, mod_menu=f.show_menu(tagword, intent.menu)
                #아래 코드는 디스플레이가 마련되면 지울것
                answer=f.display_menu(mod_menu, answer)

            if answer_code=='1':
                if tagword in ['취소', '못하', '미루', '미루워', '캔슬', '조정']:
                    if len(cust.reservation)==0:
                        answer="취소할 수 있는 예약이 없습니다."
                    else: 
                        time, person= f.timeandperson(ner_predicts)
                        answer="해당 시간에 잡힌 예약이 없습니다."
                        for reserv in cust.reservation:
                            if reserv[0]==time:
                                cust.cancel_reserv(time)
                                answer=f"{time}시 예약을 취소하였습니다."
                else:
                    answer=''
                    time, person= f.timeandperson(ner_predicts)
                    if time!=None and person!=None:
                        answer=str(time)+'시 '+str(person)+'명 예약합니다.'
                        cust.reserv(time, person)
                    else:
                        answer="예약창으로 이동합니다. 나머지 정보를 채워주십시오."
                if len(cust.reservation)!=0:
                    answer+=f"\n예약 현황:"
                    for reserv in cust.reservation:
                        answer+=f"\n{reserv[0]}시, {reserv[1]}명"
                    #예약 내역 보여주기는 디스플레이로 대체 가능하다면 지울것
            if answer_code=='5':
                    answer="현재 진행중인 이벤트를 안내드리겠습니다."
                    #이벤트 이미지 첨부


        except:
            answer = "죄송해요 무슨 말인지 모르겠어요. 조금 더 공부 할게요."
            answer_code = None

        cart_data =[]
        for item in cust.bag:
            cart_data.append({"name": item, "quantity": cust.numbag[item]})
        total_price = cust.charge()

        send_json_data_str = {
            "Query" : query,
            "Answer": answer,
            "AnswerCode" : answer_code,
            "Intent": intent_name,
            "Intent_tag": tagword,
            "NER": str(ner_predicts),
            "Menu": [data['name'] for data in cart_data],
            "Num": [data['quantity'] for data in cart_data],
            "Total_price": total_price
        }
        message = json.dumps(send_json_data_str)
        conn.send(message.encode())
        #if answer_code=='3':
        #    menu_to_display = json.dumps(mod_menu)
        #    conn.send(message.encode())


    except Exception as ex:
        print(ex)

    finally:
        if db is not None: # db 연결 끊기
            db.close()
        conn.close()


if __name__ == '__main__':

    # 질문/답변 학습 디비 연결 객체 생성
    db = Database(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, db_name=DB_NAME
    )
    print("DB 접속")

    port = 5050
    listen = 100

    # 봇 서버 동작
    bot = BotServer(port, listen)
    bot.create_sock()
    print("bot start")

    while True:
        conn, addr = bot.ready_for_client()
        params = {
            "db": db
        }

        client = threading.Thread(target=to_client, args=(
            conn,
            addr,
            params
        ))
        client.start()
