import psycopg2
from prac08.config import load_config

def connect():
    config = load_config()
    try:
        conn = psycopg2.connect(**config)
        print("Connected successfully!")
        conn.close()
    except Exception as e:
        print("Error:", e)

connect()
