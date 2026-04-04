from flask import Blueprint, request, jsonify
from database.db import get_db_connection
from datetime import datetime
import requests

chat_bp = Blueprint('chat', __name__)

# ------------------ OpenAI Config ------------------
OPENAI_API_KEY = "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"
MODEL = "gpt-5-nano"

# Set to True to use mock responses (for testing without API)
USE_MOCK = False  # Change to True if API keeps timing out


def check_subscription_access(user_id):
    """Check if user has active premium subscription"""
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """SELECT subscription_id 
               FROM SUBSCRIPTION 
               WHERE user_id = %s 
                   AND status = 'ACTIVE' 
                   AND end_date >= CURDATE()
                   AND plan_type != 'FREE_TRIAL'""",
            (user_id,)
        )
        result = cursor.fetchone()
        return result is not None
    except:
        return False
    finally:
        cursor.close()
        conn.close()


def chat_with_openai(prompt):
    """Your OpenAI chatbot function"""

    # MOCK MODE - Use this if API keeps timing out (for testing)
    if USE_MOCK:
        print("[MOCK] Using mock AI response")
        return f"This is a mock AI response analyzing your dream. In production, this would be a real AI analysis from OpenAI. Dream analysis based on: {prompt[:100]}..."

    url = "https://api.openai.com/v1/responses"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "input": [{"role": "user", "content": prompt}],
        "store": True
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()

        # Extract response text
        output_text = ""
        if "output" in result:
            for item in result["output"]:
                if "content" in item:
                    for c in item["content"]:
                        if c.get("type") == "output_text" and "text" in c:
                            output_text += c["text"]

        return output_text.strip() or "[No response generated]"

    except requests.exceptions.Timeout:
        print("OpenAI API Timeout")
        return "The AI is taking longer than usual. The dream analysis has been saved, but the interpretation is taking time to generate. Please try again in a moment."
    except requests.exceptions.HTTPError as e:
        print(f"OpenAI API Error: {e}")
        print(f"Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
        return "AI service temporarily unavailable. Please try again later."
    except Exception as e:
        print(f"Unexpected error: {e}")
        return "An error occurred while generating the analysis. Please try again."


def analyze_dream_with_ai(dream_text):
    """Enhanced dream analysis prompt for OpenAI"""
    prompt = f"""You are an expert dream analyst and psychologist. Analyze the following dream:

"{dream_text}"

Please provide:
1. **Interpretation**: What this dream might symbolize
2. **Emotions**: The underlying emotions and feelings
3. **Themes**: Key themes and symbols present
4. **Insights**: Psychological or personal insights
5. **Recommendations**: Suggestions for the dreamer

Keep your response conversational, insightful, and supportive."""

    return chat_with_openai(prompt)


@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    """
    General chatbot endpoint - Premium feature with OpenAI
    Saves to CHAT_SESSION table for general conversations
    """
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message')

    if not user_id or not message:
        return jsonify({"error": "Missing user_id or message"}), 400

    # Check subscription
    if not check_subscription_access(user_id):
        return jsonify({
            "error": "Premium feature - Please subscribe to access AI dream analysis",
            "premium_required": True
        }), 403

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        # Get AI response from OpenAI
        print(f"[CHAT] User {user_id}: {message[:50]}...")
        reply = analyze_dream_with_ai(message)
        print(f"[CHAT] Bot replied: {reply[:50]}...")

        # Save general chat session (not linked to specific dream)
        cursor.execute(
            """INSERT INTO CHAT_SESSION (user_id, messages) 
               VALUES (%s, %s)""",
            (user_id, f"User: {message}\nBot: {reply}")
        )
        session_id = cursor.lastrowid

        conn.commit()

        return jsonify({
            "reply": reply,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }), 200

    except Exception as e:
        conn.rollback()
        print(f"Chat error: {e}")
        return jsonify({"error": f"Chat failed: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


@chat_bp.route('/api/analyze-dream/<int:dream_id>', methods=['POST'])
def analyze_specific_dream(dream_id):
    """
    Analyze a specific dream - Premium feature
    Saves to DREAM_ANALYSIS table linked to dream_id
    """
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    # Check subscription
    if not check_subscription_access(user_id):
        return jsonify({
            "error": "Premium feature - Please subscribe",
            "premium_required": True
        }), 403

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        # Get dream details
        cursor.execute(
            """SELECT d.*, 
                      GROUP_CONCAT(DISTINCT e.emotion_type) as emotions,
                      GROUP_CONCAT(DISTINCT t.theme_name) as themes
               FROM DREAM d
               LEFT JOIN DREAM_EMOTION de ON d.dream_id = de.dream_id
               LEFT JOIN EMOTION e ON de.emotion_id = e.emotion_id
               LEFT JOIN DREAM_THEME dt ON d.dream_id = dt.dream_id
               LEFT JOIN THEME t ON dt.theme_id = t.theme_id
               WHERE d.dream_id = %s AND d.user_id = %s
               GROUP BY d.dream_id""",
            (dream_id, user_id)
        )
        dream = cursor.fetchone()

        if not dream:
            return jsonify({"error": "Dream not found"}), 404

        # Create SIMPLIFIED analysis prompt (avoid timeout)
        lucid_text = "This was a lucid dream. " if dream['lucid'] else ""
        analysis_prompt = f"{lucid_text}I dreamed about: {dream['dname']}. {dream['description'][:200]}"

        # Get AI analysis
        print(f"[ANALYZE] Analyzing dream {dream_id} for user {user_id}...")
        print(f"[ANALYZE] Prompt length: {len(analysis_prompt)} chars")
        interpretation = analyze_dream_with_ai(analysis_prompt)
        print(f"[ANALYZE] Analysis complete: {interpretation[:50]}...")

        # Save analysis to DREAM_ANALYSIS table (linked to dream_id)
        cursor.execute(
            """INSERT INTO DREAM_ANALYSIS (dream_id, interpretation) 
               VALUES (%s, %s)""",
            (dream_id, interpretation)
        )
        analysis_id = cursor.lastrowid

        conn.commit()

        return jsonify({
            "analysis_id": analysis_id,
            "dream": dream,
            "interpretation": interpretation
        }), 200

    except Exception as e:
        conn.rollback()
        print(f"Analyze dream error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@chat_bp.route('/api/dream-analyses/<int:dream_id>', methods=['GET'])
def get_dream_analyses(dream_id):
    """
    Get all analyses for a specific dream
    Shows history of AI interpretations for this dream
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """SELECT * FROM DREAM_ANALYSIS 
               WHERE dream_id = %s 
               ORDER BY created_at DESC""",
            (dream_id,)
        )
        analyses = cursor.fetchall()

        return jsonify({
            "dream_id": dream_id,
            "total_analyses": len(analyses),
            "analyses": analyses
        }), 200

    except Exception as e:
        print(f"Get analyses error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@chat_bp.route('/api/dream-analyses/<int:analysis_id>', methods=['DELETE'])
def delete_dream_analysis(analysis_id):
    """
    Delete a specific dream analysis
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        # Check if analysis exists
        cursor.execute(
            """SELECT analysis_id FROM DREAM_ANALYSIS 
               WHERE analysis_id = %s""",
            (analysis_id,)
        )
        analysis = cursor.fetchone()

        if not analysis:
            return jsonify({"error": "Analysis not found"}), 404

        # Delete the analysis
        cursor.execute(
            """DELETE FROM DREAM_ANALYSIS 
               WHERE analysis_id = %s""",
            (analysis_id,)
        )

        conn.commit()

        return jsonify({
            "message": "Analysis deleted successfully",
            "analysis_id": analysis_id
        }), 200

    except Exception as e:
        conn.rollback()
        print(f"Delete analysis error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@chat_bp.route('/api/chat/history/<int:user_id>', methods=['GET'])
def get_chat_history(user_id):
    """Get user's general chat history (not dream-specific)"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """SELECT session_id, messages, session_date 
               FROM CHAT_SESSION 
               WHERE user_id = %s 
               ORDER BY session_date DESC 
               LIMIT 50""",
            (user_id,)
        )
        history = cursor.fetchall()

        return jsonify({
            "user_id": user_id,
            "total_sessions": len(history),
            "chat_history": history
        }), 200

    except Exception as e:
        print(f"Chat history error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()