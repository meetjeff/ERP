# ERP API

/api_doc :
@GET
api documentation


/count :
@GET、POST (依班級、姓名、當日或當月、日期範圍篩選遲到、早退、缺席、未打卡、出席次數)

-Input Parameters (group必填，其他可選) :
group (班級，e.g.,fn101)
name (姓名，不分大小寫，e.g.,amy)
cur (當日或當月，當日:today，當月:month)
startdate (起始日期，e.g.,2022-01-01)
stopdate (結束日期，e.g.,2022-01-01)

-Success Example:
{
  "data": [
    {
      "absent": 774,
      "excused": 57,
      "late": 837,
      "miss": 175,
      "present": 1505
    }
  ],
  "datatime": "2022-07-11T07:29:10.746734",
  "message": "success"
}


/course :
@GET、POST (依班級、姓名、當日或當月、日期範圍、課程狀態篩選各課程總時數、出席時數，以及總課程時數、課程總數、已進行課程數、當日課程學習資源)

-Input Parameters (group必填，其他可選) :
group (班級，e.g.,fn101)
name (姓名，不分大小寫，e.g.,amy)
cur (當日或當月，當日:today，當月:month)
startdate (起始日期，e.g.,2022-01-01)
stopdate (結束日期，e.g.,2022-01-01)
status (課程狀態，已進行:progress，未開始:unfinished)

-Success Example:
{
  "data": {
    "course": [
      {
        "course": "JS與Node.js",
        "present": "182.7501",
        "totalhours": "217"
      },
      {
        "course": "個人網頁專題製作",
        "present": "166.4500",
        "totalhours": "217"
      }
    ],
    "resource": [
      {
        "course": "JS與Node.js",
        "url": "https://www.youtube.com/watch?v=RpMVP52YQRQ"
      },
      {
        "course": "個人網頁專題製作",
        "url": "https://www.youtube.com/watch?v=CLUPkcLQm64"
      }
    ],
    "total": [
      {
        "progress": 34,
        "totalcourse": 34,
        "totalhours": "697"
      }
    ]
  },
  "datatime": "2022-07-11T07:52:01.456255",
  "message": "success"
}


/curriculum :
@GET (依班級、月份篩選課表)

-Input Parameters (group必填，其他可選) :
group (班級，e.g.,fn101)
month (月份，e.g.,2022-04)

-Success Example:
{
  "data": [
    {
      "classroom": "123",
      "course": "產品設計輔導",
      "date": "2022-04-01",
      "hours": 3,
      "part": "AM"
    },
    .
    .
    .
    {
      "classroom": "123",
      "course": "企業實習",
      "date": "2022-04-29",
      "hours": 3,
      "part": "PM"
    }
  ],
  "datatime": "2022-07-11T08:02:59.941018",
  "message": "success"
}

@POST (依班級上傳課表)

-Input Parameters (group必填，其他可選) :
group (班級，e.g.,fn101)
file (課表csv檔，e.g.,課表.csv)

-Success Example (返回更新後的課表):
{
  "data": [
    {
      "classroom": "123",
      "course": "阿甘正傳",
      "date": "2021-12-15",
      "hours": 3,
      "part": "AM"
    },
    .
    .
    .
    {
      "classroom": "123",
      "course": "產品實做",
      "date": "2022-05-26",
      "hours": 3,
      "part": "PM"
    }
  ],
  "datatime": "2022-07-11T08:06:41.057632",
  "message": "success"
}


/leave :
@GET (依班級、姓名、當日或當月、日期範圍、假別篩選請假列表)

-Input Parameters (group必填，其他可選) :
group (班級，e.g.,fn101)
name (姓名，不分大小寫，e.g.,amy)
cur (當日或當月，當日:today，當月:month)
startdate (起始日期，e.g.,2022-01-01)
stopdate (結束日期，e.g.,2022-01-01)
leavetype (假別，e.g.,病假)

-Success Example:
{
  "data": [
    {
      "date": "Tue, 29 Mar 2022 00:00:00 GMT",
      "name": "Mia",
      "reason": "驗PCR\r\n",
      "time": "上午 9:00 ~ 12:00",
      "type": "特殊原因"
    },
    {
      "date": "Tue, 29 Mar 2022 00:00:00 GMT",
      "name": "Peter",
      "reason": "no reason",
      "time": "下午 13:30~ 課程結束",
      "type": "病假"
    }
  ],
  "datatime": "2022-07-11T07:14:13.042239",
  "message": "success"
}

@POST (依班級上傳請假表單)

-Input Parameters (group必填，其他可選) :
group (班級，e.g.,fn101)
file (請假csv檔，e.g.,請假.csv)

-Success Example (返回更新後的請假表單):
{
  "data": [
    {
      "date": "Tue, 29 Mar 2022 00:00:00 GMT",
      "name": "Mia",
      "reason": "驗PCR\r\n",
      "time": "上午 9:00 ~ 12:00",
      "type": "特殊原因"
    },
    .
    .
    .
    {
      "date": "Tue, 29 Mar 2022 00:00:00 GMT",
      "name": "Peter",
      "reason": "no reason",
      "time": "下午 13:30~ 課程結束",
      "type": "病假"
    }
  ],
  "datatime": "2022-07-11T07:14:13.042239",
  "message": "success"
}


/punch





