import pymysql
import json
from flask_apispec import doc,use_kwargs,MethodResource
from model import GetPunchRequest,GetCountRequest,GetCurriculumRequest,PostCurriculumRequest
import sta
from flask import request, redirect, url_for
import csv

def db_init():
    db = pymysql.connect(
        host='ec2-34-208-156-155.us-west-2.compute.amazonaws.com',
        user='erp',
        password='erp',
        port=3306
    )
    cursor = db.cursor(pymysql.cursors.DictCursor)
    return db, cursor

class Punch(MethodResource):
    @doc(description="Punch", tags=['Punch'])
    @use_kwargs(GetPunchRequest,location="query")
    def get(self,**kwargs):
        db, cursor = db_init()

        par={
            'group': kwargs.get('group'),
            'name': kwargs.get('name'),
            'cur' : kwargs.get('cur'),
            'startdate': kwargs.get('startdate'),
            'stopdate': kwargs.get('stopdate'),
            'status': kwargs.get('status')
        }

        query='WHERE date1 <= curdate()'
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
            query += 'AND outtime IS NULL'

        sql = f"""
            SELECT date1 classdate,name1 student,intime,outtime,inip,outip,
            CASE WHEN intime IS NULL THEN 'absent' WHEN outtime IS NULL THEN 'miss' WHEN intime>=shouldin THEN 'late' WHEN outtime<=shouldout THEN 'excused' ELSE 'present' END AS 'status' 
            FROM
            (SELECT curr.date date1,person.Name name1,curr.shouldin,curr.shouldout 
            FROM 
            (SELECT CONCAT(SUBSTRING(date,1,4)+1911, SUBSTRING(date,5)) date,str_to_date(CONCAT(min(starthour),':',startminute+1,':00'),'%H:%i:%s') shouldin,str_to_date(CONCAT(max(stophour),':',stopminute,':00'),'%H:%i:%s') shouldout 
            FROM curriculum.`{par['group']}` GROUP BY date) AS curr join personal_data.`{par['group']}` AS person) 
            AS currn left join 
            (SELECT a.date date2,a.fullname name2,intime,outtime,inip,outip 
            FROM 
            (SELECT SUBSTRING(CONVERT_TZ(FROM_UNIXTIME(timestamp),@@session.time_zone,'+8:00'),1,10) date,fullname, min(SUBSTRING(CONVERT_TZ(FROM_UNIXTIME(timestamp),@@session.time_zone,'+8:00'),12)) intime,ipaddress inip
            FROM punch.`info` where `inout`='in' GROUP BY date,fullname) AS a left join 
            (SELECT SUBSTRING(CONVERT_TZ(FROM_UNIXTIME(timestamp),@@session.time_zone,'+8:00'),1,10) date,fullname, max(SUBSTRING(CONVERT_TZ(FROM_UNIXTIME(timestamp),@@session.time_zone,'+8:00'),12)) outtime,ipaddress outip 
            FROM punch.`info` where `inout`='out' GROUP BY date,fullname) AS b using (date,fullname)) 
            AS pun ON currn.date1=pun.date2 AND currn.name1=pun.name2
            {query}
            ORDER BY date1 DESC;
        """

        try:
            cursor.execute(sql)
            data = json.dumps(cursor.fetchall())
            db.commit()
            cursor.close()
            db.close()

            return sta.success(data)

        except:
            return sta.failure('參數有誤')


class Count(MethodResource):
    @doc(description="Count", tags=['Count'])
    @use_kwargs(GetCountRequest,location="query")
    def get(self,**kwargs):
        db, cursor = db_init()

        par={
            'group': kwargs.get('group'),
            'name': kwargs.get('name'),
            'cur' : kwargs.get('cur'),
            'startdate': kwargs.get('startdate'),
            'stopdate': kwargs.get('stopdate')
        }

        query='WHERE date1 <= curdate()'
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
            SELECT COUNT(status='late' OR NULL) late,COUNT(status='excused' OR NULL) excused,COUNT(status='absent' OR NULL) absent,COUNT(status='miss' OR NULL) miss,COUNT(status='present' OR NULL) present 
            FROM 
            (SELECT date1 classdate,name1 student,intime,outtime,inip,outip,
            CASE WHEN intime IS NULL THEN 'absent' WHEN outtime IS NULL THEN 'miss' WHEN intime>=shouldin THEN 'late' WHEN outtime<=shouldout THEN 'excused' ELSE 'present' END AS 'status' 
            FROM
            (SELECT curr.date date1,person.Name name1,curr.shouldin,curr.shouldout 
            FROM 
            (SELECT CONCAT(SUBSTRING(date,1,4)+1911, SUBSTRING(date,5)) date,str_to_date(CONCAT(min(starthour),':',startminute+1,':00'),'%H:%i:%s') shouldin,str_to_date(CONCAT(max(stophour),':',stopminute,':00'),'%H:%i:%s') shouldout 
            FROM curriculum.`{par['group']}` GROUP BY date) AS curr join personal_data.`{par['group']}` AS person) 
            AS currn left join 
            (SELECT a.date date2,a.fullname name2,intime,outtime,inip,outip 
            FROM 
            (SELECT SUBSTRING(CONVERT_TZ(FROM_UNIXTIME(timestamp),@@session.time_zone,'+8:00'),1,10) date,fullname, min(SUBSTRING(CONVERT_TZ(FROM_UNIXTIME(timestamp),@@session.time_zone,'+8:00'),12)) intime,ipaddress inip
            FROM punch.`info` where `inout`='in' GROUP BY date,fullname) AS a left join 
            (SELECT SUBSTRING(CONVERT_TZ(FROM_UNIXTIME(timestamp),@@session.time_zone,'+8:00'),1,10) date,fullname, max(SUBSTRING(CONVERT_TZ(FROM_UNIXTIME(timestamp),@@session.time_zone,'+8:00'),12)) outtime,ipaddress outip 
            FROM punch.`info` where `inout`='out' GROUP BY date,fullname) AS b using (date,fullname)) 
            AS pun ON currn.date1=pun.date2 AND currn.name1=pun.name2
            {query}) AS punchlog;
        """

        try:
            cursor.execute(sql)
            data = json.dumps(cursor.fetchall())
            db.commit()
            cursor.close()
            db.close()

            return sta.success(data)

        except:
            return sta.failure('參數有誤')


class Curriculum(MethodResource):
    @doc(description="GetCurriculum", tags=['Curriculum'])
    @use_kwargs(GetCurriculumRequest,location="query")
    def get(self,**kwargs):
        db, cursor = db_init()

        par={
            'group': kwargs.get('group'),
            'month': kwargs.get('month')
        }

        query = ""
        if par['month'] is not None:
            query = f"WHERE date LIKE '{par['month']}%'"
        

        sql = f"""
            SELECT date,part,course,TIMESTAMPDIFF(HOUR,shouldin,shouldout) hours,'123' classroom 
            FROM 
            (SELECT CONCAT(SUBSTRING(date,1,4)+1911, SUBSTRING(date,5)) date,CASE WHEN starthour <= 12 THEN 'AM' ELSE 'PM' END AS 'part',
            course,str_to_date(CONCAT(starthour,':',startminute,':00'),'%H:%i:%s') shouldin,str_to_date(CONCAT(stophour,':',stopminute,':00'),'%H:%i:%s') shouldout 
            FROM curriculum.`{par['group']}`) AS curr {query};
        """

        try:
            cursor.execute(sql)
            data = json.dumps(cursor.fetchall(),ensure_ascii=False)
            db.commit()
            cursor.close()
            db.close()

            return sta.success(data)

        except:
            return sta.failure('參數有誤')
            

    @doc(description="UploadCurriculum", tags=['Curriculum'])
    @use_kwargs(PostCurriculumRequest,location="form")
    def post(self,**kwargs):
        group = request.values.get('group')
        file = request.files.get('file')
        if file is None :
            return sta.failure('未上傳課表檔案(csv)')

        create = f"""
            CREATE TABLE IF NOT EXISTS curriculum.{group} (course varchar(50),date date,starthour int(10),startminute int(10),stophour int(10),stopminute int(10));
        """
        truncate = f"TRUNCATE TABLE curriculum.{group};"
        val = []
        
        ts=file.readline()
        while ts is not None and ts != '':
            ts=file.readline().decode("utf-8")
            if ts is None or ts == '':
                break
            tsn=f"('{ts.split(',')[0]}','{ts.split(',')[1]}',"+",".join(ts.split(',')[2:])+")"
            val.append(tsn)
        file.close()

        val = ",".join(val)
        insert = f"INSERT INTO curriculum.{group} VALUES {val};"
        
        db, cursor = db_init()
        cursor.execute(create)
        cursor.execute(truncate)
        cursor.execute(insert)
        db.commit()
        cursor.close()
        db.close()

        return redirect(url_for('curriculum',group=group))



