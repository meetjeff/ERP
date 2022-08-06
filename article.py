from bs4 import BeautifulSoup as bs
import requests
from lxml import html
from googlesearch import search
import pymysql
import pandas as pd
from fake_useragent import UserAgent
import sys
import logging
import os
import re
import time,random
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(filename = os.getenv("arclog"),
                    level = logging.INFO,
                    format = "%(asctime)s %(message)s",
                    datefmt = "%d/%m/%Y %I:%M:%S %p")

savepath = os.getenv("arclog")
if not os.path.exists(savepath):
    logging.warning("Warning! The savepath provided doesn\'t exist!Saving at current directory")
    savepath = os.getcwd() 
    logging.info("savepath reset at %s",str(savepath))
else:
    logging.info("Savepath provided is correct,saving at %s",str(savepath))

group=sys.argv[1]
ua = UserAgent()
user_agent = ua.random
headers = {'User-Agent':user_agent}
db = pymysql.connect(host = os.getenv("dbip"), port = int(os.getenv("dbport")), user = os.getenv("dbuser"), passwd = os.getenv("dbpassword"))
cursor = db.cursor()
sql = f"SELECT DISTINCT course FROM curriculum.{group} WHERE course not REGEXP'專題|輔導|產品|企業|研討會|典禮|結訓';" #篩掉部分關鍵字
cursor.execute(sql)
data = cursor.fetchall()
df = pd.DataFrame(list(data))
list_of_curriculum = df[0].tolist()

for cur in list_of_curriculum:
    query = cur+" 教學" #用課程名稱+教學避免查出官方網站或官方文件
    try:
        for i in search(query, stop = int(os.getenv("search")), pause = 1.0):  #query表示關鍵字，stop表示查詢筆數，pause表示查詢停留時間
            if 'youtube' in i:  #跳過三個常常出現的不相干網站
                pass
            elif 'udemy' in i:
                pass
            elif 'accupass' in i:
                pass
            else:
                try:
                    res1 = requests.get(i, headers = headers) 
                    res1.encoding = res1.apparent_encoding #通過res1.apparent_encoding屬性指定編碼
                    html = res1.text
                    soup = bs(html, 'lxml')
                    time.sleep(random.uniform(1, 2))
                    if 'ithelp' in i:  #因為it邦幫忙的標題格式長得特別不一樣，又常常是搜尋結果，固有另外拉出來做處理
                        search_t = soup.find('h2')
                        search_title = search_t.text
                    else:    
                        search_t = soup.find('title')  #一般文章的標題格式
                        search_title = search_t.text
                    try:  
                        arc1 = f"INSERT INTO curriculum.resource (groups, course, url, content, title) VALUES ('{group}', '{cur}', '{i}', 'article', '{search_title}')"
                        cursor.execute(arc1)
                        db.commit()
                        
                    except Exception as e:
                        logging.info(e)
                        
                except:
                    search_title = "參考資料"  #還有一些標題格式比較不一樣的，就沒有特別處理，標題就直接叫”參考資料“
                    try:
                        arc2 = f"INSERT INTO curriculum.resource (groups, course, url, content, title) VALUES ('{group}', '{cur}', '{i}', 'article', '{search_title}')"
                        cursor.execute(arc2)
                        db.commit()
                        
                    except Exception as e:
                        logging.info(e)
                       
    except Exception as e:
        logging.info(e)
    
    time.sleep(random.uniform(1, 2))
    
fin = f"INSERT INTO curriculum.crawlerstatus (groups,articles) VALUES('{group}','finished') ON DUPLICATE KEY UPDATE videos=videos,articles='finished',date=CURRENT_TIMESTAMP;"
cursor.execute(fin)
db.commit()
cursor.close()   
db.close()
logging.info("%s article finished",str(group))
