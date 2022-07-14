import pymysql
from flask_apispec import doc,use_kwargs,MethodResource
from model import GetPunchRequest,GetCourseRequest,GetCountRequest,GetCurriculumRequest,PostCurriculumRequest,GetLeaveRequest
import sta
from flask import request, redirect, url_for
from werkzeug.utils import secure_filename
import os

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
    @doc(description = "出缺勤列表 ( 日期、姓名、簽到、簽退、簽到ip、簽退ip、打卡狀態 )", tags = ['Punch'])
    @use_kwargs(GetPunchRequest,location = "query")
    def get(self,**kwargs):        
        par = {
            'group': kwargs.get('group'),
            'name': kwargs.get('name'),
            'cur' : kwargs.get('cur'),
            'startdate': kwargs.get('startdate'),
            'stopdate': kwargs.get('stopdate'),
            'status': kwargs.get('status'),
            'rows' : kwargs.get('rows',30),
            'page' : kwargs.get('page',1)
        }

        query = 'WHERE date1 <= curdate()'
        if par['name'] is not None:
            query += f"AND LOWER(name1) = LOWER('{par['name']}')"
        if par['cur'] == 'today':
            query += "AND date1 = curdate()"
        if par['cur'] == 'month':
            query += "AND date1 LIKE CONCAT(SUBSTRING(curdate(),1,7),'%')"
        if par['startdate'] is not None:
            query += f"AND date1 >= '{par['startdate']}'"
        if par['stopdate'] is not None:
            query += f"AND date1 <= '{par['stopdate']}'"
        if par['status'] == 'late':
            query += 'AND intime >= shouldin'
        if par['status'] == 'excused':
            query += 'AND outtime <= shouldout'
        if par['status'] == 'absent':
            query += 'AND intime IS NULL'
        if par['status'] == 'miss':
            query += 'AND outtime IS NULL AND intime IS NOT NULL'

        sql = f"""
            SELECT SQL_CALC_FOUND_ROWS date1 classdate,name1 student,intime,outtime,inip,outip,
            CASE WHEN intime IS NULL THEN 'absent' WHEN outtime IS NULL THEN 'miss' WHEN intime >= shouldin THEN 'late' 
            WHEN outtime <= shouldout THEN 'excused' ELSE 'present' END AS 'status' 
            FROM
            (SELECT curr.date date1,person.Name name1,curr.shouldin,curr.shouldout 
            FROM 
            (SELECT CONCAT(SUBSTRING(date,1,4)+1911, SUBSTRING(date,5)) date,
            str_to_date(CONCAT(min(starthour),':',startminute+1,':00'),'%H:%i:%s') shouldin,
            str_to_date(CONCAT(max(stophour),':',stopminute,':00'),'%H:%i:%s') shouldout 
            FROM curriculum.`{par['group']}` GROUP BY date) AS curr join personal_data.`{par['group']}` AS person) 
            AS currn left join 
            (SELECT a.date date2,a.fullname name2,intime,outtime,inip,outip 
            FROM 
            (SELECT SUBSTRING(FROM_UNIXTIME(timestamp),1,10) date,fullname, 
            SUBSTRING(CONVERT_TZ(FROM_UNIXTIME(min(timestamp)),@@session.time_zone,'+8:00'),12) intime,ipaddress inip
            FROM punch.`info` where `inout` = 'in' GROUP BY date,fullname) AS a left join 
            (SELECT SUBSTRING(FROM_UNIXTIME(timestamp),1,10) date,fullname, 
            SUBSTRING(CONVERT_TZ(FROM_UNIXTIME(max(timestamp)),@@session.time_zone,'+8:00'),12) outtime,ipaddress outip 
            FROM punch.`info` where `inout` = 'out' GROUP BY date,fullname) AS b using (date,fullname)) 
            AS pun ON currn.date1 = pun.date2 AND currn.name1 = pun.name2
            {query}
            ORDER BY date1 DESC LIMIT {(par['page']-1)*par['rows']},{par['rows']};
        """

        paging = f"SELECT FOUND_ROWS() totalrows,CEILING(FOUND_ROWS()/{par['rows']}) totalpages;"

        try:
            db, cursor = db_init()
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


    @doc(description = "出缺勤列表 ( 日期、姓名、簽到、簽退、簽到ip、簽退ip、打卡狀態 )", tags = ['Punch'])
    @use_kwargs(GetPunchRequest)
    def post(self,**kwargs):        
        return redirect(url_for('punch',**kwargs))


class Count(MethodResource):
    @doc(description = "統計次數 : 遲到、早退、缺席、未打卡、出席", tags = ['Count'])
    @use_kwargs(GetCountRequest,location = "query")
    def get(self,**kwargs):
        par = {
            'group': kwargs.get('group'),
            'name': kwargs.get('name'),
            'cur' : kwargs.get('cur'),
            'startdate': kwargs.get('startdate'),
            'stopdate': kwargs.get('stopdate')
        }

        query = 'WHERE date1 <= curdate()'
        if par['name'] is not None:
            query += f"AND LOWER(name1) = LOWER('{par['name']}')"
        if par['cur'] == 'today':
            query += "AND date1 = curdate()"
        if par['cur'] == 'month':
            query += "AND date1 LIKE CONCAT(SUBSTRING(curdate(),1,7),'%')"
        if par['startdate'] is not None:
            query += f"AND date1 >= '{par['startdate']}'"
        if par['stopdate'] is not None:
            query += f"AND date1 <= '{par['stopdate']}'"

        sql = f"""
            SELECT COUNT(status = 'late' OR NULL) late,COUNT(status = 'excused' OR NULL) excused,COUNT(status = 'absent' OR NULL) absent,
            COUNT(status = 'miss' OR NULL) miss,COUNT(status = 'present' OR NULL) present 
            FROM 
            (SELECT date1 classdate,name1 student,intime,outtime,inip,outip,
            CASE WHEN intime IS NULL THEN 'absent' WHEN outtime IS NULL THEN 'miss' WHEN intime >= shouldin THEN 'late' 
            WHEN outtime <= shouldout THEN 'excused' ELSE 'present' END AS 'status' 
            FROM
            (SELECT curr.date date1,person.Name name1,curr.shouldin,curr.shouldout 
            FROM 
            (SELECT CONCAT(SUBSTRING(date,1,4)+1911, SUBSTRING(date,5)) date,
            str_to_date(CONCAT(min(starthour),':',startminute+1,':00'),'%H:%i:%s') shouldin,
            str_to_date(CONCAT(max(stophour),':',stopminute,':00'),'%H:%i:%s') shouldout 
            FROM curriculum.`{par['group']}` GROUP BY date) AS curr join personal_data.`{par['group']}` AS person) 
            AS currn left join 
            (SELECT a.date date2,a.fullname name2,intime,outtime,inip,outip 
            FROM 
            (SELECT SUBSTRING(FROM_UNIXTIME(timestamp),1,10) date,fullname, 
            SUBSTRING(CONVERT_TZ(FROM_UNIXTIME(min(timestamp)),@@session.time_zone,'+8:00'),12) intime,ipaddress inip
            FROM punch.`info` where `inout` = 'in' GROUP BY date,fullname) AS a left join 
            (SELECT SUBSTRING(FROM_UNIXTIME(timestamp),1,10) date,fullname, 
            SUBSTRING(CONVERT_TZ(FROM_UNIXTIME(max(timestamp)),@@session.time_zone,'+8:00'),12) outtime,ipaddress outip 
            FROM punch.`info` where `inout` = 'out' GROUP BY date,fullname) AS b using (date,fullname)) 
            AS pun ON currn.date1 = pun.date2 AND currn.name1 = pun.name2
            {query}) AS punchlog;
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


    @doc(description = "統計次數 : 遲到、早退、缺席、未打卡、出席", tags = ['Count'])
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
            SELECT date,part,course,TIMESTAMPDIFF(HOUR,shouldin,shouldout) hours,'123' classroom 
            FROM 
            (SELECT CONCAT(SUBSTRING(date,1,4)+1911, SUBSTRING(date,5)) date,
            CASE WHEN starthour <= 12 THEN 'AM' ELSE 'PM' END AS 'part',
            course,str_to_date(CONCAT(starthour,':',startminute,':00'),'%H:%i:%s') shouldin,
            str_to_date(CONCAT(stophour,':',stopminute,':00'),'%H:%i:%s') shouldout 
            FROM curriculum.`{par['group']}`) AS curr {query};
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
            

    @doc(description = "上傳課表 ( 課程、日期、時起、分起、時訖、分訖 )", tags = ['Curriculum'])
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
        sql = f"SELECT * FROM leavelist.`{par['group']}` {query} ORDER BY date DESC;"
        
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
    @doc(description = "各課程總時數、出席時數、總課程時數、課程總數、已進行課程數、當日課程學習資源", tags = ['Course'])
    @use_kwargs(GetCourseRequest,location = "query")
    def get(self,**kwargs):
        par = {
            'group': kwargs.get('group'),
            'name': kwargs.get('name'),
            'cur' : kwargs.get('cur'),
            'startdate': kwargs.get('startdate'),
            'stopdate': kwargs.get('stopdate'),
            'status': kwargs.get('status')
        }

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
            FROM punch.`info` where `inout` = 'in' GROUP BY date,fullname) AS a left join 
            (SELECT SUBSTRING(FROM_UNIXTIME(timestamp),1,10) date,fullname, 
            SUBSTRING(CONVERT_TZ(FROM_UNIXTIME(max(timestamp)),@@session.time_zone,'+8:00'),12) outtime,ipaddress outip 
            FROM punch.`info` where `inout` = 'out' GROUP BY date,fullname) AS b using (date,fullname)) 
            AS pun ON date = pun.date2 AND Name = pun.name2 {query} GROUP BY course;
        """

        totals = f"""
            SELECT COUNT(DISTINCT(course)) totalcourse,
            SUM(TIMESTAMPDIFF(HOUR,str_to_date(CONCAT(starthour,':',startminute,':00'),'%H:%i:%s'),
            str_to_date(CONCAT(stophour,':',stopminute,':00'),'%H:%i:%s'))) totalhours,
            COUNT(DISTINCT(CASE WHEN CONCAT(SUBSTRING(date,1,4)+1911, SUBSTRING(date,5)) <= curdate() THEN course END)) AS progress 
            FROM curriculum.`{par['group']}`;
        """

        videos = f"SELECT course,url FROM curriculum.`resource` WHERE date = curdate() AND groups = '{par['group']}' AND content = 'video';"

        articles = f"SELECT course,url FROM curriculum.`resource` WHERE date = curdate() AND groups = '{par['group']}' AND content = 'article';"

        try:
            db, cursor = db_init()
        except:
            return sta.failure('資料庫連線失敗')

        try:
            cursor.execute(courses)
            course = cursor.fetchall()
            cursor.execute(totals)
            total = cursor.fetchall()
            cursor.execute(videos)
            video = cursor.fetchall()
            cursor.execute(articles)
            article = cursor.fetchall()
            resource = {'video':video,'article':article}
            data={'course':course,'total':total,'resource':resource}
            db.commit()
            cursor.close()
            db.close()
            return sta.success(data)
        
        except:
            cursor.close()
            db.close()
            return sta.failure('參數有誤')


    @doc(description = "各課程總時數、出席時數、總課程時數、課程總數、已進行課程數、當日課程學習資源", tags = ['Course'])
    @use_kwargs(GetCourseRequest)
    def post(self,**kwargs):
        return redirect(url_for('course',**kwargs))
        
        
