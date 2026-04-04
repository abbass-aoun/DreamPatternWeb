from flask import Blueprint, jsonify
from database.db import get_db_connection

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/api/stats/user/<int:user_id>', methods=['GET'])
def get_user_stats(user_id):
    """Get overall statistics for a user"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT COUNT(*) as total_dreams FROM DREAM WHERE user_id = %s",
            (user_id,)
        )
        total_dreams = cursor.fetchone()['total_dreams']

        cursor.execute(
            "SELECT COUNT(*) as lucid_dreams FROM DREAM WHERE user_id = %s AND lucid = TRUE",
            (user_id,)
        )
        lucid_dreams = cursor.fetchone()['lucid_dreams']

        cursor.execute(
            "SELECT AVG(intensity) as avg_intensity FROM DREAM WHERE user_id = %s",
            (user_id,)
        )
        avg_intensity = cursor.fetchone()['avg_intensity'] or 0

        cursor.execute(
            "SELECT MAX(dream_date) as last_dream FROM DREAM WHERE user_id = %s",
            (user_id,)
        )
        last_dream = cursor.fetchone()['last_dream']

        return jsonify({
            "total_dreams": total_dreams,
            "lucid_dreams": lucid_dreams,
            "lucid_percentage": (lucid_dreams / total_dreams * 100) if total_dreams > 0 else 0,
            "average_intensity": round(float(avg_intensity), 2),
            "last_dream_date": last_dream.isoformat() if last_dream else None
        }), 200

    except Exception as e:
        print(f"Stats error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@stats_bp.route('/api/emotions', methods=['GET'])
def get_all_emotions():
    """Get all available emotions"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM EMOTION ORDER BY emotion_type")
        emotions = cursor.fetchall()
        return jsonify(emotions), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@stats_bp.route('/api/themes', methods=['GET'])
def get_all_themes():
    """Get all available themes"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM THEME ORDER BY theme_name")
        themes = cursor.fetchall()
        return jsonify(themes), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@stats_bp.route('/api/categories', methods=['GET'])
def get_all_categories():
    """Get all available categories"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM CATEGORY ORDER BY category_name")
        categories = cursor.fetchall()
        return jsonify(categories), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@stats_bp.route('/api/stats/emotions/<int:user_id>', methods=['GET'])
def get_user_emotions(user_id):
    """Get emotion frequency for user"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT e.emotion_type, COUNT(de.dream_id) as frequency
            FROM EMOTION e
            INNER JOIN DREAM_EMOTION de ON e.emotion_id = de.emotion_id
            INNER JOIN DREAM d ON de.dream_id = d.dream_id
            WHERE d.user_id = %s
            GROUP BY e.emotion_id, e.emotion_type
            ORDER BY frequency DESC
            LIMIT 8
        """, (user_id,))

        emotions = cursor.fetchall()
        return jsonify(emotions), 200

    except Exception as e:
        print(f"Get emotions error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@stats_bp.route('/api/stats/themes/<int:user_id>', methods=['GET'])
def get_user_themes(user_id):
    """Get theme frequency for user"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT t.theme_name, COUNT(dt.dream_id) as dream_count
            FROM THEME t
            INNER JOIN DREAM_THEME dt ON t.theme_id = dt.theme_id
            INNER JOIN DREAM d ON dt.dream_id = d.dream_id
            WHERE d.user_id = %s
            GROUP BY t.theme_id, t.theme_name
            ORDER BY dream_count DESC
            LIMIT 10
        """, (user_id,))

        themes = cursor.fetchall()
        return jsonify(themes), 200

    except Exception as e:
        print(f"Get themes error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()