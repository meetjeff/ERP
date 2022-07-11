from flask import Flask
from flask_restful import Api
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_apispec.extension import FlaskApiSpec
from resource import Punch,Count,Curriculum,Leave,Course

app = Flask(__name__)
api = Api(app)
app.config.update({
    'APISPEC_SPEC': APISpec(
        title='Erp Project API',
        version='v1',
        plugins=[MarshmallowPlugin()],
        openapi_version='2.0.0'
    ),
    'APISPEC_SWAGGER_URL': '/api_doc',
    'APISPEC_SWAGGER_UI_URL': '/',
    'JSON_AS_ASCII': False,
    'MAX_CONTENT_LENGTH': 1024 * 1024
})
docs = FlaskApiSpec(app)

api.add_resource(Punch,'/punch')
docs.register(Punch)
api.add_resource(Count,'/count')
docs.register(Count)
api.add_resource(Curriculum,'/curriculum')
docs.register(Curriculum)
api.add_resource(Leave,'/leave')
docs.register(Leave)
api.add_resource(Course,'/course')
docs.register(Course)

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)
