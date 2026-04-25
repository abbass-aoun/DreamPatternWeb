from flask import Flask, jsonify, render_template
from flask_cors import CORS

# Import all route blueprints
from routes.auth import auth_bp
from routes.dreams import dreams_bp
from routes.chat import chat_bp
from routes.subscription import subscription_bp
from routes.stats import stats_bp
from routes.game import game_bp
from routes.search import search_bp
from routes.games import games_bp

app = Flask(__name__)
CORS(app)

# Register all blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dreams_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(subscription_bp)
app.register_blueprint(stats_bp)
app.register_blueprint(game_bp)
app.register_blueprint(search_bp)
app.register_blueprint(games_bp)

# ===== HTML PAGE ROUTES =====
@app.route("/")
def home():
    return render_template('index.html')

@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/register")
def register():
    return render_template('register.html')

@app.route("/dashboard")
def dashboard():
    return render_template('dashboard.html')

@app.route("/add-dream")
def add_dream():
    return render_template('add_dream.html')

@app.route("/analytics")
def analytics():
    return render_template('analytics.html')

@app.route("/chat")
def chat():
    return render_template('chat.html')

@app.route("/subscription")
def subscription():
    return render_template('subscription.html')

@app.route("/dream-detail")  # ✅ NEW ROUTE
def dream_detail():
    return render_template('dream_detail.html')

@app.route("/minigame")
def minigame():
    return render_template('minigame.html')

@app.route("/games")
def games():
    return render_template('games.html')

@app.route("/timeline")
def timeline():
    return render_template('timeline.html')

@app.route("/search")
def search():
    return render_template('search.html')

@app.route("/logout")
def logout():
    return render_template('login.html')



# ===== API INFO ROUTE =====
@app.route("/api")
def api_info():
    return jsonify({
        "message": "Dream Pattern Analysis API",
        "version": "1.0",
        "status": "running"
    })

@app.route("/health")
def health_check():
    return jsonify({"status": "healthy"}), 200

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


# Run Flask
if __name__ == "__main__":
    print("=" * 50)
    print("ðŸŒ™ DREAM PATTERN ANALYSIS SERVER")
    print("=" * 50)
    print("âœ… Server starting on http://localhost:5000")
    print("âœ… Open your browser and go to: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)