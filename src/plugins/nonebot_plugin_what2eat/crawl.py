from dataclasses import dataclass
import json
import ujson as json
import re
from bs4 import BeautifulSoup
import urllib.request

baseurl = "https://home.meishichina.com/show-top-type-recipe-page-"

file = "E:/code/code_study_project/QQRobot/AstolfoCatV2/src/plugins/nonebot_plugin_what2eat/resource/text.json"

ownheaders = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36 Edg/98.0.1108.43"
headers = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36 Edg/98.0.1108.43"
}

def askurl(url):
    request = urllib.request.Request(url=url, headers=headers, method="GET")  # 发送请求
    html = ''
    try:
        response = urllib.request.urlopen(request)  # 取得响应
        html = response.read().decode('utf-8')
    except urllib.error.URLError as e:
        if hasattr(e, 'code'):
            print(e.code)
        if hasattr(e, 'reason'):
            print(e.reason)
    return html

def crawl():
    with open(file, 'r', encoding='utf-8') as f:
        data_json = json.load(f)
        for i in range(1,31):
            url = baseurl + str(i).zfill(2) + ".html"
            html = askurl(url)
            soup = BeautifulSoup(html, 'html.parser')
            for j in range(10):
                foodtitle = soup.select('h2')[j].text.strip()
                data_json["basic_food"].append(foodtitle)

    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data_json, f, ensure_ascii=False, indent=4)
    
    

crawl()
