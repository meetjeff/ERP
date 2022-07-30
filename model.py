from marshmallow import Schema, fields
class GetPunchRequest(Schema):
    group = fields.Str(doc = "group")
    name = fields.Str(doc = "name")
    cur = fields.Str(doc = "cur")
    startdate = fields.Date(doc = "startdate")
    stopdate = fields.Date(doc = "stopdate")
    status = fields.Str(doc = "status")
    rows = fields.Int(doc = "rows")
    page = fields.Int(doc = "page")

class GetCourseRequest(Schema):
    group = fields.Str(doc = "group")
    name = fields.Str(doc = "name")
    cur = fields.Str(doc = "cur")
    startdate = fields.Date(doc = "startdate")
    stopdate = fields.Date(doc = "stopdate")
    status = fields.Str(doc = "status")
    course = fields.Str(doc = "course")

class GetCountRequest(Schema):
    group = fields.Str(doc = "group")
    name = fields.Str(doc = "name")
    cur = fields.Str(doc = "cur")
    startdate = fields.Date(doc = "startdate")
    stopdate = fields.Date(doc = "stopdate")

class GetCurriculumRequest(Schema):
    group = fields.Str(doc = "group")
    month = fields.Str(doc = "month")

class GetLeaveRequest(Schema):
    group = fields.Str(doc = "group")
    name = fields.Str(doc = "name")
    cur = fields.Str(doc = "cur")
    startdate = fields.Date(doc = "startdate")
    stopdate = fields.Date(doc = "stopdate")
    leavetype = fields.Str(doc = "leavetype")

class PostFileRequest(Schema):
    group = fields.Str(doc = "group", required = True)
    file = fields.Raw(type = 'file',doc = "file")
    
class CrawlerRequest(Schema):
    group = fields.Str(doc="group", required=True)

class LoginRequest(Schema):
    group = fields.Str(doc="group", required=True)
    account = fields.Str(doc="account", required=True)
    password = fields.Str(doc="password", required=True)
