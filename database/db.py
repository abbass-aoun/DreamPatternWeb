import mysql.connector
from mysql.connector import Error

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'aabbcc123',  # ← CHANGE THIS to your actual MariaDB password
    'database': 'dream_pattern_db',
    'port': 3307  # ← Added port (change to 3306 if that's your port)
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error connecting to MariaDB: {e}")
        return None