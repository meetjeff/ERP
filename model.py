from marshmallow import Schema, fields
class GetPunchRequest(Schema):
    group = fields.Str(doc = "group", required = True)
    name = fields.Str(doc = "name")
    cur = fields.Str(doc = "cur")
    startdate = fields.Date(doc = "startdate")
    stopdate = fields.Date(doc = "stopdate")
    status = fields.Str(doc = "status")
    rows = fields.Int(doc = "rows")
    page = fields.Int(doc = "page")

class GetCourseRequest(Schema):
    group = fields.Str(doc = "group", required = True)
    name = fields.Str(doc = "name")
    cur = fields.Str(doc = "cur")
    startdate = fields.Date(doc = "startdate")
    stopdate = fields.Date(doc = "stopdate")
    status = fields.Str(doc = "status")
    course = fields.Str(doc = "course")

class GetCountRequest(Schema):
    group = fields.Str(doc = "group", required = True)
    name = fields.Str(doc = "name")
    cur = fields.Str(doc = "cur")
    startdate = fields.Date(doc = "startdate")
    stopdate = fields.Date(doc = "stopdate")

class GetCurriculumRequest(Schema):
    group = fields.Str(doc = "group", required = True)
    month = fields.Str(doc = "month")

class PostCurriculumRequest(Schema):
    group = fields.Str(doc = "group", required = True)
    file = fields.Raw(type = 'file',doc = "file")

class GetLeaveRequest(Schema):
    group = fields.Str(doc = "group", required = True)
    name = fields.Str(doc = "name")
    cur = fields.Str(doc = "cur")
    startdate = fields.Date(doc = "startdate")
    stopdate = fields.Date(doc = "stopdate")
    leavetype = fields.Str(doc = "leavetype")
    
class CrawlerRequest(Schema):
    group = fields.Str(doc="group", required=True)
