from flask import Flask,render_template
from flask_restful import Api
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_apispec.extension import FlaskApiSpec
from resource import Punch,Count,Curriculum

app = Flask(__name__)
api = Api(app)
app.config.update({
    'APISPEC_SPEC': APISpec(
        title='Erp Project API',
        version='v1',
        plugins=[MarshmallowPlugin()],
        openapi_version='2.0.0'
    ),
    'APISPEC_SWAGGER_URL': '/api_doc',  # URI to access API Doc JSON
    'APISPEC_SWAGGER_UI_URL': '/', # URI to access UI of API Doc
    'JSON_AS_ASCII': False
})
docs = FlaskApiSpec(app)

@app.route('/upload')
def upload():
    return render_template('upload.html')

api.add_resource(Punch,'/punch')
docs.register(Punch)
api.add_resource(Count,'/count')
docs.register(Count)
api.add_resource(Curriculum,'/curriculum')
docs.register(Curriculum)


if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)
