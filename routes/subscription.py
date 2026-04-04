from flask import Blueprint, request, jsonify
from database.db import get_db_connection
from datetime import datetime, timedelta

subscription_bp = Blueprint('subscription', __name__)


@subscription_bp.route('/api/subscribe', methods=['POST'])
def subscribe():
    """TRANSACTION #2: Process payment and activate subscription"""
    data = request.json
    user_id = data.get('user_id')
    plan_type = data.get('plan_type')
    payment_method = data.get('payment_method')
    amount = data.get('amount')

    if not all([user_id, plan_type, payment_method, amount]):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        # START TRANSACTION
        conn.start_transaction()

        start_date = datetime.now().date()
        if plan_type == 'MONTHLY':
            end_date = start_date + timedelta(days=30)
        elif plan_type == 'YEARLY':
            end_date = start_date + timedelta(days=365)
        else:
            conn.rollback()
            return jsonify({"error": "Invalid plan type"}), 400

        cursor.execute(
            """SELECT subscription_id, status 
               FROM SUBSCRIPTION 
               WHERE user_id = %s AND status = 'ACTIVE'""",
            (user_id,)
        )
        existing_sub = cursor.fetchone()

        if existing_sub:
            subscription_id = existing_sub['subscription_id']
            cursor.execute(
                """UPDATE SUBSCRIPTION 
                   SET plan_type = %s, start_date = %s, end_date = %s, 
                       status = 'ACTIVE', auto_renew = TRUE
                   WHERE subscription_id = %s""",
                (plan_type, start_date, end_date, subscription_id)
            )
        else:
            cursor.execute(
                """INSERT INTO SUBSCRIPTION 
                   (user_id, start_date, end_date, plan_type, status, auto_renew) 
                   VALUES (%s, %s, %s, %s, 'ACTIVE', TRUE)""",
                (user_id, start_date, end_date, plan_type)
            )
            subscription_id = cursor.lastrowid

        cursor.execute(
            """INSERT INTO PAYMENT 
               (subscription_id, amount, payment_method, status) 
               VALUES (%s, %s, %s, 'COMPLETED')""",
            (subscription_id, amount, payment_method)
        )
        payment_id = cursor.lastrowid

        # COMMIT TRANSACTION
        conn.commit()

        return jsonify({
            "message": "Subscription activated successfully",
            "subscription_id": subscription_id,
            "payment_id": payment_id,
            "plan_type": plan_type,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }), 200

    except Exception as e:
        conn.rollback()
        print(f"Subscription error: {e}")
        return jsonify({"error": f"Subscription failed: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


@subscription_bp.route('/api/subscription/<int:user_id>', methods=['GET'])
def get_subscription_status(user_id):
    """Get user's current subscription status"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """SELECT s.*, 
                      CASE 
                          WHEN s.end_date < CURDATE() THEN 'EXPIRED'
                          ELSE s.status 
                      END as actual_status
               FROM SUBSCRIPTION s
               WHERE s.user_id = %s
               ORDER BY s.start_date DESC
               LIMIT 1""",
            (user_id,)
        )
        subscription = cursor.fetchone()

        if not subscription:
            return jsonify({
                "has_subscription": False,
                "message": "No subscription found"
            }), 200

        is_active = (subscription['actual_status'] == 'ACTIVE' and
                     subscription['end_date'] >= datetime.now().date())

        return jsonify({
            "has_subscription": True,
            "is_active": is_active,
            "subscription": subscription
        }), 200

    except Exception as e:
        print(f"Get subscription error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@subscription_bp.route('/api/cancel-subscription', methods=['POST'])
def cancel_subscription():
    """Cancel auto-renewal for subscription (keeps access until end date)"""
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        # Get active subscription
        cursor.execute(
            """SELECT subscription_id, end_date, auto_renew 
               FROM SUBSCRIPTION 
               WHERE user_id = %s AND status = 'ACTIVE'
               ORDER BY start_date DESC
               LIMIT 1""",
            (user_id,)
        )
        subscription = cursor.fetchone()

        if not subscription:
            return jsonify({"error": "No active subscription found"}), 404

        if not subscription['auto_renew']:
            return jsonify({"message": "Auto-renewal is already disabled"}), 200

        # Update auto_renew to FALSE
        cursor.execute(
            """UPDATE SUBSCRIPTION 
               SET auto_renew = FALSE 
               WHERE subscription_id = %s""",
            (subscription['subscription_id'],)
        )
        conn.commit()

        return jsonify({
            "message": "Auto-renewal cancelled successfully",
            "end_date": subscription['end_date'].isoformat(),
            "note": "You will keep access until the end date"
        }), 200

    except Exception as e:
        conn.rollback()
        print(f"Cancel subscription error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@subscription_bp.route('/api/reactivate-subscription', methods=['POST'])
def reactivate_subscription():
    """Re-enable auto-renewal for subscription"""
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        # Get active subscription
        cursor.execute(
            """SELECT subscription_id, auto_renew 
               FROM SUBSCRIPTION 
               WHERE user_id = %s AND status = 'ACTIVE'
               ORDER BY start_date DESC
               LIMIT 1""",
            (user_id,)
        )
        subscription = cursor.fetchone()

        if not subscription:
            return jsonify({"error": "No active subscription found"}), 404

        if subscription['auto_renew']:
            return jsonify({"message": "Auto-renewal is already enabled"}), 200

        # Update auto_renew to TRUE
        cursor.execute(
            """UPDATE SUBSCRIPTION 
               SET auto_renew = TRUE 
               WHERE subscription_id = %s""",
            (subscription['subscription_id'],)
        )
        conn.commit()

        return jsonify({
            "message": "Auto-renewal reactivated successfully"
        }), 200

    except Exception as e:
        conn.rollback()
        print(f"Reactivate subscription error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()