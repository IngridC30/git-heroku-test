# -*- coding: utf-8 -*-

from flask import Flask, request, abort, render_template, Response
from flask import json, jsonify, session, redirect, url_for
#from flask_cors import CORS, cross_origin # for cross domain problem
from flask import send_file

import requests
import csv
import folium
import geocoder

from apscheduler.schedulers.background import BackgroundScheduler
import os

app = Flask(__name__, static_url_path='', static_folder='static')

@app.route("/", methods=['GET'])
def basic_url():
    return 'hello'

@app.route("/hello", methods=['GET'])
def hello():
    name = request.args.get('name')
    return 'hello ' + name

@app.route("/map/kh-parking", methods=['GET'])
def map_kh_parking():
    url = "https://data.kcg.gov.tw/dataset/449e45d9-dead-4873-95a9-cc34dabbb3af/resource/fe3f93da-9673-4f7b-859c-9017d793f798/download/108.6.21.csv"
    r = requests.get(url)
    print(r)
    decoded_content = r.content.decode('utf-8')
    cr = csv.reader(decoded_content.splitlines(), delimiter=',')
    data_list = list(cr)

    # 開始產生地圖
    location = geocoder.osm('高雄市').latlng
    m = folium.Map(location=location, zoom_start=14)
    for item in data_list[1:]:
        try:
            name = item[2]
            total = item[7]
            fee = item[10]
            lat = item[5]
            lng = item[4]
            info = '%s<br>%s<br>停車格數：%s' %(name, fee, total)
            
            folium.Marker([float(lat), float(lng)], tooltip=info,
                        icon=folium.Icon(color='green', prefix='fa', icon='fa-car')).add_to(m)
            
        except Exception as e:
            print(e.args)    
            
    m.save('./map_kh_parking.html')

    return send_file('./map_kh_parking.html')


@app.route("/map/w01-6", methods=['GET'])
def map_w01_6():
    return app.send_static_file('W01-6.html')


#####################
# Scheduler
#####################
def job_wakeup():
    print('cron fun1: awake myself')
    url = 'https://malo-cron2.herokuapp.com/'
    r = requests.get(url)
    print(r)

def send_line(msg, token='rpHUQIIMkArQh6EtQpqfjK6hjPN2jjNxh0zDbcFVoD2'):
    url = "https://notify-api.line.me/api/notify"  # --> 不支援http, 只能用https
    headers = {"Authorization" : "Bearer "+ token}
    title = '排程測試'
    message =  '[%s] %s' %(title, msg)
    payload = {"message" :  message}

    r = requests.post(url ,headers = headers ,params=payload)
    
#- 空污通報
def job_function2():
    url = 'https://data.epa.gov.tw/api/v1/aqx_p_432?format=json&api_key=9be7b239-557b-4c10-9775-78cadfc555e9'
    r = requests.get(url)
    print(r)
    data = r.json()
    records = data['records']
    for item in records:
        if item['County']=='高雄市' and item['SiteName']=='鳳山':
            send_line('%s>> AQI=%s' %(item['SiteName'], item['AQI']))

def start_scheduler():
    scheduler = BackgroundScheduler()

    # run every 10 minute
    #scheduler.add_job(job_wakeup, 'cron', minute='*/10')

    # 每天早上6:30執行
    #scheduler.add_job(job_function2, 'cron', hour='6', minute='30')
    scheduler.add_job(job_function2, 'cron', minute='*/1')

    # start the scheduler
    scheduler.start()

def run_web():
    os.system('gunicorn -w 2 app:app')

if __name__ == "__main__":
    #app.run()
    start_scheduler()
    run_web()
