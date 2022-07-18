from requests_html import HTMLSession
import pymysql
from sqlalchemy import create_engine
import pandas as pd



# 資料庫資訊
group = 'fn101'
acc = 'erp'
pwd = 'erp'
ip = 'ec2-34-208-156-155.us-west-2.compute.amazonaws.com'
db = 'curriculum'
table = 'resource'
engine = create_engine(f'mysql+pymysql://{acc}:{pwd}@{ip}/{db}')

# 取得課程名稱
result = engine.execute(f"SELECT DISTINCT course FROM curriculum.{group} WHERE course not REGEXP' 專題|輔導|產品|企業|研討會|典禮';")
data = result.fetchall()
# print(data)
df = pd.DataFrame(list(data))
curriculum = df['course'].tolist()
# print(curriculum)


#爬取各個課程的url
for query in curriculum:
    session = HTMLSession()
    url = f"https://www.youtube.com/results?search_query={query}]"
    response = session.get(url)
    response.html.render(sleep=1, keep_page = True, scrolldown = 1)

    for links in response.html.find('a#video-title'):
        try:
            link = next(iter(links.absolute_links))
            #匯入資料
            sql = f"INSERT INTO curriculum.resource (groups, course, url, content, title) VALUES ('{group}', '{query}', '{link}', 'video', '{query}')"
            engine.execute(sql)
        except Exception as e:
            print(e) #印出異常的狀態是甚麼,因此except後面的可以不加(https://steam.oxxostudio.tw/category/python/basic/try-except.html)
            engine.dispose()

engine.dispose()
