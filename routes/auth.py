from flask import Blueprint, request, jsonify
from database.db import get_db_connection
from datetime import datetime, timedelta
import hashlib

auth_bp = Blueprint('auth', __name__)


def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()


@auth_bp.route('/api/register', methods=['POST'])
def register():
    """Register new user with FREE TRIAL subscription - TRANSACTION"""
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    birthdate = data.get('birthdate')

    if not all([username, email, password]):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        # START TRANSACTION
        conn.start_transaction()

        # Check if email already exists
        cursor.execute("SELECT user_id FROM USER WHERE email = %s", (email,))
        if cursor.fetchone():
            conn.rollback()
            return jsonify({"error": "Email already registered"}), 409

        # Hash password
        hashed_password = hash_password(password)

        # Insert new user
        cursor.execute(
            """INSERT INTO USER (username, email, password, birthdate) 
               VALUES (%s, %s, %s, %s)""",
            (username, email, hashed_password, birthdate)
        )
        user_id = cursor.lastrowid

        # Create FREE TRIAL subscription (7 days)
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=7)

        cursor.execute(
            """INSERT INTO SUBSCRIPTION 
               (user_id, start_date, end_date, plan_type, status, auto_renew) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (user_id, start_date, end_date, 'FREE_TRIAL', 'ACTIVE', False)
        )

        # COMMIT TRANSACTION
        conn.commit()

        # RETURN USER OBJECT for auto-login
        return jsonify({
            "message": "Registration successful! 7-day free trial activated.",
            "user": {
                "user_id": user_id,
                "username": username,
                "email": email,
                "subscription": {
                    "plan_type": "FREE_TRIAL",
                    "status": "ACTIVE",
                    "end_date": end_date.isoformat()
                }
            }
        }), 201

    except Exception as e:
        conn.rollback()
        print(f"Registration error: {e}")
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


@auth_bp.route('/api/login', methods=['POST'])
def login():
    """User login"""
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        hashed_password = hash_password(password)

        cursor.execute(
            """SELECT u.user_id, u.username, u.email, 
                      s.plan_type, s.status, s.end_date
               FROM USER u
               LEFT JOIN SUBSCRIPTION s ON u.user_id = s.user_id 
                   AND s.status = 'ACTIVE'
               WHERE u.email = %s AND u.password = %s""",
            (email, hashed_password)
        )

        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "Invalid email or password"}), 401

        return jsonify({
            "message": "Login successful",
            "user": {
                "user_id": user['user_id'],
                "username": user['username'],
                "email": user['email'],
                "subscription": {
                    "plan_type": user['plan_type'],
                    "status": user['status'],
                    "end_date": user['end_date'].isoformat() if user['end_date'] else None
                }
            }
        }), 200

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"error": f"Login failed: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()