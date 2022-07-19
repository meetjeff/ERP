from bs4 import BeautifulSoup as bs
import requests
from lxml import html
from googlesearch import search
import pymysql
import pandas as pd
from requests_html import HTMLSession
from sqlalchemy import create_engine
import sys
from concurrent.futures import ProcessPoolExecutor
import logging
import os

logging.basicConfig(filename = "craw.log",
                    level = logging.DEBUG,
                    format = "%(asctime)s %(message)s",
                    datefmt = "%d/%m/%Y %I:%M:%S %p")

savepath = "~/"
if not os.path.exists(savepath):
    logging.warning("Warning! The savepath provided doesn\'t exist!Saving at current directory")
    savepath = os.getcwd() 
    logging.info("savepath reset at %s",str(savepath))
else:
    logging.info("Savepath provided is correct,saving at %s",str(savepath))

group=sys.argv[1]
def yt(group):
    # 資料庫資訊
    acc = 'erp'
    pwd = 'erp'
    ip = 'ec2-34-208-156-155.us-west-2.compute.amazonaws.com'
    db = 'curriculum'
    engine = create_engine(f'mysql+pymysql://{acc}:{pwd}@{ip}/{db}')

    # 取得課程名稱
    result = engine.execute(f"SELECT DISTINCT course FROM curriculum.{group} WHERE course not REGEXP'專題|輔導|產品|企業|研討會|典禮';")
    data = result.fetchall()
    df = pd.DataFrame(list(data))
    curriculum = df[0].tolist()


    #爬取各個課程的url
    for query in curriculum:
        session = HTMLSession()
        url = f"https://www.youtube.com/results?search_query={query}"
        response = session.get(url)
        response.html.render(sleep=1, keep_page = True, scrolldown = 1,timeout=40)

        for i ,links in enumerate(response.html.find('a#video-title')):
            try:
                link = next(iter(links.absolute_links))

                #匯入資料
                sql = f"INSERT INTO curriculum.resource (groups, course, url, content, title) VALUES ('{group}', '{query}', '{link}', 'video', '{query}')"
                engine.execute(sql)
                if i == 0:
                    break
            except Exception as e:
                logging.info(e)
                #印出異常的狀態是甚麼,因此except後面的可以不加(https://steam.oxxostudio.tw/category/python/basic/try-except.html)
                
    engine.dispose()
    logging.info("video finished")

def arc(group):
    #連接資料庫
    db = pymysql.connect(host = 'ec2-34-208-156-155.us-west-2.compute.amazonaws.com', port = 3306, user = 'erp', passwd = 'erp')
    cursor = db.cursor()

    #讀取資料庫中fn101的課表
    sql = f"SELECT DISTINCT course FROM curriculum.{group} WHERE course not REGEXP'專題|輔導|產品|企業|研討會|典禮';" #篩掉部分關鍵字
    cursor.execute(sql)
    data = cursor.fetchall()

    #用轉成dataframe的方式再把tuple轉list
    df = pd.DataFrame(list(data))
    list_of_curriculum = df[0].tolist()

    #用search這個套件可以抓出搜尋結果
    headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15'}
    for cur in list_of_curriculum:
        query = cur+" 教學" #用課程名稱+教學避免查出官方網站或官方文件
        for i in search(query, stop = 1, pause = 1.0):   #query表示關鍵字，stop表示查詢筆數，pause表示查詢停留時間
            if 'youtube' in i:  #跳過三個常常出現的不相干網站
                pass
            elif 'udemy' in i:
                pass
            elif 'accupass' in i:
                pass
            else:
                try:
                    res = requests.get(i, headers = headers) 
                    res.encoding = res.apparent_encoding #通過res.apparent_encoding屬性指定編碼
                    html = res.text
                    soup = bs(html, 'lxml')
                    if 'ithelp' in i:  #因為it邦幫忙的標題格式長得特別不一樣，又常常是搜尋結果，固有另外拉出來做處理
                        search_t = soup.find('h2')
                        search_title = search_t.text
                    else:    
                        search_t = soup.find('title')  #一般文章的標題格式
                        search_title = search_t.text
                    try:  
                        sql = f"INSERT INTO curriculum.resource (groups, course, url, content, title) VALUES ('{group}', '{cur}', '{i}', 'article', '{search_title}')"
                        cursor.execute(sql)
                        db.commit()
                    except Exception as e:
                        logging.info(e)
                except:
                    search_title = "參考資料"  #還有一些標題格式比較不一樣的，就沒有特別處理，標題就直接叫”參考資料“
                    try:
                        sql = f"INSERT INTO curriculum.resource (groups, course, url, content, title) VALUES ('{group}', '{cur}', '{i}', 'article', '{search_title}')"
                        cursor.execute(sql)
                        db.commit()
                    except Exception as e:
                        logging.info(e)
                    
    db.commit()   
    db.close()
    logging.info("article finished")
    

if __name__ == '__main__':

    with ProcessPoolExecutor(max_workers=4) as executor:
        executor.submit(yt, group)
        executor.submit(arc, group)

    db = pymysql.connect(
        host = 'ec2-34-208-156-155.us-west-2.compute.amazonaws.com',
        user = 'erp',
        password = 'erp',
        port = 3306
    )
    cursor = db.cursor(pymysql.cursors.DictCursor)

    sql = f"INSERT INTO curriculum.crawlerstatus (groups, status) VALUES('{group}', 'finished') ON DUPLICATE KEY UPDATE status='finished';"
    cursor.execute(sql)
    
    db.commit()
    cursor.close()
    db.close()
    logging.info("%s finished",str(group))
