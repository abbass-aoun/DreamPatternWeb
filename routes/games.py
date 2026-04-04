from flask import Blueprint, request, jsonify
from database.db import get_db_connection
from datetime import datetime
import json

games_bp = Blueprint('games', __name__)


# ========================================
# GAME LIST & INFO
# ========================================

@games_bp.route('/api/games', methods=['GET'])
def get_games():
    """Get list of all available games"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT * FROM GAME WHERE is_active = TRUE ORDER BY game_name"""
        )
        games = cursor.fetchall()
        return jsonify({"games": games}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ========================================
# SUBMIT GAME SCORE
# ========================================

@games_bp.route('/api/games/submit-score', methods=['POST'])
def submit_score():
    """Submit a game score"""
    data = request.json
    user_id = data.get('user_id')
    game_name = data.get('game_name')
    score = data.get('score', 0)
    level = data.get('level', 1)
    time_played = data.get('time_played', 0)
    metadata = data.get('metadata', {})

    if not user_id or not game_name:
        return jsonify({"error": "Missing user_id or game_name"}), 400

    if score < 0:
        return jsonify({"error": "Invalid score"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        # Get game_id
        cursor.execute("SELECT game_id FROM GAME WHERE game_name = %s AND is_active = TRUE", (game_name,))
        game = cursor.fetchone()
        
        if not game:
            return jsonify({"error": "Game not found"}), 404

        game_id = game['game_id']

        # Insert score
        metadata_json = json.dumps(metadata) if metadata else None
        cursor.execute(
            """INSERT INTO GAME_SCORE 
               (user_id, game_id, score, level, time_played, metadata)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (user_id, game_id, score, level, time_played, metadata_json)
        )
        score_id = cursor.lastrowid

        # Get user's rank for this game
        cursor.execute(
            """SELECT COUNT(*) + 1 as rank
               FROM GAME_SCORE
               WHERE game_id = %s AND (score > %s OR (score = %s AND created_at < (SELECT created_at FROM GAME_SCORE WHERE score_id = %s)))""",
            (game_id, score, score, score_id)
        )
        rank_result = cursor.fetchone()
        rank = rank_result['rank'] if rank_result else 1

        # Check if this is a personal best
        cursor.execute(
            """SELECT MAX(score) as best_score
               FROM GAME_SCORE
               WHERE user_id = %s AND game_id = %s AND score_id != %s""",
            (user_id, game_id, score_id)
        )
        best_result = cursor.fetchone()
        is_personal_best = not best_result or not best_result['best_score'] or score > best_result['best_score']

        # Award XP and coins based on score and game
        xp_reward = calculate_xp_reward(game_name, score, level)
        coins_reward = max(1, xp_reward // 10)

        if xp_reward > 0:
            # Record XP transaction
            cursor.execute(
                """INSERT INTO XP_TRANSACTION 
                   (user_id, xp_amount, transaction_type, description)
                   VALUES (%s, %s, 'BONUS', %s)""",
                (user_id, xp_reward, f"Game: {game_name} (Score: {score})")
            )

            # Record coin transaction
            cursor.execute(
                """INSERT INTO COIN_TRANSACTION 
                   (user_id, coin_amount, transaction_type, description)
                   VALUES (%s, %s, 'EARNED', %s)""",
                (user_id, coins_reward, f"Game reward: {game_name}")
            )

            # Update user stats
            cursor.execute(
                """INSERT INTO USER_GAME_STATS (user_id, total_xp, dream_coins, total_coins_earned)
                   VALUES (%s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE
                       total_xp = total_xp + %s,
                       dream_coins = dream_coins + %s,
                       total_coins_earned = total_coins_earned + %s""",
                (user_id, xp_reward, coins_reward, coins_reward, xp_reward, coins_reward, coins_reward)
            )

            # Check for level up
            cursor.execute("SELECT total_xp FROM USER_GAME_STATS WHERE user_id = %s", (user_id,))
            current_xp = cursor.fetchone()['total_xp']
            new_level = (current_xp // 100) + 1

            cursor.execute(
                "UPDATE USER_GAME_STATS SET current_level = %s WHERE user_id = %s",
                (new_level, user_id)
            )

        conn.commit()

        return jsonify({
            "message": f"Score submitted! Rank: #{rank}",
            "score_id": score_id,
            "rank": rank,
            "is_personal_best": is_personal_best,
            "xp_earned": xp_reward,
            "coins_earned": coins_reward
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


def calculate_xp_reward(game_name, score, level):
    """Calculate XP reward based on game and score"""
    base_xp = 0
    level_bonus = 0
    
    if game_name == "Flappy Bird":
        # 1 XP per 50 points, max 75 XP
        base_xp = min(75, score // 50)
        # Level bonus: 5 XP per level
        level_bonus = (level - 1) * 5
    elif game_name == "Super Mario":
        # 1 XP per 10 points, max 100 XP
        base_xp = min(100, score // 10)
        # Level bonus: 10 XP per level (level 1 = 0 bonus, level 2 = 10, etc.)
        level_bonus = (level - 1) * 10
        # Cap total at 150 XP
        total_xp = base_xp + level_bonus
        return max(3, min(150, total_xp))
    
    total_xp = base_xp + level_bonus
    
    # Minimum 3 XP
    return max(3, total_xp)


# ========================================
# LEADERBOARD APIs
# ========================================

@games_bp.route('/api/games/leaderboard/<game_name>', methods=['GET'])
def get_leaderboard(game_name):
    """Get leaderboard for a specific game - shows highest score per user"""
    limit = request.args.get('limit', 100, type=int)

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        # Get game_id
        cursor.execute("SELECT game_id FROM GAME WHERE game_name = %s AND is_active = TRUE", (game_name,))
        game = cursor.fetchone()

        if not game:
            return jsonify({"error": "Game not found"}), 404

        game_id = game['game_id']

        # Get best score per user - simpler and more reliable query
        cursor.execute(
            """SELECT 
                gs.score_id,
                gs.user_id,
                u.username,
                MAX(gs.score) as score,
                MAX(gs.level) as level,
                MAX(gs.time_played) as time_played,
                MAX(gs.created_at) as created_at
            FROM GAME_SCORE gs
            JOIN USER u ON gs.user_id = u.user_id
            WHERE gs.game_id = %s
            GROUP BY gs.user_id, u.username
            ORDER BY score DESC, created_at ASC
            LIMIT %s""",
            (game_id, limit)
        )
        leaderboard = cursor.fetchall()

        # Add rank to each entry
        for index, entry in enumerate(leaderboard):
            entry['rank'] = index + 1

        print(f"Leaderboard for {game_name}: {len(leaderboard)} entries")
        for entry in leaderboard:
            print(f"  - {entry['username']}: {entry['score']} points")

        return jsonify({
            "game_name": game_name,
            "leaderboard": leaderboard,
            "total_players": len(leaderboard)
        }), 200

    except Exception as e:
        print(f"Leaderboard error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@games_bp.route('/api/games/user-scores/<int:user_id>', methods=['GET'])
def get_user_scores(user_id):
    """Get user's best scores for all games"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT 
                g.game_name,
                g.game_icon,
                MAX(gs.score) as best_score,
                MAX(gs.level) as best_level,
                COUNT(gs.score_id) as total_plays,
                MAX(gs.created_at) as last_played
            FROM GAME g
            LEFT JOIN GAME_SCORE gs ON g.game_id = gs.game_id AND gs.user_id = %s
            WHERE g.is_active = TRUE
            GROUP BY g.game_id, g.game_name, g.game_icon
            ORDER BY g.game_name""",
            (user_id,)
        )
        scores = cursor.fetchall()

        return jsonify({"scores": scores}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@games_bp.route('/api/games/user-rank/<int:user_id>/<game_name>', methods=['GET'])
def get_user_rank(user_id, game_name):
    """Get user's rank and best score for a specific game"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        # Get game_id
        cursor.execute("SELECT game_id FROM GAME WHERE game_name = %s AND is_active = TRUE", (game_name,))
        game = cursor.fetchone()
        
        if not game:
            return jsonify({"error": "Game not found"}), 404

        game_id = game['game_id']

        # Get user's best score
        cursor.execute(
            """SELECT MAX(score) as best_score, MAX(level) as best_level, COUNT(*) as total_plays
               FROM GAME_SCORE
               WHERE user_id = %s AND game_id = %s""",
            (user_id, game_id)
        )
        user_stats = cursor.fetchone()

        if not user_stats or not user_stats['best_score']:
            return jsonify({
                "has_played": False,
                "rank": None,
                "best_score": 0,
                "best_level": 0,
                "total_plays": 0
            }), 200

        # Get user's rank
        cursor.execute(
            """SELECT COUNT(*) + 1 as rank
               FROM GAME_SCORE
               WHERE game_id = %s AND (score > %s OR (score = %s AND created_at < (
                   SELECT MIN(created_at) FROM GAME_SCORE 
                   WHERE user_id = %s AND game_id = %s AND score = %s
               )))""",
            (game_id, user_stats['best_score'], user_stats['best_score'], user_id, game_id, user_stats['best_score'])
        )
        rank_result = cursor.fetchone()

        return jsonify({
            "has_played": True,
            "rank": rank_result['rank'] if rank_result else 1,
            "best_score": user_stats['best_score'],
            "best_level": user_stats['best_level'],
            "total_plays": user_stats['total_plays']
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

