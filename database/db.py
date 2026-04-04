import os
from urllib.parse import urlparse, unquote

import mysql.connector
from mysql.connector import Error


def _int_env(key, default):
    v = os.environ.get(key)
    if v is None or v == "":
        return default
    return int(v)


def _config_from_mysql_url(url):
    """Parse mysql://user:pass@host:port/db (Railway MYSQL_URL / MYSQL_PRIVATE_URL)."""
    if not url or not url.startswith("mysql"):
        return None
    parsed = urlparse(url)
    if not parsed.hostname:
        return None
    database = (parsed.path or "").lstrip("/") or None
    return {
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "database": database,
    }


def build_db_config():
    """Prefer full URL from Railway-linked MySQL, then discrete env vars."""
    for key in ("MYSQL_PRIVATE_URL", "MYSQL_URL", "DATABASE_URL"):
        url = os.environ.get(key)
        cfg = _config_from_mysql_url(url)
        if cfg and cfg.get("database"):
            return cfg

    return {
        "host": os.environ.get("MYSQLHOST") or os.environ.get("MYSQL_HOST", "localhost"),
        "user": os.environ.get("MYSQLUSER") or os.environ.get("MYSQL_USER", "root"),
        "password": os.environ.get("MYSQLPASSWORD")
        or os.environ.get("MYSQL_PASSWORD", "aabbcc123"),
        "database": os.environ.get("MYSQLDATABASE")
        or os.environ.get("MYSQL_DATABASE", "dream_pattern_db"),
        "port": _int_env("MYSQLPORT", _int_env("MYSQL_PORT", 3307)),
    }


DB_CONFIG = build_db_config()


def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error connecting to MariaDB: {e}")
        return None
