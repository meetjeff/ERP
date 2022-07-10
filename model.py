from marshmallow import Schema, fields
class GetPunchRequest(Schema):
    group = fields.Str(doc="group", required=True)
    name = fields.Str(doc="name")
    cur = fields.Str(doc="cur")
    startdate = fields.Date(doc="startdate")
    stopdate = fields.Date(doc="stopdate")
    status = fields.Str(doc="status")

class GetCountRequest(Schema):
    group = fields.Str(doc="group", required=True)
    name = fields.Str(doc="name")
    cur = fields.Str(doc="cur")
    startdate = fields.Date(doc="startdate")
    stopdate = fields.Date(doc="stopdate")

class GetCurriculumRequest(Schema):
    group = fields.Str(doc="group", required=True)
    month = fields.Str(doc="month")

class PostCurriculumRequest(Schema):
    group = fields.Str(doc="group", required=True)
    file = fields.Raw(type='file',doc="file")
