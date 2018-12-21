# -*- coding: utf-8 -*-
import json
import os
import re
import time
import multiprocessing as mp
from threading import Thread
from bs4 import BeautifulSoup

#StackClient import
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template

#==========selenium import==========
from selenium import webdriver
import time
#===================================

#======================KAKAO API===========================
import urllib.request
KakaoAK = "KakaoAK 0933ffbc620a742ffcd7ac2b8339dd4e"
#==========================================================


'''=========================================================
    processing_event(메세지 큐)

        Slack 챗봇에 계속 메시지가 전송되어 중복 출력
        현상을 방지하기 위한 메소드
========================================================='''
def processing_event(queue):
   while True:
       # if queue is not empty
       if not queue.empty():
           print('queue pushed!!')
           slack_event = queue.get()

           # Your Processing Code Block gose to here
           if "event" in slack_event:
               event_type = slack_event["event"]["type"]
               _event_handler(event_type, slack_event)


app = Flask(__name__)
#=============================Slack_INFO========================================
slack_token = "xoxb-504131970294-506765311072-7bgjaZXiEC5apf1Gli1CdFL6"
slack_client_id = "504131970294.508901295270"
slack_client_secret = "5781449a3d89bfc010eaf0c2b26b4afe"
slack_verification = "ecpN944Tp1XITArTp2po3gdU"
sc = SlackClient(slack_token)
#===============================================================================

#error 처리문 변수
current_client_msg_id = ""
errMsg = "입력형식을 정확하게 해주세요. :( \n *EX: 구미, 구미 미세먼지*"

#==========================selenium browser=====================================
browser = webdriver.Chrome('./chromedriver.exe')
browser.implicitly_wait(3)
#===============================================================================


'''=========================================================
    KAKAO API
    
        KAKAO 검색 API를 사용하여 검색 결과(URL)을 제공해줌
========================================================='''
def kakaoAPIsearching(search_text):

    ret = []
    ret.append("*"+ search_text + " 검색결과를 알려드릴게요!*\n\n")
    encText = urllib.parse.quote(search_text)
    url = "https://dapi.kakao.com/v2/search/web?query=" + encText

    request = urllib.request.Request(url)

    request.add_header("Authorization", KakaoAK)
    response = urllib.request.urlopen(request)
    rescode = response.getcode()
    if (rescode == 200):
        response_body = response.read()

        json_response_body = json.loads(response_body.decode('utf-8'))
        for element in json_response_body['documents']:
            ret.append("*" + re.sub('<.+?>', '', element['title'], 0, re.I | re.S) + "*")
            ret.append(re.sub('<.+?>', '', element['url'], 0, re.I | re.S) + "\n")
    else:
        print("Error Code:" + rescode)

    return ret


'''====================================================
    getWeatherInfo(날씨정보, 지역)

        오늘 날씨 데이터를 불러오고 저장하는 메소드
===================================================='''
def getWeatherInfo(weather, area):

    ret = []

    # 온도와 부가정보 솎아내기
    temperature = weather.find("p", class_="info_temperature")
    dataList = weather.find("ul", class_="info_list")

    temperature = temperature.get_text().strip()
    dataList = list(dataList.get_text().strip().split())

    # 데이터 변수에 저장
    ment = dataList[0] + " " + dataList[1] + " " + dataList[2] + "\n"
    high_low_temp = "최저/최고온도 : " + dataList[3]
    sensible_temp = dataList[4] + " : " + dataList[5]
    uv = dataList[6] + " : " + dataList[7]

    # 결과 리스트에 저장
    ret.append("\t*오늘 " + area + "의 기후 정보를 알려드릴께요! :)*\n")
    ret.append("온도 : " + temperature)
    ret.append(ment)
    ret.append(high_low_temp)
    ret.append(sensible_temp)
    ret.append(uv)

    print(ret)
    return ret

'''====================================================
    getFineDustInfo(미세먼지정보, 지역)

        미세먼지 데이터를 불러오고 저장하는 메소드
===================================================='''
def getFineDustInfo(misedata, area):

    ret = []

    ment = "*오늘 "+ area + "의 미세먼지 정보를 알려드릴께요! :)*\n"
    dustData = list(misedata.get_text().split())

    print(dustData)

    dust = dustData[0] + " : " + dustData[1]
    microDust = dustData[2] + " : " + dustData[3]
    ozone = dustData[4] + " : " + dustData[5]

    ret.append(ment)
    ret.append(dust)
    ret.append(microDust)
    ret.append(ozone)

    print(ret)
    return ret

'''====================================================
    tommorowWeather(내일과모레 날씨정보, 지역)

        내일과 모레 날씨 정보를 알려주는 메소드
===================================================='''
def tommorowWeather(nextWeather, key):

    ret = []
    times = 0

    ret.append("*"+key+"의 내일과 모레 날씨를 알려드릴게요! :)*\n")
    ret.append("_*내일*_")
    for element in nextWeather:

        if(times == 2):
            ret.append("_*모레*_")
        ret.append(element.get_text().strip())
        times += 1

    return ret

'''====================================================
    _WeatherBot_Func(사용자입력정보)

        사용자가 입력한 정보를 분석하여 처리하는 메소드
===================================================='''
def _WeatherBot_Func(text):
    global browser

    #area = 대구 or 대구 미세먼지
    keys = text.split()
    select = len(keys)
    keywords = []

    print(keys)

    #사용자가 입력한 내용중 검색이라는 키워드가 들어가 있을경우
    if(keys[1] == "검색"):
        try:
            keywords = kakaoAPIsearching(keys[2])
        except Exception:
            keywords.append("검색내용을 정확하게 입력해주세요! :( \n"
                            + "*EX: 검색 검색할내용*")
        return u'\n'.join(keywords)

    #사용자가 입력한 내용이 형식에 맞는지 확인하는 부분
    #ex) 구미, 구미 날씨, 구미 내일
    if(len(keys) == 3):

        if(keys[2] == "내일"):
            key = keys[1] + " 내일 날씨"
        elif(keys[2] == "미세먼지"):
            key = keys[1] + " 날씨"
        else:
            keywords.append(errMsg)
            return u'\n'.join(keywords)
    elif(len(keys) == 2):
        key = keys[1] + " 날씨"
    else:
        keywords.append(errMsg)
        return u'\n'.join(keywords)

    # selenium 관련 데이터
    browser.get("http://naver.com")

    #브라우저에 데이터 입력
    browser.find_element_by_name('query').clear()
    browser.find_element_by_name('query').send_keys(key)
    browser.find_element_by_id('search_btn').click()

    sourcecode = browser.page_source
    soup = BeautifulSoup(sourcecode, "html.parser")

    if select == 2:

        # 도시 검사 후
        try:
            weatherData = soup.find("div", class_="main_info")
            weatherData = weatherData.find("div", class_="info_data")
            keywords = getWeatherInfo(weatherData, key)

        except Exception:
            keywords.append(errMsg)
            return u'\n'.join(keywords)
    elif select == 3:

        # 도시 검사 후
        try:

            if(keys[2] == "내일"):

                print("아니?")
                nextWeather = soup.find_all("div", class_="main_info morning_box")

                type(nextWeather)
                print(nextWeather)

                if len(nextWeather) != 0:
                    keywords = tommorowWeather(nextWeather, key.split()[0])
                else:
                    keywords.append(errMsg)
                    return u'\n'.join(keywords)
            else:
                misedata = soup.find("div", class_="sub_info")
                misedata = misedata.find("dl", class_="indicator")
                keywords = getFineDustInfo(misedata, key)

        except Exception:
            keywords.append(errMsg)
            return u'\n'.join(keywords)
    else:
        keywords.append("입력형식을 정확하게 해주세요. :(")

    return u'\n'.join(keywords)

# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    global current_client_msg_id

    print(slack_event["event"])

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]

        print(current_client_msg_id)
        print(current_client_msg_id != slack_event["event"]['client_msg_id'])

        keywords = _WeatherBot_Func(text)

        # 결과가 담겨있는 리스트 포맷팅
        formatted_text = [{
            "text": keywords,
            "mrkdwn": True,
            "color": "#FF0000"
        }]

        sc.api_call(
            "chat.postMessage",
            channel=channel,
            attachments=formatted_text
        )

@app.route("/listening", methods=["GET", "POST"])
def hears():
   global event_queue
   slack_event = json.loads(request.data)

   if "challenge" in slack_event:
       return make_response(slack_event["challenge"], 200, {"content_type":
                                                                "application/json"
                                                            })

   if slack_verification != slack_event.get("token"):
       message = "Invalid Slack verification token: %s" % (slack_event["token"])
       make_response(message, 403, {"X-Slack-No-Retry": 1})

   # 슬랙 챗봇이 대답한다
   print(slack_event)
   if "event" in slack_event and slack_event["event"]["type"] == "app_mention":
       # push slack_event to event_queue
       event_queue.put(slack_event)

       return make_response("App mention message has been sent", 200, )

   # 이 외 해당하지 않는 이벤트나 에러는 다음과 같이 리턴한다.
   return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                        you're looking for.", 404, {"X-Slack-No-Retry": 1})


@app.route("/", methods=["GET"])
def index():
   return "<h1>Server is ready.</h1>"


if __name__ == '__main__':
   event_queue = mp.Queue()

   p = Thread(target=processing_event, args=(event_queue,))
   p.start()
   print("subprocess started")

   app.run('0.0.0.0', port=8080)
   p.join()