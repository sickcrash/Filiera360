from database.db_connection import get_db_connection
from datetime import datetime
import pytz
from datetime import timedelta

def insert_or_update_otp(email, otp):
    local_tz = pytz.timezone("Europe/Rome")
    expiration_time = (datetime.now(local_tz) + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")

    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO otp_codes (email, otp, expiration)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE otp = VALUES(otp), expiration = VALUES(expiration)
        """, (email, otp, expiration_time))
    connection.commit()
    connection.close()



def get_otp_record(email):
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT otp, expiration FROM otp_codes WHERE email = %s", (email,))
        return cursor.fetchone()


def get_latest_otp(email):
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT otp FROM otp_codes WHERE email = %s", (email,))
        return cursor.fetchone()
