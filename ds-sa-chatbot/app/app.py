# coding = utf-8

from flask import Flask, render_template, request
import socket
import os
import json
from flask_cors import cross_origin

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
@cross_origin()
def connect():
    if request.method == 'POST':
        query = request.form['message']
        print(query)
        #POST 형식으로 전송된 값을 value에 저장
        host = "127.0.0.1"  # 챗봇 엔진 서버 IP 주소
        port = 5050  # 챗봇 엔진 서버 통신 포트
        mySocket = socket.socket()
        mySocket.connect((host, port))
        if query != "":
            # 챗봇 엔진 질의 요청
            json_data = {
                'Query': query,
                'BotType': "MyService"  
            }
            message = json.dumps(json_data)
            mySocket.send(message.encode())

            # 챗봇 엔진 답변 출력
            data = mySocket.recv(5000).decode() # 원래 2048 # 낮추면 json이 길 경우 전부 전송을 못받고 끊겨서 오류가 나는 경우가 있다.
            print(data)
            ret_data = json.loads(data)
            print(ret_data)
            # answer = ret_data['Answer']
            # answer_code = ret_data['AnswerCode']
            # print(answer_code)

            # 챗봇 엔진 서버 연결 소켓 닫기
            mySocket.close()
            return data # 답변 json을 전송


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))