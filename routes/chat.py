import os
from flask import Blueprint, request, jsonify
from database.db import get_db_connection
from datetime import datetime
import requests

chat_bp = Blueprint('chat', __name__)

# ------------------ AI Provider Config ------------------
AI_PROVIDER = os.environ.get("AI_PROVIDER", "groq").lower().strip()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama3-8b-8192")

# Set to True to use mock responses (for testing without any API key)
USE_MOCK = False


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


def chat_with_groq(prompt):
    """Call Groq API using llama3."""
    if USE_MOCK:
        print("[MOCK] Using mock AI response")
        return f"This is a mock AI response analyzing your dream. Dream analysis based on: {prompt[:100]}..."

    if not GROQ_API_KEY:
        raise RuntimeError("Groq key is missing. Set GROQ_API_KEY in your .env file.")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024,
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip() or "[No response generated]"

    except requests.exceptions.Timeout:
        raise RuntimeError("Groq timeout. Please try again.")
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, "response") and e.response is not None else None
        response_text = e.response.text if hasattr(e, "response") and e.response is not None else "No response"
        print(f"Groq API Error ({status_code}): {response_text}")
        if status_code == 401:
            raise RuntimeError("Groq key is invalid. Check your .env file.")
        if status_code == 429:
            raise RuntimeError("Groq rate limit exceeded. Try again in a moment.")
        raise RuntimeError("Groq service is unavailable right now.")
    except Exception as e:
        print(f"Unexpected Groq error: {e}")
        raise RuntimeError("An unexpected AI error occurred.")


def chat_with_openai(prompt):
    """Call OpenAI API."""
    if USE_MOCK:
        return f"This is a mock AI response analyzing your dream. Dream analysis based on: {prompt[:100]}..."

    if not OPENAI_API_KEY:
        raise RuntimeError("OpenAI key is missing. Set OPENAI_API_KEY in your .env file.")

    url = "https://api.openai.com/v1/responses"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": OPENAI_MODEL,
        "input": [{"role": "user", "content": prompt}],
        "store": True
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()

        output_text = ""
        if "output" in result:
            for item in result["output"]:
                if "content" in item:
                    for c in item["content"]:
                        if c.get("type") == "output_text" and "text" in c:
                            output_text += c["text"]

        return output_text.strip() or "[No response generated]"

    except requests.exceptions.Timeout:
        raise RuntimeError("OpenAI timeout. Please try again.")
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, "response") and e.response is not None else None
        if status_code == 401:
            raise RuntimeError("OpenAI key is invalid or expired. Check your .env file.")
        if status_code == 429:
            raise RuntimeError("OpenAI rate limit or quota exceeded.")
        raise RuntimeError("OpenAI service is unavailable right now.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise RuntimeError("An unexpected AI error occurred.")


def chat_with_gemini(prompt):
    """Call Google Gemini API."""
    if USE_MOCK:
        return f"This is a mock AI response analyzing your dream. Dream analysis based on: {prompt[:100]}..."

    if not GEMINI_API_KEY:
        raise RuntimeError("Gemini key is missing. Set GEMINI_API_KEY in your .env file.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()

        candidates = result.get("candidates", [])
        if not candidates:
            return "[No response generated]"

        parts = candidates[0].get("content", {}).get("parts", [])
        output_text = "".join(part.get("text", "") for part in parts)
        return output_text.strip() or "[No response generated]"

    except requests.exceptions.Timeout:
        raise RuntimeError("Gemini timeout. Please try again.")
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, "response") and e.response is not None else None
        if status_code in (401, 403):
            raise RuntimeError("Gemini key is invalid or unauthorized. Check your .env file.")
        if status_code == 429:
            raise RuntimeError("Gemini rate limit or quota exceeded.")
        raise RuntimeError("Gemini service is unavailable right now.")
    except Exception as e:
        print(f"Unexpected Gemini error: {e}")
        raise RuntimeError("An unexpected AI error occurred.")


def analyze_dream_with_ai(dream_text):
    """Enhanced dream analysis prompt for configured AI provider."""
    prompt = f"""You are an expert dream analyst and psychologist. Analyze the following dream:

"{dream_text}"

Please provide:
1. **Interpretation**: What this dream might symbolize
2. **Emotions**: The underlying emotions and feelings
3. **Themes**: Key themes and symbols present
4. **Insights**: Psychological or personal insights
5. **Recommendations**: Suggestions for the dreamer

Keep your response conversational, insightful, and supportive."""

    if AI_PROVIDER == "gemini":
        return chat_with_gemini(prompt)
    elif AI_PROVIDER == "openai":
        return chat_with_openai(prompt)
    else:
        return chat_with_groq(prompt)


@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    """General chatbot endpoint - Premium feature"""
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message')

    if not user_id or not message:
        return jsonify({"error": "Missing user_id or message"}), 400

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
        print(f"[CHAT] User {user_id}: {message[:50]}...")
        try:
            reply = analyze_dream_with_ai(message)
        except RuntimeError as ai_error:
            return jsonify({"error": str(ai_error), "ai_unavailable": True}), 503
        print(f"[CHAT] Bot replied: {reply[:50]}...")

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
    """Analyze a specific dream - Premium feature"""
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

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

        lucid_text = "This was a lucid dream. " if dream['lucid'] else ""
        analysis_prompt = f"{lucid_text}I dreamed about: {dream['dname']}. {dream['description'][:200]}"

        print(f"[ANALYZE] Analyzing dream {dream_id} for user {user_id}...")
        try:
            interpretation = analyze_dream_with_ai(analysis_prompt)
        except RuntimeError as ai_error:
            return jsonify({"error": str(ai_error), "ai_unavailable": True}), 503
        print(f"[ANALYZE] Analysis complete: {interpretation[:50]}...")

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
    """Get all analyses for a specific dream"""
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
    """Delete a specific dream analysis"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """SELECT analysis_id FROM DREAM_ANALYSIS 
               WHERE analysis_id = %s""",
            (analysis_id,)
        )
        analysis = cursor.fetchone()

        if not analysis:
            return jsonify({"error": "Analysis not found"}), 404

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
    """Get user's general chat history"""
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