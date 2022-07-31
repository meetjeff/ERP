from flask import Flask
from flask_restful import Api
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_apispec.extension import FlaskApiSpec
from resource import Punch,Count,Curriculum,Leave,Course,Crawler,Login
# from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os
from dotenv import load_dotenv
from flask import jsonify
import logging

load_dotenv()

logging.basicConfig(filename = os.getenv("punchlog"),
                    level = logging.INFO,
                    format = "%(asctime)s %(message)s",
                    datefmt = "%d/%m/%Y %I:%M:%S %p")

app = Flask(__name__)
jwt = JWTManager(app)
# CORS(app)
api = Api(app)
app.config['JWT_SECRET_KEY'] = os.getenv("secretkey")
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes = int(os.getenv("tokenexpires")))
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config.update({
    'APISPEC_SPEC': APISpec(
        title = 'Erp Project API',
        version = 'v1',
        plugins = [MarshmallowPlugin()],
        openapi_version = '2.0.0'
    ),
    'APISPEC_SWAGGER_URL': '/api_doc',
    'APISPEC_SWAGGER_UI_URL': '/',
    'JSON_AS_ASCII': False,
    'MAX_CONTENT_LENGTH': 1024 * 1024
})
docs = FlaskApiSpec(app)

@app.errorhandler(422)
@app.errorhandler(400)
def handle_error(err):
    headers = err.data.get("headers", None)
    messages = err.data.get("messages", ["Invalid request."])
    logging.info(messages)
    if headers:
        return jsonify({"errors": messages}), err.code, headers
    else:
        return jsonify({"errors": messages}), err.code


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
api.add_resource(Crawler,'/crawler')
docs.register(Crawler)
api.add_resource(Login,'/login')
docs.register(Login)

# if __name__ == '__main__':
#     app.run('0.0.0.0', debug = True)
