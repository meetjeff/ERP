from flask_apispec import doc,use_kwargs,MethodResource
from model import GetPunchRequest,GetCourseRequest,GetCountRequest,GetCurriculumRequest,GetLeaveRequest
from model import Getinfo,PostFileRequest,CrawlerRequest,LoginRequest
import sta
from flask import request,redirect,url_for
from werkzeug.utils import secure_filename
import os
import requests
import subprocess
from flask_jwt_extended import create_access_token,jwt_required,get_jwt_identity
import dbcon

class Login(MethodResource):
    @jwt_required()
    @doc(description = "自動帶入基本資料", tags = ['Getinfo'], params = {
        'Authorization': {
            'description':'Authorization HTTP header with JWT access token, like: Bearer (token)',
            'in':'header',
            'type':'string',
            'required':True
        }
    })
    @use_kwargs(Getinfo, location = "query")
    def get(self,**kwargs):
        identity = get_jwt_identity()
        if str(identity[0]['Access']) == '1':
            group = identity[0]['Class']
            name = identity[0]['Name']
        if str(identity[0]['Access']) in ['2','3']:
            group = kwargs.get("group")
            name = kwargs.get("name")
        if str(identity[0]['Access']) not in ['1','2','3']:
            return sta.failure('權限不足')
        
        sql = f"SELECT Class,Name,Id,Email FROM `personal_data`.{group} WHERE LOWER(Name) = LOWER('{name}');"
        
        try:
            db, cursor = dbcon.db_init()
        except:
            return sta.failure('資料庫連線失敗')

        try:
            cursor.execute(sql)
            user = cursor.fetchall()
            cursor.close()
            db.close()
            if user != ():
                return sta.success(user)
        except:
            cursor.close()
            db.close()
            return sta.failure('參數有誤')
        return sta.failure("Account does not exist")


    @doc(description = "登入 ( 群組、帳號、密碼 )", tags = ['Login'])
    @use_kwargs(LoginRequest)
    def post(self,**kwargs):
        group = kwargs.get("group")
        account = kwargs.get("account")
        password = kwargs.get("password")
        sql = f"SELECT Access,Class,Name FROM personal_data.{group} WHERE LOWER(Name) = LOWER('{account}') AND Password = '{password}';"
        
        try:
            db, cursor = dbcon.db_init()
        except:
            return sta.failure('資料庫連線失敗')

        try:
            cursor.execute(sql)
            user = cursor.fetchall()
            cursor.close()
            db.close()

            if user != ():
                access_token = create_access_token(identity=user)
                data = {
                    "message": f"Welcome {user[0]['Name']}",
                    "access_token": access_token}
                return sta.success(data)
        except:
            cursor.close()
            db.close()
            return sta.failure('參數有誤')
            
        return sta.failure("Account or password is wrong")


class Punch(MethodResource):
    @jwt_required()
    @doc(description = "出缺勤列表 ( 日期、姓名、簽到、簽退、簽到ip、簽退ip、打卡狀態 )", tags = ['Punch'], params = {
        'Authorization': {
            'description':'Authorization HTTP header with JWT access token, like: Bearer (token)',
            'in':'header',
            'type':'string',
            'required':True
        }
    })
    @use_kwargs(GetPunchRequest,location = "query")
    def get(self,**kwargs):
        identity = get_jwt_identity()
        if str(identity[0]['Access']) == '1':
            group = identity[0]['Class']
            name = identity[0]['Name']
        if str(identity[0]['Access']) in ['2','3']:
            group = kwargs.get("group")
            name = kwargs.get("name")
        if str(identity[0]['Access']) not in ['1','2','3']:
            return sta.failure('權限不足')

        par = {
            'group': group,
            'name': name,
            'cur' : kwargs.get('cur'),
            'startdate': kwargs.get('startdate'),
            'stopdate': kwargs.get('stopdate'),
            'status': kwargs.get('status'),
            'rows' : kwargs.get('rows',30),
            'page' : kwargs.get('page',1)
        }

        query = 'WHERE date <= curdate()'
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
            min(str_to_date(CONCAT(starthour,':',startminute+1,':00'),'%H:%i:%s')) shouldin,
            max(str_to_date(CONCAT(stophour,':',stopminute,':00'),'%H:%i:%s')) shouldout 
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

        paging = f"SELECT FOUND_ROWS() totalrows,CEILING(FOUND_ROWS()/{par['rows']}) totalpages;"

        try:
            db, cursor = dbcon.db_init()
        except:
            return sta.failure('資料庫連線失敗')

        try:
            cursor.execute(sql)
            punch = cursor.fetchall()
            cursor.execute(paging)
            pagination = cursor.fetchall()
            data = {'punch':punch,'pagination':pagination}
            db.commit()
            cursor.close()
            db.close()
            return sta.success(data)
        except:
            cursor.close()
            db.close()
            return sta.failure('參數有誤')


    @jwt_required()
    @doc(description = "出缺勤列表 ( 日期、姓名、簽到、簽退、簽到ip、簽退ip、打卡狀態 )", tags = ['Punch'], params = {
        'Authorization': {
            'description':'Authorization HTTP header with JWT access token, like: Bearer (token)',
            'in':'header',
            'type':'string',
            'required':True
        }
    })
    @use_kwargs(GetPunchRequest)
    def post(self,**kwargs):        
        return redirect(url_for('punch',**kwargs))


class Count(MethodResource):
    @jwt_required()
    @doc(description = "每日遲到、早退、缺席、未打卡、請假、出席數，應出席、出席、缺席、請假時數，範圍總合及總人數", tags = ['Count'], params = {
        'Authorization': {
            'description':'Authorization HTTP header with JWT access token, like: Bearer (token)',
            'in':'header',
            'type':'string',
            'required':True
        }
    })
    @use_kwargs(GetCountRequest,location = "query")
    def get(self,**kwargs):
        identity = get_jwt_identity()
        if str(identity[0]['Access']) == '1':
            group = identity[0]['Class']
            name = identity[0]['Name']
        if str(identity[0]['Access']) in ['2','3']:
            group = kwargs.get("group")
            name = kwargs.get("name")
        if str(identity[0]['Access']) not in ['1','2','3']:
            return sta.failure('權限不足')

        par = {
            'group': group,
            'name': name,
            'cur' : kwargs.get('cur'),
            'startdate': kwargs.get('startdate'),
            'stopdate': kwargs.get('stopdate')
        }

        query = 'WHERE date <= curdate()'
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
            COUNT(outtime >= shouldout AND intime <= shouldin OR NULL) regular,COUNT(time IS NOT NULL OR NULL) 'leave',
            SUM((TIMESTAMPDIFF(MINUTE,shouldin,shouldout)+1)/60) totalhours,
            SUM(CASE WHEN intime IS NULL OR intime >= shouldout OR outtime IS NULL OR outtime <= shouldin THEN 0 
            WHEN TIMEDIFF(shouldin,intime) <= 0 
            THEN (TIMESTAMPDIFF(MINUTE,shouldin,shouldout)+1)/60-HOUR(TIMEDIFF(shouldin,intime))-MINUTE(TIMEDIFF(shouldin,intime))/60 
            WHEN TIMEDIFF(shouldout,outtime) >= 0 
            THEN (TIMESTAMPDIFF(MINUTE,shouldin,shouldout)+1)/60-HOUR(TIMEDIFF(shouldout,outtime))-MINUTE(TIMEDIFF(shouldout,outtime))/60 
            ELSE (TIMESTAMPDIFF(MINUTE,shouldin,shouldout)+1)/60 END) AS attendancehours,
            SUM((TIMESTAMPDIFF(MINUTE,shouldin,shouldout)+1)/60-
            CASE WHEN intime IS NULL OR intime >= shouldout OR outtime IS NULL OR outtime <= shouldin THEN 0 
            WHEN TIMEDIFF(shouldin,intime) <= 0 
            THEN (TIMESTAMPDIFF(MINUTE,shouldin,shouldout)+1)/60-HOUR(TIMEDIFF(shouldin,intime))-MINUTE(TIMEDIFF(shouldin,intime))/60 
            WHEN TIMEDIFF(shouldout,outtime) >= 0 
            THEN (TIMESTAMPDIFF(MINUTE,shouldin,shouldout)+1)/60-HOUR(TIMEDIFF(shouldout,outtime))-MINUTE(TIMEDIFF(shouldout,outtime))/60 
            ELSE (TIMESTAMPDIFF(MINUTE,shouldin,shouldout)+1)/60 END) AS lackhours,
            SUM(CASE WHEN INSTR(time,'整天') THEN (TIMESTAMPDIFF(MINUTE,shouldin,shouldout)+1)/60 WHEN INSTR(time,'~') THEN  
            TIMESTAMPDIFF(MINUTE,STR_TO_DATE(SUBSTRING_INDEX(REPLACE(REPLACE(REPLACE(time,'上午',''),'下午',''),' ',''),'~',1),'%H:%i'),
            STR_TO_DATE(REPLACE(SUBSTRING_INDEX(REPLACE(REPLACE(REPLACE(time,'上午',''),'下午',''),' ',''),'~',-1),'課程結束',shouldout),'%H:%i')
            )/60 ELSE 0 END) AS leavehours,COUNT(DISTINCT(name)) 'number of people'
            FROM 
            (SELECT CONCAT(SUBSTRING(date,1,4)+1911, SUBSTRING(date,5)) date,
            min(str_to_date(CONCAT(starthour,':',startminute+1,':00'),'%H:%i:%s')) shouldin,
            max(str_to_date(CONCAT(stophour,':',stopminute,':00'),'%H:%i:%s')) shouldout 
            FROM curriculum.`{par['group']}` GROUP BY date) AS curr join 
            (SELECT Name name FROM personal_data.`{par['group']}`) AS person left join 
            (SELECT date,name,time FROM leavelist.`{par['group']}`) AS leavetime using(date,name) left join 
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
            db, cursor = dbcon.db_init()
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


    @jwt_required()
    @doc(description = "每日遲到、早退、缺席、未打卡、請假、出席數，應出席、出席、缺席、請假時數，範圍總合及總人數", tags = ['Count'], params = {
        'Authorization': {
            'description':'Authorization HTTP header with JWT access token, like: Bearer (token)',
            'in':'header',
            'type':'string',
            'required':True
        }
    })
    @use_kwargs(GetCountRequest)
    def post(self,**kwargs):
        return redirect(url_for('count',**kwargs))


class Curriculum(MethodResource):
    @jwt_required()
    @doc(description = "查詢課表 ( 日期、時段、課程、時數、教室 )", tags = ['Curriculum'], params = {
        'Authorization': {
            'description':'Authorization HTTP header with JWT access token, like: Bearer (token)',
            'in':'header',
            'type':'string',
            'required':True
        }
    })
    @use_kwargs(GetCurriculumRequest,location = "query")
    def get(self,**kwargs):
        identity = get_jwt_identity()
        if str(identity[0]['Access']) == '1':
            group = identity[0]['Class']
        if str(identity[0]['Access']) in ['2','3']:
            group = kwargs.get("group")
        if str(identity[0]['Access']) not in ['1','2','3']:
            return sta.failure('權限不足')

        par = {
            'group': group,
            'month': kwargs.get('month'),
            'crawler': request.values.get('crawler')
        }

        query = ""
        if par['month'] is not None:
            query = f"WHERE CONCAT(SUBSTRING(date,1,4)+1911, SUBSTRING(date,5)) LIKE '{par['month']}%'"
        
        sql = f"""
            SELECT CONCAT(SUBSTRING(date,1,4)+1911, SUBSTRING(date,5)) date,
            CASE WHEN starthour <= 12 THEN 'AM' ELSE 'PM' END AS 'part',course,
            TIMESTAMPDIFF(MINUTE,str_to_date(CONCAT(starthour,':',startminute,':00'),'%H:%i:%s'),
            str_to_date(CONCAT(stophour,':',stopminute,':00'),'%H:%i:%s'))/60 hours,
            '123' classroom FROM curriculum.`{par['group']}` {query};
        """

        try:
            db, cursor = dbcon.db_init()
        except:
            return sta.failure('資料庫連線失敗')

        try:
            cursor.execute(sql)
            data = cursor.fetchall()
            db.commit()
            cursor.close()
            db.close()
            if par['crawler'] is not None:
                data = {'curriculum': data,'crawlerstatus': par['crawler']}
            return sta.success(data)
        except:
            cursor.close()
            db.close()
            return sta.failure('參數有誤')
            

    @jwt_required()
    @doc(description = "上傳課表 ( 課程、日期、時起、分起、時訖、分訖 ) 並自動觸發爬蟲", tags = ['Curriculum'], params = {
        'Authorization': {
            'description':'Authorization HTTP header with JWT access token, like: Bearer (token)',
            'in':'header',
            'type':'string',
            'required':True
        }
    })
    @use_kwargs(PostFileRequest,location = "form")
    def post(self,**kwargs):
        identity = get_jwt_identity()
        if identity[0]['Access'] != '2':
            return sta.failure('權限不足')
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
            db, cursor = dbcon.db_init()
        except:
            return sta.failure('資料庫連線失敗')

        try:
            cursor.execute(create)
            cursor.execute(truncate)
            cursor.execute(insert)
            db.commit()
            cursor.close()
            db.close()
            cra = requests.post("http://54.186.56.114/crawler", json = {"group":f"{group}"})
            try:
                crawler = cra.json()
            except:
                crawler = cra.text
            return redirect(url_for('curriculum',group = group,crawler = crawler))
        except:
            cursor.close()
            db.close()
            return sta.failure('課表有誤')


class Leave(MethodResource):
    @jwt_required()
    @doc(description = "查詢請假列表 ( 姓名、日期、時段、假別、原因 )", tags = ['Leave'], params = {
        'Authorization': {
            'description':'Authorization HTTP header with JWT access token, like: Bearer (token)',
            'in':'header',
            'type':'string',
            'required':True
        }
    })
    @use_kwargs(GetLeaveRequest,location = "query")
    def get(self,**kwargs):     
        identity = get_jwt_identity()
        if str(identity[0]['Access']) == '1':
            group = identity[0]['Class']
            name = identity[0]['Name']
        if str(identity[0]['Access']) in ['2','3']:
            group = kwargs.get("group")
            name = kwargs.get("name")
        if str(identity[0]['Access']) not in ['1','2','3']:
            return sta.failure('權限不足')

        par = {
            'group': group,
            'name': name,
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
            db, cursor = dbcon.db_init()
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


    @jwt_required()
    @doc(description = "上傳請假列表 ( 姓名、日期、時段、假別、原因 )", tags = ['Leave'], params = {
        'Authorization': {
            'description':'Authorization HTTP header with JWT access token, like: Bearer (token)',
            'in':'header',
            'type':'string',
            'required':True
        }
    })
    @use_kwargs(PostFileRequest,location = "form")
    def post(self,**kwargs):
        identity = get_jwt_identity()
        if identity[0]['Access'] != '2':
            return sta.failure('權限不足')
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
            db, cursor = dbcon.db_init()
        except:
            return sta.failure('資料庫連線失敗')

        try:
            cursor.execute(create)
            cursor.execute(truncate)
            cursor.execute(insert)
            db.commit()
            cursor.close()
            db.close()
            return redirect(url_for('leave',group = group))
        except:
            cursor.close()
            db.close()
            return sta.failure('檔案內容有誤')


class Course(MethodResource):
    @jwt_required()
    @doc(description = "各課程總時數、出席時數、總課程時數、課程總數、已進行課程數、課程學習資源", tags = ['Course'], params = {
        'Authorization': {
            'description':'Authorization HTTP header with JWT access token, like: Bearer (token)',
            'in':'header',
            'type':'string',
            'required':True
        }
    })
    @use_kwargs(GetCourseRequest,location = "query")
    def get(self,**kwargs):
        identity = get_jwt_identity()
        if str(identity[0]['Access']) == '1':
            group = identity[0]['Class']
            name = identity[0]['Name']
        if str(identity[0]['Access']) in ['2','3']:
            group = kwargs.get("group")
            name = kwargs.get("name")
        if str(identity[0]['Access']) not in ['1','2','3']:
            return sta.failure('權限不足')

        par = {
            'group': group,
            'name': name,
            'cur' : kwargs.get('cur'),
            'startdate': kwargs.get('startdate'),
            'stopdate': kwargs.get('stopdate'),
            'status': kwargs.get('status'),
            'course': kwargs.get('course')
        }
        
        videos = f"""
            SELECT DISTINCT url FROM curriculum.`resource` WHERE course = '{par['course']}' AND content = 'video' ORDER BY date DESC LIMIT 3;
        """

        articles = f"""
            SELECT DISTINCT title,url FROM curriculum.`resource` WHERE course = '{par['course']}' AND content = 'article' ORDER BY date DESC LIMIT 3;
        """     
        
        if par['course'] is not None:
            
            try:
                db, cursor = dbcon.db_init()
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
            SELECT course,SUM(TIMESTAMPDIFF(MINUTE,shouldin,shouldout)/60) totalhours,
            SUM(CASE WHEN intime IS NULL OR intime >= shouldout OR outtime IS NULL OR outtime <= shouldin THEN 0 
            WHEN TIMEDIFF(shouldin,intime) <= 0 
            THEN TIMESTAMPDIFF(MINUTE,shouldin,shouldout)/60-HOUR(TIMEDIFF(shouldin,intime))-MINUTE(TIMEDIFF(shouldin,intime))/60 
            WHEN TIMEDIFF(shouldout,outtime) >= 0 
            THEN TIMESTAMPDIFF(MINUTE,shouldin,shouldout)/60-HOUR(TIMEDIFF(shouldout,outtime))-MINUTE(TIMEDIFF(shouldout,outtime))/60 
            ELSE TIMESTAMPDIFF(MINUTE,shouldin,shouldout)/60 END) AS present
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
            SUM(TIMESTAMPDIFF(MINUTE,str_to_date(CONCAT(starthour,':',startminute,':00'),'%H:%i:%s'),
            str_to_date(CONCAT(stophour,':',stopminute,':00'),'%H:%i:%s'))/60) totalhours,
            COUNT(DISTINCT(CASE WHEN CONCAT(SUBSTRING(date,1,4)+1911, SUBSTRING(date,5)) <= curdate() THEN course END)) AS progress 
            FROM curriculum.`{par['group']}`;
        """

        try:
            db, cursor = dbcon.db_init()
        except:
            return sta.failure('資料庫連線失敗')

        try:
            cursor.execute(courses)
            course = cursor.fetchall()
            cursor.execute(totals)
            total = cursor.fetchall()
            data = {'course':course,'total':total}
            db.commit()
            cursor.close()
            db.close()
            return sta.success(data)
        
        except:
            cursor.close()
            db.close()
            return sta.failure('參數有誤')


    @jwt_required()
    @doc(description = "各課程總時數、出席時數、總課程時數、課程總數、已進行課程數、課程學習資源", tags = ['Course'], params = {
        'Authorization': {
            'description':'Authorization HTTP header with JWT access token, like: Bearer (token)',
            'in':'header',
            'type':'string',
            'required':True
        }
    })
    @use_kwargs(GetCourseRequest)
    def post(self,**kwargs):
        return redirect(url_for('course',**kwargs))
    

class Crawler(MethodResource):
    @jwt_required()
    @doc(description = "查詢學習資源爬蟲狀態", tags = ['Crawler'], params = {
        'Authorization': {
            'description':'Authorization HTTP header with JWT access token, like: Bearer (token)',
            'in':'header',
            'type':'string',
            'required':True
        }
    })
    @use_kwargs(CrawlerRequest,location="query")
    def get(self,**kwargs):
        identity = get_jwt_identity()
        if identity[0]['Access'] != '2':
            return sta.failure('權限不足')
        group = kwargs.get('group')

        sql = f"SELECT * FROM curriculum.`crawlerstatus` WHERE groups = '{group}';"

        try:
            db, cursor = dbcon.db_init()
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

    
    @jwt_required()
    @doc(description = "手動執行學習資源爬蟲", tags = ['Crawler'], params = {
        'Authorization': {
            'description':'Authorization HTTP header with JWT access token, like: Bearer (token)',
            'in':'header',
            'type':'string',
            'required':True
        }
    })
    @use_kwargs(CrawlerRequest)
    def post(self,**kwargs):
        identity = get_jwt_identity()
        if identity[0]['Access'] != '2':
            return sta.failure('權限不足')
        group = kwargs.get('group')
        sql = f"""
            INSERT INTO curriculum.crawlerstatus (groups,videos,articles) VALUES('{group}','in progress','in progress') 
            ON DUPLICATE KEY UPDATE videos = 'in progress',articles = 'in progress',date = CURRENT_TIMESTAMP;
        """
        try:
            db, cursor = dbcon.db_init()
        except:
            return sta.failure('資料庫連線失敗')

        try:
            subprocess.Popen(f"python3 video.py {group}",shell = True)
            subprocess.Popen(f"python3 article.py {group}",shell = True)
            cursor.execute(sql)
            db.commit()
            cursor.close()
            db.close()
            return redirect(url_for('crawler',group = group))
        except:
            cursor.close()
            db.close()
            return sta.failure('參數有誤')
        
        
