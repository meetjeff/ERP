import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def db_init():
    db = pymysql.connect(
        host = os.getenv("dbip"),
        user = os.getenv("dbuser"),
        password = os.getenv("dbpassword"),
        port = int(os.getenv("dbport"))
    )
    cursor = db.cursor(pymysql.cursors.DictCursor)
    return db, cursor
