import requests
from lxml import html
from googlesearch import search
import pymysql
import pandas as pd
import sys
import logging
import os
import re

group=sys.argv[1]
headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15'}
db1 = pymysql.connect(host = 'ec2-34-208-156-155.us-west-2.compute.amazonaws.com', port = 3306, user = 'erp', passwd = 'erp')
cursor1 = db1.cursor()
sql1 = f"SELECT DISTINCT course FROM curriculum.{group} WHERE course not REGEXP'專題|輔導|產品|企業|研討會|典禮';" #篩掉部分關鍵字
cursor1.execute(sql1)
data1 = cursor1.fetchall()
df1 = pd.DataFrame(list(data1))
list_of_curriculum1 = df1[0].tolist()

for cur1 in list_of_curriculum1:                    
    queryv = cur1 + "youtube"
    try:
        for i2 in search(queryv, stop = 1, pause = 1.0):
            print(i2)
            if 'https://www.youtube.com/watch?v=' in i2:  
                try:
                    res2 = requests.get(i2, headers = headers)
                    res2.encoding = res2.apparent_encoding #通過res.apparent_encoding屬性指定編碼
                    url = re.sub("watch\?v=","embed/", i2)
                    yt = f"INSERT INTO curriculum.resource (groups, course, url, content, title) VALUES ('{group}', '{cur1}', '{url}', 'video', '{cur1}')"
                    # lock.acquire()
                    cursor1.execute(yt)
                    db1.commit()
                    # lock.release()
                except Exception as e:
                    # logging.info(e) 
                    print(e)
    except Exception as e:
        print(e)

fin = f"INSERT INTO curriculum.crawlerstatus (groups, status) VALUES('{group}', 'finished') ON DUPLICATE KEY UPDATE status='finished';"
cursor1.execute(fin)
db1.commit()
cursor1.close()   
db1.close()
# logging.info("%s finished",str(group))
print("ytfinish")
