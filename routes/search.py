from flask import Blueprint, request, jsonify
from database.db import get_db_connection

search_bp = Blueprint('search', __name__)


@search_bp.route('/api/search/dreams/<int:user_id>', methods=['GET'])
def search_dreams(user_id):
    """Search dreams with filters"""
    query = request.args.get('q', '')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    lucid = request.args.get('lucid')
    min_intensity = request.args.get('min_intensity')
    max_intensity = request.args.get('max_intensity')
    emotion_id = request.args.get('emotion_id')
    theme_id = request.args.get('theme_id')
    category_id = request.args.get('category_id')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        # Build query dynamically
        sql = """SELECT DISTINCT d.* 
                 FROM DREAM d"""
        conditions = ["d.user_id = %s"]
        params = [user_id]
        joins = []
        
        # Text search
        if query:
            conditions.append("(d.dname LIKE %s OR d.description LIKE %s)")
            search_term = f"%{query}%"
            params.extend([search_term, search_term])
        
        # Date range
        if start_date:
            conditions.append("d.dream_date >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("d.dream_date <= %s")
            params.append(end_date)
        
        # Lucid filter
        if lucid is not None:
            conditions.append("d.lucid = %s")
            params.append(lucid.lower() == 'true')
        
        # Intensity range
        if min_intensity:
            conditions.append("d.intensity >= %s")
            params.append(int(min_intensity))
        if max_intensity:
            conditions.append("d.intensity <= %s")
            params.append(int(max_intensity))
        
        # Emotion filter
        if emotion_id:
            joins.append("INNER JOIN DREAM_EMOTION de ON d.dream_id = de.dream_id")
            conditions.append("de.emotion_id = %s")
            params.append(int(emotion_id))
        
        # Theme filter
        if theme_id:
            joins.append("INNER JOIN DREAM_THEME dt ON d.dream_id = dt.dream_id")
            conditions.append("dt.theme_id = %s")
            params.append(int(theme_id))
        
        # Category filter
        if category_id:
            joins.append("INNER JOIN DREAM_CATEGORY dc ON d.dream_id = dc.dream_id")
            conditions.append("dc.category_id = %s")
            params.append(int(category_id))
        
        if joins:
            sql += " " + " ".join(joins)
        
        sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY d.dream_date DESC LIMIT 100"
        
        cursor.execute(sql, params)
        dreams = cursor.fetchall()
        
        return jsonify({
            "dreams": dreams,
            "count": len(dreams)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@search_bp.route('/api/search/calendar/<int:user_id>', methods=['GET'])
def get_calendar_dreams(user_id):
    """Get dreams for calendar view by month"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    if not year or not month:
        return jsonify({"error": "Year and month required"}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT dream_id, dname, dream_date, lucid, intensity, 
                      (SELECT GROUP_CONCAT(e.emotion_type) 
                       FROM DREAM_EMOTION de 
                       INNER JOIN EMOTION e ON de.emotion_id = e.emotion_id 
                       WHERE de.dream_id = d.dream_id) as emotions
               FROM DREAM d
               WHERE user_id = %s 
               AND YEAR(dream_date) = %s 
               AND MONTH(dream_date) = %s
               ORDER BY dream_date ASC""",
            (user_id, year, month)
        )
        dreams = cursor.fetchall()
        
        # Group by date
        calendar_data = {}
        for dream in dreams:
            date_str = dream['dream_date'].strftime('%Y-%m-%d') if hasattr(dream['dream_date'], 'strftime') else str(dream['dream_date'])
            if date_str not in calendar_data:
                calendar_data[date_str] = []
            calendar_data[date_str].append({
                'dream_id': dream['dream_id'],
                'dname': dream['dname'],
                'lucid': dream['lucid'],
                'intensity': dream['intensity'],
                'emotions': dream['emotions']
            })
        
        return jsonify(calendar_data), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@search_bp.route('/api/search/stats/<int:user_id>', methods=['GET'])
def get_search_stats(user_id):
    """Get statistics for search/filter options"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        # Get date range
        cursor.execute(
            "SELECT MIN(dream_date) as min_date, MAX(dream_date) as max_date FROM DREAM WHERE user_id = %s",
            (user_id,)
        )
        date_range = cursor.fetchone()
        
        # Get intensity range
        cursor.execute(
            "SELECT MIN(intensity) as min_intensity, MAX(intensity) as max_intensity FROM DREAM WHERE user_id = %s",
            (user_id,)
        )
        intensity_range = cursor.fetchone()
        
        return jsonify({
            "date_range": date_range,
            "intensity_range": intensity_range
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

