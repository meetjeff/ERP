from datetime import datetime
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(filename = os.getenv("punchlog"),
                    level = logging.INFO,
                    format = "%(asctime)s %(message)s",
                    datefmt = "%d/%m/%Y %I:%M:%S %p")

def success(data = None):
    if data is None:
        return {'message': 'success'}, 200

    return {
        'message': 'success',
        'data': data,
        'datatime': datetime.now()
    }, 200

def failure(message,e = None):
    if e != None:
        logging.info(e)
    return {"message": "failure," + message}, 400
