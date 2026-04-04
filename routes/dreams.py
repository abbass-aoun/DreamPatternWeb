from flask import Blueprint, request, jsonify
from database.db import get_db_connection

dreams_bp = Blueprint('dreams', __name__)


@dreams_bp.route('/api/dreams', methods=['POST'])
def create_dream():
    """Create a new dream entry"""
    data = request.json
    user_id = data.get('user_id')
    dname = data.get('dname')
    description = data.get('description')
    intensity = data.get('intensity')
    lucid = data.get('lucid', False)
    dream_date = data.get('dream_date')
    emotions = data.get('emotions', [])
    themes = data.get('themes', [])
    categories = data.get('categories', [])

    if not all([user_id, dname, description]):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()

    try:
        conn.start_transaction()

        cursor.execute(
            """INSERT INTO DREAM 
               (user_id, dname, description, intensity, lucid, dream_date) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (user_id, dname, description, intensity, lucid, dream_date)
        )
        dream_id = cursor.lastrowid

        for emotion_id in emotions:
            cursor.execute(
                "INSERT INTO DREAM_EMOTION (dream_id, emotion_id) VALUES (%s, %s)",
                (dream_id, emotion_id)
            )

        for theme_id in themes:
            cursor.execute(
                "INSERT INTO DREAM_THEME (dream_id, theme_id) VALUES (%s, %s)",
                (dream_id, theme_id)
            )

        for category_id in categories:
            cursor.execute(
                "INSERT INTO DREAM_CATEGORY (dream_id, category_id) VALUES (%s, %s)",
                (dream_id, category_id)
            )

        conn.commit()

        # Check and award achievements (game system)
        try:
            from routes.game import check_and_award_achievements
            check_and_award_achievements(user_id)
        except Exception as e:
            print(f"Achievement check error: {e}")

        return jsonify({
            "message": "Dream created successfully",
            "dream_id": dream_id
        }), 201

    except Exception as e:
        conn.rollback()
        print(f"Create dream error: {e}")
        return jsonify({"error": f"Failed to create dream: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


@dreams_bp.route('/api/dreams/user/<int:user_id>', methods=['GET'])
def get_user_dreams(user_id):
    """Get all dreams for a user"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """SELECT dream_id, dname, description, intensity, lucid, 
                      dream_date, created_at 
               FROM DREAM 
               WHERE user_id = %s 
               ORDER BY dream_date DESC""",
            (user_id,)
        )
        dreams = cursor.fetchall()

        return jsonify(dreams), 200

    except Exception as e:
        print(f"Get dreams error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@dreams_bp.route('/api/dreams/<int:dream_id>', methods=['DELETE'])
def delete_dream(dream_id):
    """Delete a dream"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM DREAM WHERE dream_id = %s", (dream_id,))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Dream not found"}), 404

        return jsonify({"message": "Dream deleted successfully"}), 200

    except Exception as e:
        conn.rollback()
        print(f"Delete dream error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@dreams_bp.route('/api/queries/dreams-by-emotion', methods=['GET'])
def get_dreams_by_emotion():
    """REQUIRED QUERY: Aggregate with GROUP BY"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """SELECT e.emotion_type, COUNT(de.dream_id) as dream_count,
                      AVG(d.intensity) as avg_intensity
               FROM EMOTION e
               LEFT JOIN DREAM_EMOTION de ON e.emotion_id = de.emotion_id
               LEFT JOIN DREAM d ON de.dream_id = d.dream_id
               GROUP BY e.emotion_id, e.emotion_type
               ORDER BY dream_count DESC"""
        )
        results = cursor.fetchall()

        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()