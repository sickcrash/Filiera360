import os
import pymysql
import time

# le variabili d'ambiente ottenute da Docker Compose
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = "filiera360"
MYSQL_DB = os.getenv("MYSQL_DB", "filiera360")
def get_db_connection():
    max_retries = 10

    for attempt in range(max_retries):
     try:
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            port=3306,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    
     except pymysql.MySQLError as e:
        print(f"Connection failed on attempt {attempt + 1}/{max_retries}: {e}")
        time.sleep(2)
    raise Exception("Could not connect to MySQL after several retries.")