import mysql.connector
from mysql.connector import Error
import os

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('MYSQLHOST', 'localhost'),
    'user': os.environ.get('MYSQLUSER', 'root'),
    'password': os.environ.get('MYSQLPASSWORD', 'aabbcc123'),
    'database': os.environ.get('MYSQLDATABASE', 'dream_pattern_db'),
    'port': int(os.environ.get('MYSQLPORT', 3307))
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error connecting to MariaDB: {e}")
        return None
