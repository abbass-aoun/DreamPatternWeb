from flask import Blueprint, request, jsonify
from database.db import get_db_connection
from datetime import datetime, date, time

game_bp = Blueprint('game', __name__)


# ========================================
# GAME STATS & XP SYSTEM
# ========================================

@game_bp.route('/api/game/stats/<int:user_id>', methods=['GET'])
def get_game_stats(user_id):
    """Get user's game statistics (XP, level, coins)"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        # Get game stats
        cursor.execute(
            """SELECT * FROM USER_GAME_STATS WHERE user_id = %s""",
            (user_id,)
        )
        stats = cursor.fetchone()

        if not stats:
            # Initialize stats
            cursor.execute(
                """INSERT INTO USER_GAME_STATS (user_id, total_xp, current_level, dream_coins) 
                   VALUES (%s, 0, 1, 0)""",
                (user_id,)
            )
            conn.commit()
            stats = {
                'total_xp': 0,
                'current_level': 1,
                'dream_coins': 0,
                'total_coins_earned': 0
            }

        # Get streak
        cursor.execute(
            """SELECT current_streak, longest_streak FROM DREAM_STREAK WHERE user_id = %s""",
            (user_id,)
        )
        streak = cursor.fetchone()
        if not streak:
            streak = {'current_streak': 0, 'longest_streak': 0}

        # Calculate XP needed for next level
        xp_for_current_level = (stats['current_level'] - 1) * 100
        xp_for_next_level = stats['current_level'] * 100
        xp_progress = stats['total_xp'] - xp_for_current_level
        xp_needed = xp_for_next_level - stats['total_xp']
        progress_percentage = (xp_progress / 100) * 100 if xp_for_next_level > xp_for_current_level else 100

        return jsonify({
            "total_xp": stats['total_xp'],
            "current_level": stats['current_level'],
            "dream_coins": stats['dream_coins'],
            "total_coins_earned": stats.get('total_coins_earned', 0),
            "current_streak": streak['current_streak'],
            "longest_streak": streak['longest_streak'],
            "xp_progress": xp_progress,
            "xp_needed": max(0, xp_needed),
            "progress_percentage": round(progress_percentage, 1)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@game_bp.route('/api/game/xp-history/<int:user_id>', methods=['GET'])
def get_xp_history(user_id):
    """Get XP transaction history"""
    limit = request.args.get('limit', 20, type=int)
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT * FROM XP_TRANSACTION 
               WHERE user_id = %s 
               ORDER BY created_at DESC 
               LIMIT %s""",
            (user_id, limit)
        )
        transactions = cursor.fetchall()

        return jsonify({
            "transactions": transactions,
            "total": len(transactions)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ========================================
# ACHIEVEMENT SYSTEM
# ========================================

@game_bp.route('/api/game/achievements/<int:user_id>', methods=['GET'])
def get_user_achievements(user_id):
    """Get all achievements with user progress"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        # Get all achievements
        cursor.execute("SELECT * FROM ACHIEVEMENT ORDER BY achievement_id")
        all_achievements = cursor.fetchall()

        # Get user's earned achievements
        cursor.execute(
            """SELECT achievement_id FROM USER_ACHIEVEMENT WHERE user_id = %s""",
            (user_id,)
        )
        earned_ids = {row['achievement_id'] for row in cursor.fetchall()}

        # Get user stats for progress calculation
        cursor.execute("SELECT COUNT(*) as dream_count FROM DREAM WHERE user_id = %s", (user_id,))
        dream_count = cursor.fetchone()['dream_count']
        
        cursor.execute("SELECT COUNT(*) as lucid_count FROM DREAM WHERE user_id = %s AND lucid = TRUE", (user_id,))
        lucid_count = cursor.fetchone()['lucid_count']

        cursor.execute("SELECT MAX(intensity) as max_intensity FROM DREAM WHERE user_id = %s", (user_id,))
        max_intensity = cursor.fetchone()['max_intensity'] or 0

        cursor.execute("SELECT current_streak FROM DREAM_STREAK WHERE user_id = %s", (user_id,))
        streak_data = cursor.fetchone()
        current_streak = streak_data['current_streak'] if streak_data else 0

        # Check for early bird (dreams recorded before 7 AM)
        cursor.execute(
            """SELECT COUNT(*) as early_count 
               FROM DREAM 
               WHERE user_id = %s 
               AND HOUR(created_at) < 7""",
            (user_id,)
        )
        early_bird_count = cursor.fetchone()['early_count']

        # Calculate progress for each achievement
        for achievement in all_achievements:
            achievement['earned'] = achievement['achievement_id'] in earned_ids
            progress = 0
            
            if achievement['requirement_type'] == 'DREAM_COUNT':
                progress = min(100, (dream_count / achievement['requirement_value']) * 100)
            elif achievement['requirement_type'] == 'LUCID_COUNT':
                progress = min(100, (lucid_count / achievement['requirement_value']) * 100)
            elif achievement['requirement_type'] == 'STREAK':
                progress = min(100, (current_streak / achievement['requirement_value']) * 100)
            elif achievement['requirement_type'] == 'INTENSITY':
                progress = 100 if max_intensity >= achievement['requirement_value'] else 0
            elif achievement['requirement_type'] == 'TIME':
                progress = 100 if early_bird_count >= achievement['requirement_value'] else 0
            
            achievement['progress'] = round(progress, 1)

        return jsonify({
            "achievements": all_achievements,
            "total_earned": sum(1 for a in all_achievements if a['earned'])
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


def check_and_award_achievements(user_id):
    """Check and award achievements based on user progress"""
    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor(dictionary=True)
    try:
        # Get user stats
        cursor.execute("SELECT COUNT(*) as dream_count FROM DREAM WHERE user_id = %s", (user_id,))
        dream_count = cursor.fetchone()['dream_count']
        
        cursor.execute("SELECT COUNT(*) as lucid_count FROM DREAM WHERE user_id = %s AND lucid = TRUE", (user_id,))
        lucid_count = cursor.fetchone()['lucid_count']

        cursor.execute("SELECT MAX(intensity) as max_intensity FROM DREAM WHERE user_id = %s", (user_id,))
        max_intensity = cursor.fetchone()['max_intensity'] or 0

        cursor.execute("SELECT current_streak FROM DREAM_STREAK WHERE user_id = %s", (user_id,))
        streak_data = cursor.fetchone()
        current_streak = streak_data['current_streak'] if streak_data else 0

        # Check for early bird (dreams recorded before 7 AM)
        cursor.execute(
            """SELECT COUNT(*) as early_count 
               FROM DREAM 
               WHERE user_id = %s 
               AND HOUR(created_at) < 7""",
            (user_id,)
        )
        early_bird_count = cursor.fetchone()['early_count']

        # Get all achievements
        cursor.execute("SELECT * FROM ACHIEVEMENT")
        all_achievements = cursor.fetchall()

        # Get already earned achievements
        cursor.execute(
            "SELECT achievement_id FROM USER_ACHIEVEMENT WHERE user_id = %s",
            (user_id,)
        )
        earned_ids = {row['achievement_id'] for row in cursor.fetchall()}

        # Check each achievement
        for achievement in all_achievements:
            if achievement['achievement_id'] in earned_ids:
                continue

            should_award = False
            if achievement['requirement_type'] == 'DREAM_COUNT' and dream_count >= achievement['requirement_value']:
                should_award = True
            elif achievement['requirement_type'] == 'LUCID_COUNT' and lucid_count >= achievement['requirement_value']:
                should_award = True
            elif achievement['requirement_type'] == 'STREAK' and current_streak >= achievement['requirement_value']:
                should_award = True
            elif achievement['requirement_type'] == 'INTENSITY' and max_intensity >= achievement['requirement_value']:
                should_award = True
            elif achievement['requirement_type'] == 'TIME' and early_bird_count >= achievement['requirement_value']:
                should_award = True

            if should_award:
                # Award achievement
                cursor.execute(
                    """INSERT INTO USER_ACHIEVEMENT (user_id, achievement_id) 
                       VALUES (%s, %s)""",
                    (user_id, achievement['achievement_id'])
                )

                # Award XP and coins
                if achievement['xp_reward'] > 0:
                    cursor.execute(
                        """INSERT INTO XP_TRANSACTION 
                           (user_id, xp_amount, transaction_type, source_id, description)
                           VALUES (%s, %s, 'ACHIEVEMENT', %s, %s)""",
                        (user_id, achievement['xp_reward'], achievement['achievement_id'], 
                         f"Achievement: {achievement['achievement_name']}")
                    )

                if achievement['coin_reward'] > 0:
                    cursor.execute(
                        """INSERT INTO COIN_TRANSACTION 
                           (user_id, coin_amount, transaction_type, source_id, description)
                           VALUES (%s, %s, 'EARNED', %s, %s)""",
                        (user_id, achievement['coin_reward'], achievement['achievement_id'],
                         f"Achievement reward: {achievement['achievement_name']}")
                    )

                    # Update user stats
                    cursor.execute(
                        """UPDATE USER_GAME_STATS 
                           SET total_xp = total_xp + %s,
                               dream_coins = dream_coins + %s,
                               total_coins_earned = total_coins_earned + %s
                           WHERE user_id = %s""",
                        (achievement['xp_reward'], achievement['coin_reward'], 
                         achievement['coin_reward'], user_id)
                    )

                conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Achievement check error: {e}")
    finally:
        cursor.close()
        conn.close()


# ========================================
# REALITY CHECK SYSTEM
# ========================================

@game_bp.route('/api/game/reality-check', methods=['POST'])
def record_reality_check():
    """Record a reality check and award XP (once per 24 hours)"""
    data = request.json
    user_id = data.get('user_id')
    notes = data.get('notes', '')

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        # Check if user already did a reality check in the last 24 hours
        cursor.execute(
            """SELECT check_id, check_date 
               FROM REALITY_CHECK 
               WHERE user_id = %s 
               AND check_date >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
               ORDER BY check_date DESC 
               LIMIT 1""",
            (user_id,)
        )
        recent_check = cursor.fetchone()
        
        if recent_check:
            hours_remaining = 24 - (TIMESTAMPDIFF(HOUR, recent_check['check_date'], NOW()))
            return jsonify({
                "error": f"Reality check already completed! Next check available in {hours_remaining} hours.",
                "cooldown_remaining": hours_remaining
            }), 429

        # Record reality check
        cursor.execute(
            """INSERT INTO REALITY_CHECK (user_id, notes) 
               VALUES (%s, %s)""",
            (user_id, notes)
        )
        check_id = cursor.lastrowid

        # Award XP (5 XP per reality check)
        xp_amount = 5
        coins_amount = 1  # 1 coin per 5 XP

        cursor.execute(
            """INSERT INTO XP_TRANSACTION 
               (user_id, xp_amount, transaction_type, source_id, description)
               VALUES (%s, %s, 'REALITY_CHECK', %s, 'Reality check completed')""",
            (user_id, xp_amount, check_id)
        )

        cursor.execute(
            """INSERT INTO COIN_TRANSACTION 
               (user_id, coin_amount, transaction_type, source_id, description)
               VALUES (%s, %s, 'EARNED', %s, 'Reality check reward')""",
            (user_id, coins_amount, check_id)
        )

        # Update user stats
        cursor.execute(
            """INSERT INTO USER_GAME_STATS (user_id, total_xp, dream_coins, total_coins_earned)
               VALUES (%s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE
                   total_xp = total_xp + %s,
                   dream_coins = dream_coins + %s,
                   total_coins_earned = total_coins_earned + %s""",
            (user_id, xp_amount, coins_amount, coins_amount, xp_amount, coins_amount, coins_amount)
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

        # Check achievements
        check_and_award_achievements(user_id)

        return jsonify({
            "message": "Reality check recorded! +5 XP, +1 Coin",
            "check_id": check_id,
            "xp_earned": xp_amount,
            "coins_earned": coins_amount
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@game_bp.route('/api/game/reality-checks/<int:user_id>', methods=['GET'])
def get_reality_checks(user_id):
    """Get user's reality check history"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT * FROM REALITY_CHECK 
               WHERE user_id = %s 
               ORDER BY check_date DESC 
               LIMIT 50""",
            (user_id,)
        )
        checks = cursor.fetchall()

        return jsonify({
            "reality_checks": checks,
            "total": len(checks)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ========================================
# DREAM SHOP
# ========================================

@game_bp.route('/api/game/shop', methods=['GET'])
def get_shop_items():
    """Get all shop items"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT * FROM DREAM_SHOP 
               WHERE is_active = TRUE 
               ORDER BY coin_cost ASC"""
        )
        items = cursor.fetchall()

        return jsonify({"items": items}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@game_bp.route('/api/game/shop/purchase', methods=['POST'])
def purchase_shop_item():
    """Purchase an item from the shop"""
    data = request.json
    user_id = data.get('user_id')
    item_id = data.get('item_id')

    if not user_id or not item_id:
        return jsonify({"error": "Missing user_id or item_id"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()

        # Get item details
        cursor.execute(
            "SELECT * FROM DREAM_SHOP WHERE item_id = %s AND is_active = TRUE",
            (item_id,)
        )
        item = cursor.fetchone()

        if not item:
            conn.rollback()
            return jsonify({"error": "Item not found or not available"}), 404

        # Check if already purchased
        cursor.execute(
            "SELECT purchase_id FROM USER_SHOP_PURCHASE WHERE user_id = %s AND item_id = %s",
            (user_id, item_id)
        )
        if cursor.fetchone():
            conn.rollback()
            return jsonify({"error": "Item already purchased"}), 400

        # Check user has enough coins
        cursor.execute(
            "SELECT dream_coins FROM USER_GAME_STATS WHERE user_id = %s",
            (user_id,)
        )
        user_stats = cursor.fetchone()
        if not user_stats or user_stats['dream_coins'] < item['coin_cost']:
            conn.rollback()
            return jsonify({"error": "Insufficient coins"}), 400

        # Deduct coins
        cursor.execute(
            """UPDATE USER_GAME_STATS 
               SET dream_coins = dream_coins - %s 
               WHERE user_id = %s""",
            (item['coin_cost'], user_id)
        )

        # Record purchase
        cursor.execute(
            """INSERT INTO COIN_TRANSACTION 
               (user_id, coin_amount, transaction_type, source_id, description)
               VALUES (%s, %s, 'SPENT', %s, %s)""",
            (user_id, -item['coin_cost'], item_id, f"Purchased: {item['item_name']}")
        )

        # Record purchase
        cursor.execute(
            """INSERT INTO USER_SHOP_PURCHASE (user_id, item_id) 
               VALUES (%s, %s)""",
            (user_id, item_id)
        )

        conn.commit()

        return jsonify({
            "message": f"Successfully purchased {item['item_name']}!",
            "item": item,
            "remaining_coins": user_stats['dream_coins'] - item['coin_cost']
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@game_bp.route('/api/game/shop/purchases/<int:user_id>', methods=['GET'])
def get_user_purchases(user_id):
    """Get user's purchased items"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT s.*, p.purchased_at 
               FROM DREAM_SHOP s
               INNER JOIN USER_SHOP_PURCHASE p ON s.item_id = p.item_id
               WHERE p.user_id = %s
               ORDER BY p.purchased_at DESC""",
            (user_id,)
        )
        purchases = cursor.fetchall()

        return jsonify({"purchases": purchases}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ========================================
# CRITICAL HIT (CR) SYSTEM
# ========================================

@game_bp.route('/api/game/critical-check/<int:user_id>', methods=['POST'])
def critical_hit_check(user_id):
    """Perform critical hit check for enhanced rewards"""
    data = request.json
    base_reward = data.get('base_reward', 10)
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        # Get user's CR chance (base 10% + bonuses)
        cursor.execute(
            """SELECT cr_chance_bonus FROM USER_GAME_STATS WHERE user_id = %s""",
            (user_id,)
        )
        stats = cursor.fetchone()
        cr_chance = 0.10 + (stats.get('cr_chance_bonus', 0) if stats else 0)
        
        # Roll for critical hit
        import random
        is_critical = random.random() < cr_chance
        
        if is_critical:
            # Critical hit! 2x-3x reward
            multiplier = random.uniform(2.0, 3.0)
            final_reward = int(base_reward * multiplier)
            
            # Add CR bonus to user stats
            cursor.execute(
                """UPDATE USER_GAME_STATS 
                   SET cr_chance_bonus = LEAST(cr_chance_bonus + 0.01, 0.50)
                   WHERE user_id = %s""",
                (user_id,)
            )
            
            # Record CR transaction
            cursor.execute(
                """INSERT INTO XP_TRANSACTION 
                   (user_id, xp_amount, transaction_type, description) 
                   VALUES (%s, %s, 'CRITICAL_HIT', %s)""",
                (user_id, final_reward - base_reward, f'Critical Hit! {multiplier:.1f}x multiplier')
            )
            
            result = {
                "critical": True,
                "multiplier": round(multiplier, 2),
                "base_reward": base_reward,
                "bonus_reward": final_reward - base_reward,
                "total_reward": final_reward,
                "message": f"CRITICAL HIT! {multiplier:.1f}x reward!"
            }
        else:
            result = {
                "critical": False,
                "multiplier": 1.0,
                "base_reward": base_reward,
                "bonus_reward": 0,
                "total_reward": base_reward,
                "message": "Normal reward"
            }
        
        conn.commit()
        return jsonify(result), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@game_bp.route('/api/game/upgrade-cr/<int:user_id>', methods=['POST'])
def upgrade_cr_chance(user_id):
    """Upgrade critical hit chance using Dream Coins"""
    data = request.json
    upgrade_cost = data.get('cost', 100)
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        # Check user's coins
        cursor.execute(
            """SELECT dream_coins, cr_chance_bonus FROM USER_GAME_STATS WHERE user_id = %s""",
            (user_id,)
        )
        stats = cursor.fetchone()
        
        if not stats or stats['dream_coins'] < upgrade_cost:
            return jsonify({"error": "Insufficient Dream Coins"}), 400
        
        if stats['cr_chance_bonus'] >= 0.50:  # Max 50% CR chance
            return jsonify({"error": "Maximum CR chance reached"}), 400
        
        # Upgrade CR chance by 5%
        cursor.execute(
            """UPDATE USER_GAME_STATS 
               SET dream_coins = dream_coins - %s,
                   cr_chance_bonus = LEAST(cr_chance_bonus + 0.05, 0.50)
               WHERE user_id = %s""",
            (upgrade_cost, user_id)
        )
        
        # Record coin transaction
        cursor.execute(
            """INSERT INTO COIN_TRANSACTION 
               (user_id, coin_amount, transaction_type, description) 
               VALUES (%s, %s, 'UPGRADE', %s)""",
            (user_id, -upgrade_cost, f'CR Chance Upgrade (+5%)')
        )
        
        conn.commit()
        
        return jsonify({
            "message": "CR chance upgraded successfully!",
            "new_cr_chance": round(0.10 + stats['cr_chance_bonus'] + 0.05, 2),
            "cost": upgrade_cost
        }), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ========================================
# COIN TRANSACTION HISTORY
# ========================================

@game_bp.route('/api/game/coin-history/<int:user_id>', methods=['GET'])
def get_coin_history(user_id):
    """Get coin transaction history"""
    limit = request.args.get('limit', 20, type=int)
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT * FROM COIN_TRANSACTION 
               WHERE user_id = %s 
               ORDER BY created_at DESC 
               LIMIT %s""",
            (user_id, limit)
        )
        transactions = cursor.fetchall()

        return jsonify({
            "transactions": transactions,
            "total": len(transactions)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

