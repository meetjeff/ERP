# ERP API

## /api_doc
###### -GET-
**api documentation**  

## /login
###### -GET-
依班級、姓名、當日或當月、日期範圍篩選統計數字   
( 每日遲到、早退、缺席、未打卡、請假、出席數，應出席、出席、缺席、請假時數，範圍總合及總人數 )

**Input Parameters :**
* group　　&thinsp;( 班級，e.g., fn101 )
* name　 　&thinsp;( 姓名，不分大小寫，e.g., jeff )
* cur　　　&thinsp;&thinsp;&thinsp;( 當日或當月，當日 : today，當月 : month )
* startdate　( 起始日期，e.g., 2022-01-01 )
* stopdate　( 結束日期，e.g., 2022-01-01 )

**Success Example**

## /count
###### -GET、POST-
依班級、姓名、當日或當月、日期範圍篩選統計數字   
( 每日遲到、早退、缺席、未打卡、請假、出席數，應出席、出席、缺席、請假時數，範圍總合及總人數 )

**Input Parameters :**
* group　　&thinsp;( 班級，e.g., fn101 )
* name　 　&thinsp;( 姓名，不分大小寫，e.g., jeff )
* cur　　　&thinsp;&thinsp;&thinsp;( 當日或當月，當日 : today，當月 : month )
* startdate　( 起始日期，e.g., 2022-01-01 )
* stopdate　( 結束日期，e.g., 2022-01-01 )

**Success Example**
```yaml
{
  "data": [
    {
      "absent": 5,
      "attendancehours": "190.5832",
      "day": "2022-04-11",
      "excused": 2,
      "lackhours": "72.9168",
      "late": 11,
      "leave": 1,
      "leavehours": "8.5000",
      "miss": 3,
      "number of people": 31,
      "regular": 13,
      "totalhours": "263.5000"
    },
    .
    .
    .
    {
      "absent": 21,
      "attendancehours": "33.9333",
      "day": "2022-05-26",
      "excused": 1,
      "lackhours": "198.5667",
      "late": 5,
      "leave": 0,
      "leavehours": "0.0000",
      "miss": 4,
      "number of people": 31,
      "regular": 3,
      "totalhours": "232.5000"
    },
    {
      "absent": 864,
      "attendancehours": "17547.1662",
      "day": "total",
      "excused": 113,
      "lackhours": "8996.3338",
      "late": 872,
      "leave": 29,
      "leavehours": "145.5000",
      "miss": 166,
      "number of people": 31,
      "regular": 1444,
      "totalhours": "26543.5000"
    }
  ],
  "datatime": "2022-07-22T05:41:36.720744",
  "message": "success"
}
```  

## /course
###### -GET、POST-
依班級、姓名、當日或當月、日期範圍、進行狀態篩選課程  
( 各課程總時數、出席時數、總課程時數、課程總數、已進行課程數、課程學習資源 )

**Input Parameters :**
* group　　&thinsp;( 班級，e.g., fn101 )
* name　 　&thinsp;( 姓名，不分大小寫，e.g., jeff )
* cur　　　&thinsp;&thinsp;&thinsp;( 當日或當月，當日 : today，當月 : month )
* startdate　( 起始日期，e.g., 2022-01-01 )
* stopdate　( 結束日期，e.g., 2022-01-01 )
* status　　&thinsp;( 課程狀態，已進行 : progress，未開始 : unfinished )
* course　　( 課程名稱，獲取該課程學習資源 )

**Success Example**
```yaml
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
```
**Input course**
```yaml
{
  "data": {
    "article": [
      {
        "title": "鳥哥私房菜 - Linux 伺服器篇各年份各版本的學習資料",
        "url": "https://linux.vbird.org/linux_server/"
      },
      {
        "title": "鳥哥私房菜 - 第一章、架設伺服器前的準備工作",
        "url": "https://linux.vbird.org/linux_server/centos6/0105beforeserver.php"
      },
      {
        "title": "ubuntu 基礎架站 - Alvin Chen Club",
        "url": "http://www.alvinchen.club/2018/04/12/ubuntu-%E5%9F%BA%E7%A4%8E%E6%9E%B6%E7%AB%99/"
      }
    ],
    "video": [
      {
        "url": "https://www.youtube.com/embed/m7meyDFDGMo"
      },
      {
        "url": "https://www.youtube.com/embed/brP8mgNeg0Q"
      },
      {
        "url": "https://www.youtube.com/embed/BH_2h2ZPVu8"
      }
    ]
  },
  "datatime": "2022-07-23T18:42:49.404920",
  "message": "success"
}
```  
## /crawler
###### -GET-
查看學習資源爬蟲執行狀態 ( 班級、影片、文章、最後更新時間 )

**Input Parameters :**
* group　　&thinsp;( 班級，e.g., fn101 )

**Success Example**
```yaml
{
  "articles": "in progress",
  "date": "Sat, 23 Jul 2022 18:57:53 GMT",
  "groups": "fn102",
  "videos": "finished"
}
```

###### -POST-
手動執行學習資源爬蟲 ( 課表上傳成功會自動觸發 )

**Input Parameters :**
* group　　&thinsp;( 班級，e.g., fn101 )

**Success Example**
```yaml
{
  "articles": "in progress",
  "date": "Sat, 23 Jul 2022 18:56:09 GMT",
  "groups": "fn102",
  "videos": "in progress"
}
```  

## /curriculum
###### -GET-
依班級、月份篩選課表 ( 日期、時段、課程、時數、教室 )

**Input Parameters :**
* group　　&thinsp;( 班級，e.g., fn101 )
* month　　( 月份，e.g., 2022-04 )

**Success Example**
```yaml
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
```

###### -POST-
依班級上傳課表 ( 課程、日期、時起、分起、時訖、分訖 )  
上傳成功後觸發學習資源爬蟲

**Input Parameters :**
* group　　&thinsp;( 班級，e.g., fn101 )
* file　　　&thinsp;&thinsp;&thinsp;( 課表csv檔、6欄、utf-8編碼，e.g., 課表.csv )

**Success Example  ( 返回更新後的課表及爬蟲啟動狀態、時間 )**
```yaml
{
  "data": {
    "crawlerstatus": "{'articles': 'in progress', 'date': 'Sat, 23 Jul 2022 18:45:42 GMT', 'groups': 'se102', 'videos': 'in progress'}",
    "curriculum": [
      {
        "classroom": "123",
        "course": "開訓典禮",
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
    ]
  },
  "datatime": "2022-07-23T18:45:42.354838",
  "message": "success"
}
```  

## /leave
###### -GET-
依班級、姓名、當日或當月、日期範圍、假別篩選請假列表 ( 姓名、日期、時段、假別、原因 )

**Input Parameters :**
* group　　&thinsp;( 班級，e.g., fn101 )
* name　 　&thinsp;( 姓名，不分大小寫，e.g., jeff )
* cur　　　&thinsp;&thinsp;&thinsp;( 當日或當月，當日 : today，當月 : month )
* startdate　( 起始日期，e.g., 2022-01-01 )
* stopdate　( 結束日期，e.g., 2022-01-01 )
* leavetype &thinsp;&thinsp;( 假別，e.g., 病假 )

**Success Example**
```yaml
{
  "data": [
    {
      "date": "2022-03-29",
      "name": "Mia",
      "reason": "驗PCR\r\n",
      "time": "上午 9:00 ~ 12:00",
      "type": "特殊原因"
    },
    {
      "date": "2022-03-29",
      "name": "Peter",
      "reason": "no reason",
      "time": "下午 13:30~ 課程結束",
      "type": "病假"
    }
  ],
  "datatime": "2022-07-11T07:14:13.042239",
  "message": "success"
}
```

###### -POST-
依班級上傳請假表單 ( 姓名、日期、時段、假別、原因 )

**Input Parameters :**
* group　　&thinsp;( 班級，e.g., fn101 )
* file　　　&thinsp;&thinsp;&thinsp;( 請假csv檔、5欄、utf-8編碼，e.g., 請假.csv )

**Success Example  ( 返回更新後的請假表單 )**
```yaml
{
  "data": [
    {
      "date": "2022-03-29",
      "name": "Mia",
      "reason": "驗PCR\r\n",
      "time": "上午 9:00 ~ 12:00",
      "type": "特殊原因"
    },
    .
    .
    .
    {
      "date": "2022-03-29",
      "name": "Peter",
      "reason": "no reason",
      "time": "下午 13:30~ 課程結束",
      "type": "病假"
    }
  ],
  "datatime": "2022-07-11T07:14:13.042239",
  "message": "success"
}
```

## /punch
###### -GET、POST-
依班級、姓名、當日或當月、日期範圍、打卡狀態篩選出缺勤列表  
( 日期、姓名、簽到、簽退、簽到ip、簽退ip、打卡狀態 )  
可依單頁筆數進行分頁篩選 ( 回傳總筆數、總頁數 )

**Input Parameters :**
* group　　&thinsp;( 班級，e.g., fn101 )
* name　 　&thinsp;( 姓名，不分大小寫，e.g., jeff )
* cur　　　&thinsp;&thinsp;&thinsp;( 當日或當月，當日 : today，當月 : month )
* startdate　( 起始日期，e.g., 2022-01-01 )
* stopdate　( 結束日期，e.g., 2022-01-01 )
* status　　&thinsp;&thinsp;( 打卡狀態，遲到 : late，早退 : excused，缺席 : absent，未打卡 : miss )
* rows　　　( 單頁顯示筆數，預設30，e.g., 100 )
* page　　　( 第幾頁，預設1，e.g., 20 )

**Success Example**
```yaml
{
  "data": {
    "pagination": [
      {
        "totalpages": "67",
        "totalrows": 3348
      }
    ],
    "punch": [
      {
        "classdate": "2022-01-24",
        "inip": "61.66.146.110",
        "intime": "09:28:33",
        "outip": "61.66.147.98",
        "outtime": "17:37:23",
        "status": "late",
        "student": "JiaRong"
      },
      .
      .
      .
      {
        "classdate": "2022-01-21",
        "inip": "140.137.222.59",
        "intime": "08:41:04",
        "outip": "140.137.222.59",
        "outtime": "17:37:45",
        "status": "present",
        "student": "Max"
      }
    ]
  },
  "datatime": "2022-07-11T10:28:51.722611",
  "message": "success"
}
```
