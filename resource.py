import pymysql
from flask_apispec import doc,use_kwargs,MethodResource
from model import GetPunchRequest,GetCourseRequest,GetCountRequest,GetCurriculumRequest,PostCurriculumRequest,GetLeaveRequest,CrawlerRequest
import sta
from flask import request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import requests,json
import subprocess

def db_init():
    db = pymysql.connect(
        host = 'ec2-34-208-156-155.us-west-2.compute.amazonaws.com',
        user = 'erp',
        password = 'erp',
        port = 3306
    )
    cursor = db.cursor(pymysql.cursors.DictCursor)
    return db, cursor

class Punch(MethodResource):
    @doc(description="出缺勤列表 ( 日期、姓名、簽到、簽退、簽到ip、簽退ip、打卡狀態 )", tags=['Punch'])
    @use_kwargs(GetPunchRequest,location="query")
    def get(self,**kwargs):        
        par={
            'group': kwargs.get('group'),
            'name': kwargs.get('name'),
            'cur' : kwargs.get('cur'),
            'startdate': kwargs.get('startdate'),
            'stopdate': kwargs.get('stopdate'),
            'status': kwargs.get('status'),
            'rows' : kwargs.get('rows',30),
            'page' : kwargs.get('page',1)
        }

        query='WHERE date <= curdate()'
        if par['name'] is not None:
            query += f"AND LOWER(name) = LOWER('{par['name']}')"
        if par['cur'] == 'today':
            query += "AND date = curdate()"
        if par['cur'] == 'month':
            query += "AND date LIKE CONCAT(SUBSTRING(curdate(),1,7),'%')"
        if par['startdate'] is not None:
            query += f"AND date >= '{par['startdate']}'"
        if par['stopdate'] is not None:
            query += f"AND date <= '{par['stopdate']}'"
        if par['status'] == 'late':
            query += 'AND intime >= shouldin'
        if par['status'] == 'excused':
            query += 'AND outtime <= shouldout'
        if par['status'] == 'absent':
            query += 'AND intime IS NULL'
        if par['status'] == 'miss':
            query += 'AND outtime IS NULL AND intime IS NOT NULL'
        if par['status'] == 'regular':
            query += 'AND outtime >= shouldout AND intime <= shouldin'

        sql = f"""
            SELECT SQL_CALC_FOUND_ROWS date,name,intime,outtime,inip,outip,
            CASE WHEN intime IS NULL THEN 'absent' WHEN outtime IS NULL THEN 'miss' WHEN intime >= shouldin THEN 'late' 
            WHEN outtime <= shouldout THEN 'excused' ELSE 'regular' END AS 'status' 
            FROM 
            (SELECT CONCAT(SUBSTRING(date,1,4)+1911, SUBSTRING(date,5)) date,
            str_to_date(CONCAT(min(starthour),':',startminute+1,':00'),'%H:%i:%s') shouldin,
            str_to_date(CONCAT(max(stophour),':',stopminute,':00'),'%H:%i:%s') shouldout 
            FROM curriculum.`{par['group']}` GROUP BY date) AS curr join 
            (SELECT Name name FROM personal_data.`{par['group']}`) AS person left join 
            (SELECT a.date date,a.fullname name,intime,outtime,inip,outip 
            FROM 
            (SELECT SUBSTRING(FROM_UNIXTIME(timestamp),1,10) date,fullname, 
            SUBSTRING(CONVERT_TZ(FROM_UNIXTIME(min(timestamp)),@@session.time_zone,'+8:00'),12) intime,ipaddress inip
            FROM punch.`{par['group']}` where `inout` = 'in' GROUP BY date,fullname) AS a left join 
            (SELECT SUBSTRING(FROM_UNIXTIME(timestamp),1,10) date,fullname, 
            SUBSTRING(CONVERT_TZ(FROM_UNIXTIME(max(timestamp)),@@session.time_zone,'+8:00'),12) outtime,ipaddress outip 
            FROM punch.`{par['group']}` where `inout` = 'out' GROUP BY date,fullname) AS b using (date,fullname)) 
            AS pun using(date,name)
            {query} ORDER BY date DESC LIMIT {(par['page']-1)*par['rows']},{par['rows']};
        """

        paging=f"SELECT FOUND_ROWS() totalrows,CEILING(FOUND_ROWS()/{par['rows']}) totalpages;"

        try:
            db, cursor = db_init()
        except:
            return sta.failure('資料庫連線失敗')

        try:
            cursor.execute(sql)
            punch = cursor.fetchall()
            cursor.execute(paging)
            pagination = cursor.fetchall()
            data={'punch':punch,'pagination':pagination}
            db.commit()
            cursor.close()
            db.close()
            return sta.success(data)
        except:
            cursor.close()
            db.close()
            return sta.failure('參數有誤')


    @doc(description="出缺勤列表 ( 日期、姓名、簽到、簽退、簽到ip、簽退ip、打卡狀態 )", tags=['Punch'])
    @use_kwargs(GetPunchRequest)
    def post(self,**kwargs):        
        return redirect(url_for('punch',**kwargs))



class Count(MethodResource):
    @doc(description="每日遲到、早退、缺席、未打卡、出席次數，應出席、出席、缺席時數，範圍總合及總人數", tags=['Count'])
    @use_kwargs(GetCountRequest,location="query")
    def get(self,**kwargs):
        par={
            'group': kwargs.get('group'),
            'name': kwargs.get('name'),
            'cur' : kwargs.get('cur'),
            'startdate': kwargs.get('startdate'),
            'stopdate': kwargs.get('stopdate')
        }

        query='WHERE date <= curdate()'
        if par['name'] is not None:
            query += f"AND LOWER(name) = LOWER('{par['name']}')"
        if par['cur'] == 'today':
            query += "AND date = curdate()"
        if par['cur'] == 'month':
            query += "AND date LIKE CONCAT(SUBSTRING(curdate(),1,7),'%')"
        if par['startdate'] is not None:
            query += f"AND date >= '{par['startdate']}'"
        if par['stopdate'] is not None:
            query += f"AND date <= '{par['stopdate']}'"

        sql = f"""
            SELECT COALESCE(date,'total') day,COUNT(intime >= shouldin OR NULL) late,COUNT(outtime <= shouldout OR NULL) excused,
            COUNT(intime IS NULL OR NULL) absent,COUNT(outtime IS NULL AND intime IS NOT NULL OR NULL) miss,
            COUNT(outtime >= shouldout AND intime <= shouldin OR NULL) regular,
            SUM(TIMESTAMPDIFF(HOUR,shouldin,shouldout)) totalhours,
            SUM(CASE WHEN intime IS NULL OR intime >= shouldout OR outtime IS NULL OR outtime <= shouldin THEN 0 
            WHEN TIMEDIFF(shouldin,intime) <= 0 
            THEN TIMESTAMPDIFF(HOUR,shouldin,shouldout)-(HOUR(TIMEDIFF(shouldin,intime))+MINUTE(TIMEDIFF(shouldin,intime))/60) 
            WHEN TIMEDIFF(shouldout,outtime) >= 0 
            THEN TIMESTAMPDIFF(HOUR,shouldin,shouldout)-(HOUR(TIMEDIFF(shouldout,outtime))+MINUTE(TIMEDIFF(shouldout,outtime))/60) 
            ELSE TIMESTAMPDIFF(HOUR,shouldin,shouldout) END) AS attendancehours,
            SUM(TIMESTAMPDIFF(HOUR,shouldin,shouldout))-
            SUM(CASE WHEN intime IS NULL OR intime >= shouldout OR outtime IS NULL OR outtime <= shouldin THEN 0 
            WHEN TIMEDIFF(shouldin,intime) <= 0 
            THEN TIMESTAMPDIFF(HOUR,shouldin,shouldout)-(HOUR(TIMEDIFF(shouldin,intime))+MINUTE(TIMEDIFF(shouldin,intime))/60) 
            WHEN TIMEDIFF(shouldout,outtime) >= 0 
            THEN TIMESTAMPDIFF(HOUR,shouldin,shouldout)-(HOUR(TIMEDIFF(shouldout,outtime))+MINUTE(TIMEDIFF(shouldout,outtime))/60) 
            ELSE TIMESTAMPDIFF(HOUR,shouldin,shouldout) END) AS lackhours,COUNT(DISTINCT(name)) 'number of people'
            FROM 
            (SELECT CONCAT(SUBSTRING(date,1,4)+1911, SUBSTRING(date,5)) date,
            str_to_date(CONCAT(min(starthour),':',startminute+1,':00'),'%H:%i:%s') shouldin,
            str_to_date(CONCAT(max(stophour),':',stopminute,':00'),'%H:%i:%s') shouldout 
            FROM curriculum.`{par['group']}` GROUP BY date) AS curr join 
            (SELECT Name name FROM personal_data.`{par['group']}`) AS person left join 
            (SELECT a.date date,a.fullname name,intime,outtime,inip,outip 
            FROM 
            ((SELECT SUBSTRING(FROM_UNIXTIME(timestamp),1,10) date,fullname,
            SUBSTRING(CONVERT_TZ(FROM_UNIXTIME(min(timestamp)),@@session.time_zone,'+8:00'),12) intime,ipaddress inip 
            FROM punch.`{par['group']}` where `inout` = 'in' GROUP BY date,fullname) AS a left join 
            (SELECT SUBSTRING(FROM_UNIXTIME(timestamp),1,10) date,fullname,
            SUBSTRING(CONVERT_TZ(FROM_UNIXTIME(max(timestamp)),@@session.time_zone,'+8:00'),12) outtime,ipaddress outip 
            FROM punch.`{par['group']}` where `inout` = 'out' GROUP BY date,fullname) AS b using (date,fullname))) 
            AS pun using (date,name) {query} GROUP BY date WITH ROLLUP;
        """

        try:
            db, cursor = db_init()
        except:
            return sta.failure('資料庫連線失敗')

        try:
            cursor.execute(sql)
            data = cursor.fetchall()
            db.commit()
            cursor.close()
            db.close()
            return sta.success(data)
        except:
            cursor.close()
            db.close()
            return sta.failure('參數有誤')


    @doc(description="每日遲到、早退、缺席、未打卡、出席次數，應出席、出席、缺席時數，及範圍總合", tags=['Count'])
    @use_kwargs(GetCountRequest)
    def post(self,**kwargs):
        return redirect(url_for('count',**kwargs))


class Curriculum(MethodResource):
    @doc(description = "查詢課表 ( 日期、時段、課程、時數、教室 )", tags = ['Curriculum'])
    @use_kwargs(GetCurriculumRequest,location = "query")
    def get(self,**kwargs):
        par = {
            'group': kwargs.get('group'),
            'month': kwargs.get('month')
        }

        query = ""
        if par['month'] is not None:
            query = f"WHERE date LIKE '{par['month']}%'"
        
        sql = f"""
            SELECT CONCAT(SUBSTRING(date,1,4)+1911, SUBSTRING(date,5)) date,
            CASE WHEN starthour <= 12 THEN 'AM' ELSE 'PM' END AS 'part',course,
            TIMESTAMPDIFF(HOUR,str_to_date(CONCAT(starthour,':',startminute,':00'),'%H:%i:%s'),
            str_to_date(CONCAT(stophour,':',stopminute,':00'),'%H:%i:%s')) hours,
            '123' classroom FROM curriculum.`{par['group']}` {query};
        """

        try:
            db, cursor = db_init()
        except:
            return sta.failure('資料庫連線失敗')

        try:
            cursor.execute(sql)
            data = cursor.fetchall()
            db.commit()
            cursor.close()
            db.close()
            return sta.success(data)
        except:
            cursor.close()
            db.close()
            return sta.failure('參數有誤')
            

    @doc(description = "上傳課表 ( 課程、日期、時起、分起、時訖、分訖 ) 並自動觸發爬蟲", tags = ['Curriculum'])
    @use_kwargs(PostCurriculumRequest,location = "form")
    def post(self,**kwargs):
        group = request.values.get('group')
        file = request.files.get('file')
        if file is None or secure_filename(file.filename) == '':
            return sta.failure('未上傳課表檔案')

        file_ext = os.path.splitext(secure_filename(file.filename))
        if file_ext[1] not in ['.csv'] and file_ext[0] not in ['csv']:
            return sta.failure('請上傳csv檔')

        create = f"""
            CREATE TABLE IF NOT EXISTS curriculum.{group} 
            (course varchar(50),date date,starthour int(10),startminute int(10),stophour int(10),stopminute int(10));
        """
        truncate = f"TRUNCATE TABLE curriculum.{group};"
        val = []
        
        try:
            ts = file.readline().decode('utf-8')
        except:
            return sta.failure('請使用utf-8編碼')

        while ts is not None and ts != '':
            ts = file.readline().decode("utf-8")
            if ts is None or ts == '':
                break
            if len(ts.split(',')) != 6:
                return sta.failure('欄位有誤(6欄)')

            tsn = f"('{ts.split(',')[0]}','{ts.split(',')[1]}',"+",".join(ts.split(',')[2:])+")"
            val.append(tsn)
        file.close()

        val = ",".join(val)
        insert = f"INSERT INTO curriculum.{group} VALUES {val};"
        
        try:
            db, cursor = db_init()
        except:
            return sta.failure('資料庫連線失敗')

        try:
            cursor.execute(create)
            cursor.execute(truncate)
            cursor.execute(insert)
            db.commit()
            cursor.close()
            db.close()
            requests.post("http://54.186.56.114/crawler", json = {"group":f"{group}"})
            return redirect(url_for('curriculum',group = group))
        except:
            cursor.close()
            db.close()
            return sta.failure('課表有誤')


class Leave(MethodResource):
    @doc(description = "查詢請假列表 ( 姓名、日期、時段、假別、原因 )", tags = ['Leave'])
    @use_kwargs(GetLeaveRequest,location = "query")
    def get(self,**kwargs):        
        par = {
            'group': kwargs.get('group'),
            'name': kwargs.get('name'),
            'cur' : kwargs.get('cur'),
            'startdate': kwargs.get('startdate'),
            'stopdate': kwargs.get('stopdate'),
            'leavetype': kwargs.get('leavetype')
        }

        query = ''
        if par['name'] is not None:
            query += f"AND LOWER(name) = LOWER('{par['name']}')"
        if par['cur'] == 'today':
            query += "AND date = curdate()"
        if par['cur'] == 'month':
            query += "AND date LIKE CONCAT(SUBSTRING(curdate(),1,7),'%')"
        if par['startdate'] is not None:
            query += f"AND date >= '{par['startdate']}'"
        if par['stopdate'] is not None:
            query += f"AND date <= '{par['stopdate']}'"
        if par['leavetype'] is not None:
            query += f"AND type LIKE '%{par['leavetype']}%'"

        if query != '':
            query = 'WHERE' + query[3:]
        sql = f"SELECT DATE_FORMAT(date,'%Y-%m-%d') date,name,time,type,reason FROM leavelist.`{par['group']}` {query} ORDER BY date DESC;"
        
        try:
            db, cursor = db_init()
        except:
            return sta.failure('資料庫連線失敗')

        try:
            cursor.execute(sql)
            data = cursor.fetchall()
            db.commit()
            cursor.close()
            db.close()
            return sta.success(data)
        except:
            cursor.close()
            db.close()
            return sta.failure('參數有誤')


    @doc(description = "上傳請假列表 ( 姓名、日期、時段、假別、原因 )", tags = ['Leave'])
    @use_kwargs(PostCurriculumRequest,location = "form")
    def post(self,**kwargs):
        group = request.values.get('group')
        file = request.files.get('file')
        if file is None or secure_filename(file.filename) == '':
            return sta.failure('未上傳請假檔案')

        file_ext = os.path.splitext(secure_filename(file.filename))
        if file_ext[1] not in ['.csv'] and file_ext[0] not in ['csv']:
            return sta.failure('請上傳csv檔')

        create = f"""
            CREATE TABLE IF NOT EXISTS leavelist.{group} 
            (name varchar(20),date date,time varchar(40),type varchar(20),reason varchar(50));
        """
        truncate = f"TRUNCATE TABLE leavelist.{group};"
        val = []
        
        try:
            ts = file.readline().decode('utf-8')
        except:
            return sta.failure('請使用utf-8編碼')

        while ts is not None and ts != '':
            ts = file.readline().decode('utf-8')
            if ts is None or ts == '':
                break
            if len(ts.split(',')) != 5:
                return sta.failure('欄位有誤(5欄)')

            tl = ts.split(',')
            if tl[4] == "\r\n":
                tl[4] = 'no reason'
            for i in range(len(tl)):
                tl[i] = f"'{tl[i]}'"
            tl = f"({','.join(tl)})"

            val.append(tl)
        file.close()

        val = ",".join(val)
        insert = f"INSERT INTO leavelist.{group} VALUES {val};"
        
        try:
            db, cursor = db_init()
        except:
            return sta.failure('資料庫連線失敗')

        try:
            cursor.execute(create)
            cursor.execute(truncate)
            cursor.execute(insert)
            db.commit()
            cursor.close()
            db.close()
            return redirect(url_for('leave',group=group))
        except:
            cursor.close()
            db.close()
            return sta.failure('檔案內容有誤')


class Course(MethodResource):
    @doc(description = "各課程總時數、出席時數、總課程時數、課程總數、已進行課程數、課程學習資源", tags = ['Course'])
    @use_kwargs(GetCourseRequest,location = "query")
    def get(self,**kwargs):
        par = {
            'group': kwargs.get('group'),
            'name': kwargs.get('name'),
            'cur' : kwargs.get('cur'),
            'startdate': kwargs.get('startdate'),
            'stopdate': kwargs.get('stopdate'),
            'status': kwargs.get('status'),
            'course': kwargs.get('course')
        }
        
        videos = f"""
            SELECT url FROM curriculum.`resource` WHERE course = '{par['course']}' AND content = 'video' ORDER BY date DESC LIMIT 3;
        """

        articles = f"""
            SELECT title,url FROM curriculum.`resource` WHERE course = '{par['course']}' AND content = 'article' ORDER BY date DESC LIMIT 3;
        """     
        
        if par['course'] is not None:
            
            try:
                db, cursor = db_init()
            except:
                return sta.failure('資料庫連線失敗')

            try:
                cursor.execute(videos)
                video = cursor.fetchall()
                cursor.execute(articles)
                article = cursor.fetchall()
                data = {'video':video,'article':article}
                db.commit()
                cursor.close()
                db.close()
                return sta.success(data)

            except:
                cursor.close()
                db.close()
                return sta.failure('參數有誤')

        query = ""
        if par['name'] is not None:
            query += f"AND LOWER(Name) = LOWER('{par['name']}')"
        if par['cur'] == 'today':
            query += "AND date = curdate()"
        if par['cur'] == 'month':
            query += "AND date LIKE CONCAT(SUBSTRING(curdate(),1,7),'%')"
        if par['startdate'] is not None:
            query += f"AND date >= '{par['startdate']}'"
        if par['stopdate'] is not None:
            query += f"AND date <= '{par['stopdate']}'"
        if par['status'] == 'progress':
            query += 'AND date <= curdate()'
        if par['status'] == 'unfinished':
            query += 'AND date >= curdate()'
    
        if query != '':
            query = 'WHERE' + query[3:]

        courses = f"""
            SELECT course,SUM(TIMESTAMPDIFF(HOUR,shouldin,shouldout)) totalhours,
            SUM(CASE WHEN intime IS NULL OR intime >= shouldout OR outtime IS NULL OR outtime <= shouldin THEN 0 
            WHEN TIMEDIFF(shouldin,intime) <= 0 
            THEN TIMESTAMPDIFF(HOUR,shouldin,shouldout)-(HOUR(TIMEDIFF(shouldin,intime))+MINUTE(TIMEDIFF(shouldin,intime))/60) 
            WHEN TIMEDIFF(shouldout,outtime) >= 0 
            THEN TIMESTAMPDIFF(HOUR,shouldin,shouldout)-(HOUR(TIMEDIFF(shouldout,outtime))+MINUTE(TIMEDIFF(shouldout,outtime))/60) 
            ELSE TIMESTAMPDIFF(HOUR,shouldin,shouldout) END) AS present
            FROM 
            (SELECT CONCAT(SUBSTRING(date,1,4)+1911, SUBSTRING(date,5)) date,
            CASE WHEN starthour <= 12 THEN 'AM' ELSE 'PM' END AS 'part',course,
            str_to_date(CONCAT(starthour,':',startminute,':00'),'%H:%i:%s') shouldin,
            str_to_date(CONCAT(stophour,':',stopminute,':00'),'%H:%i:%s') shouldout 
            FROM curriculum.`{par['group']}`) AS curr join personal_data.`{par['group']}` AS person
            left join 
            (SELECT a.date date2,a.fullname name2,intime,outtime,inip,outip 
            FROM 
            (SELECT SUBSTRING(FROM_UNIXTIME(timestamp),1,10) date,fullname, 
            SUBSTRING(CONVERT_TZ(FROM_UNIXTIME(min(timestamp)),@@session.time_zone,'+8:00'),12) intime,ipaddress inip
            FROM punch.`{par['group']}` where `inout` = 'in' GROUP BY date,fullname) AS a left join 
            (SELECT SUBSTRING(FROM_UNIXTIME(timestamp),1,10) date,fullname, 
            SUBSTRING(CONVERT_TZ(FROM_UNIXTIME(max(timestamp)),@@session.time_zone,'+8:00'),12) outtime,ipaddress outip 
            FROM punch.`{par['group']}` where `inout` = 'out' GROUP BY date,fullname) AS b using (date,fullname)) 
            AS pun ON date = pun.date2 AND Name = pun.name2 {query} GROUP BY course;
        """

        totals = f"""
            SELECT COUNT(DISTINCT(course)) totalcourse,
            SUM(TIMESTAMPDIFF(HOUR,str_to_date(CONCAT(starthour,':',startminute,':00'),'%H:%i:%s'),
            str_to_date(CONCAT(stophour,':',stopminute,':00'),'%H:%i:%s'))) totalhours,
            COUNT(DISTINCT(CASE WHEN CONCAT(SUBSTRING(date,1,4)+1911, SUBSTRING(date,5)) <= curdate() THEN course END)) AS progress 
            FROM curriculum.`{par['group']}`;
        """

        try:
            db, cursor = db_init()
        except:
            return sta.failure('資料庫連線失敗')

        try:
            cursor.execute(courses)
            course = cursor.fetchall()
            cursor.execute(totals)
            total = cursor.fetchall()
            data={'course':course,'total':total}
            db.commit()
            cursor.close()
            db.close()
            return sta.success(data)
        
        except:
            cursor.close()
            db.close()
            return sta.failure('參數有誤')


    @doc(description = "各課程總時數、出席時數、總課程時數、課程總數、已進行課程數、課程學習資源", tags = ['Course'])
    @use_kwargs(GetCourseRequest)
    def post(self,**kwargs):
        return redirect(url_for('course',**kwargs))
    

class Crawler(MethodResource):
    @doc(description = "查詢學習資源爬蟲狀態", tags = ['Crawler'])
    @use_kwargs(CrawlerRequest,location="query")
    def get(self,**kwargs):
        group= kwargs.get('group')

        sql = f"SELECT status FROM curriculum.`crawlerstatus` WHERE groups='{group}';"

        try:
            db, cursor = db_init()
        except:
            return sta.failure('資料庫連線失敗')

        try:
            cursor.execute(sql)
            data = cursor.fetchone()
            if data == None:
                data = {"status": "inactivated"}
            db.commit()
            cursor.close()
            db.close()
            return data
        except:
            cursor.close()
            db.close()
            return sta.failure('參數有誤')

    @doc(description = "手動執行學習資源爬蟲", tags = ['Crawler'])
    @use_kwargs(CrawlerRequest)
    def post(self,**kwargs):
        group= kwargs.get('group')
        sql = f"INSERT INTO curriculum.crawlerstatus (groups, status) VALUES('{group}', 'in progress') ON DUPLICATE KEY UPDATE status='in progress';"
        try:
            db, cursor = db_init()
        except:
            return sta.failure('資料庫連線失敗')

        try:
            cursor.execute(sql)
            db.commit()
            cursor.close()
            db.close()
            subprocess.Popen(f"python3 crawler.py {group}",shell=True)
            return redirect(url_for('crawler',group=group))
        except:
            cursor.close()
            db.close()
            return sta.failure('參數有誤')
        
        
